"""
Lead Processing Pipeline — MVP
Flow: POST /submit → normalize → AI summary → classify → Google Sheets → Telegram
"""
from dotenv import load_dotenv
load_dotenv()

import os
import re
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from normalizer import normalize_lead
from classifier import classify_lead
from ai_summary import generate_summary
from sheets import append_to_sheet
from notifier import send_telegram_notification

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lead Processing Pipeline",
    description="MVP for processing landing page form submissions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ── Input schema ─────────────────────────────────────────────────────────────

class LeadPayload(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None
    budget: Optional[str] = None
    source: Optional[str] = "website"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if digits and len(digits) < 7:
            raise ValueError("Phone number too short")
        return v.strip() if v.strip() else None


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "service": "lead-pipeline"}


# ── Main endpoint ─────────────────────────────────────────────────────────────

@app.post("/submit")
async def submit_lead(payload: LeadPayload):
    # 1. Normalize
    lead = normalize_lead(payload.model_dump())

    # 2. AI Summary (a plain-text fallback if the model is unavailable)
    try:
        summary = await generate_summary(lead)
    except Exception as e:
        logger.warning(f"AI summary failed ({type(e).__name__}); using fallback")
        summary = _fallback_summary(lead)

    # 3. Classify
    classification = classify_lead(lead)

    # 4. Build result record
    record = {
        **lead,
        "summary": summary,
        "score": classification["score"],
        "label": classification["label"],
        "reasons": ", ".join(classification["reasons"]),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    # 5. Write to Google Sheets -- the lead's only durable record
    try:
        await append_to_sheet(record)
        stored = True
    except Exception as e:
        logger.error(f"Sheets write failed ({type(e).__name__}): {e}")
        stored = False
    record["stored"] = stored

    # 6. Telegram notification -- sent even when the sheet failed, flagged as such
    try:
        await send_telegram_notification(record)
        notified = True
    except Exception as e:
        logger.error(f"Telegram notification failed ({type(e).__name__}): {e}")
        notified = False

    # No personal data in the log: label, score and outcome only.
    logger.info(f"Lead {record['label']} ({record['score']}): stored={stored} notified={notified}")

    body = {
        "status": "received" if stored else "not_stored",
        "stored": stored,
        "notified": notified,
        "label": record["label"],
        "score": record["score"],
        "summary": summary,
    }
    # A lead that was not stored must not be reported as received: the form can retry.
    return JSONResponse(status_code=200 if stored else 502, content=body)


def _fallback_summary(lead: dict) -> str:
    company = lead.get("company") or "unknown company"
    message = (lead.get("message") or "no message")[:100]
    return f"{lead['name']} from {company} — {message}"
