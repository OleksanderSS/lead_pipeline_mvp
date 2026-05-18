"""
Telegram Notifier — sends a formatted message to a chat/channel.

Setup:
  1. Create a bot via @BotFather → get TELEGRAM_BOT_TOKEN
  2. Add the bot to your chat/channel
  3. Get TELEGRAM_CHAT_ID:
     - For a group: forward a message to @userinfobot or check getUpdates
     - For a channel: use @channelusername or numeric ID (-100xxxxxxxxxx)
  4. Set env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

import os
import logging

import httpx

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

LABEL_EMOJI = {
    "HOT": "🔥",
    "WARM": "🟡",
    "COLD": "🧊",
}


async def send_telegram_notification(record: dict) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")

    text = _format_message(record)

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
            },
        )
        response.raise_for_status()
        logger.info("Telegram message sent successfully")


def _format_message(r: dict) -> str:
    label = r.get("label", "—")
    emoji = LABEL_EMOJI.get(label, "📋")

    name = r.get("name", "—")
    email = r.get("email", "—")
    phone = r.get("phone") or "—"
    company = r.get("company") or "—"
    budget = r.get("budget") or "—"
    source = r.get("source", "—")
    score = r.get("score", 0)
    reasons = r.get("reasons") or "—"
    summary = r.get("summary", "—")
    created_at = r.get("created_at", "—")

    return (
        f"{emoji} <b>New Lead — {label}</b> (score: {score}/100)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> {name}\n"
        f"📧 <b>Email:</b> {email}\n"
        f"📱 <b>Phone:</b> {phone}\n"
        f"🏢 <b>Company:</b> {company}\n"
        f"💰 <b>Budget:</b> {budget}\n"
        f"📣 <b>Source:</b> {source}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>AI Summary:</b>\n{summary}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Scoring reasons:</b> {reasons}\n"
        f"🕐 {created_at}"
    )
