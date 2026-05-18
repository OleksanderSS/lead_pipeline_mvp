"""
Classifier — assigns a priority label (HOT / WARM / COLD) to a lead.

Scoring logic (0–100 points):
  +30  has company name
  +20  has phone
  +20  message length > 50 chars
  +15  budget is $2k or higher
  +10  known business email domain (not gmail/yahoo/etc.)
  +5   has budget field at all

Labels:
  HOT  → score ≥ 60
  WARM → score 30–59
  COLD → score < 30
"""

from typing import Any

_FREE_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "icloud.com", "ukr.net", "meta.ua", "i.ua", "bigmir.net",
}

_HIGH_BUDGET_LABELS = {"$2k–$10k", "$10k–$50k", "$50k+"}


def classify_lead(lead: dict[str, Any]) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []

    # +30: has company
    if lead.get("company"):
        score += 30
        reasons.append("has company")

    # +20: has phone
    if lead.get("phone"):
        score += 20
        reasons.append("has phone")

    # +20: meaningful message
    message = lead.get("message") or ""
    if len(message) > 50:
        score += 20
        reasons.append("detailed message")

    # +15: high budget
    budget = lead.get("budget")
    if budget and budget in _HIGH_BUDGET_LABELS:
        score += 15
        reasons.append(f"budget {budget}")

    # +5: any budget
    elif budget:
        score += 5
        reasons.append("budget stated")

    # +10: business email
    domain = lead.get("email", "").split("@")[-1].lower()
    if domain and domain not in _FREE_DOMAINS:
        score += 10
        reasons.append("business email")

    score = min(score, 100)

    if score >= 60:
        label = "HOT"
    elif score >= 30:
        label = "WARM"
    else:
        label = "COLD"

    return {
        "score": score,
        "label": label,
        "reasons": reasons,
    }
