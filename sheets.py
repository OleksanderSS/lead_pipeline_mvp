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

# Налаштування логування
logger = logging.getLogger(__name__)

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

HEADERS = [
    "created_at", "name", "email", "phone", "company",
    "budget", "source", "message", "score", "label", "reasons", "summary",
]

def get_creds() -> Credentials:
    """Отримує облікові дані з ENV або файлу."""
    json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_str:
        return Credentials.from_service_account_info(
            json.loads(json_str), 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
    
    path = "service_account.json"
    if os.path.exists(path):
        return Credentials.from_service_account_file(
            path, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
    
    raise FileNotFoundError("Google Credentials не знайдені в ENV чи файлі service_account.json")

def _sync_append(creds: Credentials, record: dict[str, Any]) -> None:
    """Синхронна функція для запису в таблицю."""
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    range_name = "A1"

    # Перевірка наявності заголовків
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=range_name).execute()
    if not result.get("values"):
        sheet.values().update(
            spreadsheetId=SHEET_ID,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": [HEADERS]},
        ).execute()

    # Запис даних
    row = [str(record.get(col, "") or "") for col in HEADERS]
    sheet.values().append(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()

async def append_to_sheet(record: dict[str, Any]) -> None:
    """Асинхронна обгортка для запису."""
    if not SHEET_ID:
        raise EnvironmentError("GOOGLE_SHEET_ID не встановлено")

    creds = get_creds()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_append, creds, record)