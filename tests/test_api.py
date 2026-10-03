"""The /submit endpoint: what the caller is told when a step fails."""
import logging

import pytest
from fastapi.testclient import TestClient

import main

PAYLOAD = {"name": "Olena", "email": "olena@techstartup.ua", "company": "TechStartup"}


async def _ok(*args, **kwargs):
    return None


async def _fails(*args, **kwargs):
    raise RuntimeError("step down")


async def _summary(lead):
    return "summary"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "generate_summary", _summary)
    monkeypatch.setattr(main, "append_to_sheet", _ok)
    monkeypatch.setattr(main, "send_telegram_notification", _ok)
    return TestClient(main.app, raise_server_exceptions=False)


def test_a_stored_and_notified_lead_is_received(client):
    response = client.post("/submit", json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "received" and body["stored"] is True and body["notified"] is True


def test_a_lead_the_sheet_did_not_store_is_not_reported_as_received(client, monkeypatch):
    sent = []

    async def _capture(record):
        sent.append(record)

    monkeypatch.setattr(main, "append_to_sheet", _fails)
    monkeypatch.setattr(main, "send_telegram_notification", _capture)
    response = client.post("/submit", json=PAYLOAD)
    assert response.status_code == 502
    assert response.json()["status"] == "not_stored"
    assert sent and sent[0]["stored"] is False  # the team still hears about it


def test_a_failed_notification_is_reported(client, monkeypatch):
    monkeypatch.setattr(main, "send_telegram_notification", _fails)
    response = client.post("/submit", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json()["notified"] is False


def test_the_fallback_summary_survives_an_empty_message(client, monkeypatch):
    monkeypatch.setattr(main, "generate_summary", _fails)
    response = client.post("/submit", json={"name": "Petro", "email": "petro@yahoo.com"})
    assert response.status_code == 200
    assert "Petro" in response.json()["summary"]


def test_personal_data_stays_out_of_the_log(client, caplog):
    with caplog.at_level(logging.INFO):
        client.post("/submit", json={**PAYLOAD, "phone": "0671234567"})
    text = caplog.text
    assert "olena@techstartup.ua" not in text and "0671234567" not in text and "380671234567" not in text
