"""
Normalizer — cleans and standardizes raw lead data before further processing.
"""

import re
from typing import Any


def normalize_lead(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Accepts raw payload dict, returns cleaned normalized dict.
    Rules:
      - Strip whitespace from all strings
      - Title-case names
      - Lowercase email
      - Normalize phone to E.164-ish (+380XXXXXXXXX)
      - Normalize budget to a canonical bucket
      - Normalize source label
    """
    lead = {}

    # Name — strip + title case
    name = (raw.get("name") or "").strip()
    lead["name"] = _title_case(name)

    # Email
    lead["email"] = (raw.get("email") or "").strip().lower()

    # Phone
    lead["phone"] = _normalize_phone(raw.get("phone"))

    # Company
    company = (raw.get("company") or "").strip()
    lead["company"] = company if company else None

    # Message
    message = (raw.get("message") or "").strip()
    lead["message"] = message if message else None

    # Budget → canonical bucket
    lead["budget"] = _normalize_budget(raw.get("budget"))

    # Source
    lead["source"] = _normalize_source(raw.get("source"))

    return lead


# ── Helpers ───────────────────────────────────────────────────────────────────

def _title_case(name: str) -> str:
    """Handle Cyrillic + Latin names."""
    return " ".join(word.capitalize() for word in name.split())


def _normalize_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw.strip())
    if not digits or len(digits) < 7:
        return None

    # Ukrainian numbers: 0XXXXXXXXX → +380XXXXXXXXX
    if digits.startswith("0") and len(digits) == 10:
        return "+38" + digits
    # Already has country code
    if digits.startswith("380") and len(digits) == 12:
        return "+" + digits
    if digits.startswith("38") and len(digits) == 11:
        return "+" + digits

    # Generic international — just prefix +
    if not digits.startswith("+"):
        return "+" + digits
    return digits


BUDGET_BUCKETS = [
    (0,      500,   "< $500"),
    (500,    2000,  "$500–$2k"),
    (2000,   10000, "$2k–$10k"),
    (10000,  50000, "$10k–$50k"),
    (50000,  None,  "$50k+"),
]

_AMOUNT = re.compile(r"(\d[\d\s]*(?:[.,]\d+)*)\s*(k|к|тис)?", re.IGNORECASE)


def _normalize_budget(raw: str | None) -> str | None:
    """Map free text ("5 000 грн", "$5,000", "5k", the form's own "$2k–$10k") to a bucket.

    The first amount in the text decides; a "k"/"к"/"тис" right after it means thousands.
    Text with no amount at all is kept as written.
    """
    if not raw:
        return None
    match = _AMOUNT.search(raw)
    if not match:
        return raw.strip()

    digits = re.sub(r"\s", "", match.group(1))
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", digits):   # 5,000 / 1.500.000: thousands separators
        amount = float(re.sub(r"[.,]", "", digits))
    else:                                                # 1.5 / 1,5: a decimal point
        amount = float(digits.replace(",", "."))
    if match.group(2):
        amount *= 1000

    for low, high, label in BUDGET_BUCKETS:
        if amount >= low and (high is None or amount < high):
            return label
    return raw.strip()


SOURCE_MAP = {
    "google": "Google",
    "facebook": "Facebook",
    "fb": "Facebook",
    "instagram": "Instagram",
    "ig": "Instagram",
    "linkedin": "LinkedIn",
    "referral": "Referral",
    "website": "Website",
    "organic": "Organic",
    "email": "Email",
}

def _normalize_source(raw: str | None) -> str:
    if not raw:
        return "Website"
    key = raw.strip().lower()
    return SOURCE_MAP.get(key, raw.strip().title())
