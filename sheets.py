"""
Google Sheets writer — appends one row per lead.
Використовує файл 'service_account.json' для автентифікації.
"""

import os
import json
import logging
import asyncio
from typing import Any
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

HEADERS = [
    "created_at", "name", "email", "phone", "company",
    "budget", "source", "message", "score", "label", "reasons", "summary",
]

def get_creds():
    # 1. Перевіряємо наявність JSON-рядка у змінних оточення
    json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_str:
        # Парсимо рядок у словник
        info = json.loads(json_str)
        return Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    
    # 2. Fallback: намагаємось прочитати локальний файл
    path = "service_account.json"
    if os.path.exists(path):
        return Credentials.from_service_account_file(path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    
    raise FileNotFoundError("Google Credentials не знайдені: ні в ENV, ні у файлі service_account.json")

# Ініціалізація сервісу
creds = get_creds()
service = build('sheets', 'v4', credentials=creds)

async def append_to_sheet(record: dict[str, Any]) -> None:
    if not SHEET_ID:
        raise EnvironmentError("GOOGLE_SHEET_ID не встановлено в .env")

    creds = get_creds()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_append, creds, record)

def _sync_append(creds, record: dict[str, Any]) -> None:
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    # Записуємо в перший аркуш без прив'язки до назви "Sheet1" або "Аркуш1"
    # Використання "A1" без імені аркуша завжди вказує на перший доступний аркуш
    range_name = "A1"

    _ensure_header(sheet, range_name)

    row = [str(record.get(col, "") or "") for col in HEADERS]
    sheet.values().append(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()

def _ensure_header(sheet, range_name: str) -> None:
    """Перевіряє, чи порожній перший рядок, і записує заголовки, якщо так."""
    result = sheet.values().get(
        spreadsheetId=SHEET_ID,
        range=range_name,
    ).execute()

    if not result.get("values"):
        sheet.values().update(
            spreadsheetId=SHEET_ID,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": [HEADERS]},
        ).execute()
        logger.info("Заголовки успішно записані в Google Sheets")