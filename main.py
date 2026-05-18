"""
Lead Processing Pipeline — MVP
Flow: POST /submit → normalize → AI summary → classify → Google Sheets → Telegram
"""
from dotenv import load_dotenv
load_dotenv()

import os
import re
import json
import logging
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator

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
    logger.info(f"Incoming lead from: {payload.email}")

    # 1. Normalize
    lead = normalize_lead(payload.model_dump())
    logger.info(f"Normalized: {lead}")

    # 2. AI Summary
    try:
        summary = await generate_summary(lead)
    except Exception as e:
        logger.warning(f"AI summary failed: {e}. Using fallback.")
        summary = f"{lead['name']} from {lead.get('company', 'unknown company')} — {lead.get('message', 'no message')[:100]}"

    # 3. Classify
    classification = classify_lead(lead)
    logger.info(f"Classification: {classification}")

    # 4. Build result record
    record = {
        **lead,
        "summary": summary,
        "score": classification["score"],
        "label": classification["label"],
        "reasons": ", ".join(classification["reasons"]),
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    # 5. Write to Google Sheets
    try:
        await append_to_sheet(record)
        logger.info("Written to Google Sheets")
    except Exception as e:
        logger.warning(f"Sheets write failed: {e}")

    # 6. Telegram notification
    try:
        await send_telegram_notification(record)
        logger.info("Telegram notification sent")
    except Exception as e:
        logger.warning(f"Telegram notification failed: {e}")

    return {
        "status": "received",
        "label": record["label"],
        "score": record["score"],
        "summary": summary,
    }
