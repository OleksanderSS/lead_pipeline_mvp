"""A clean install must provide what the code imports; user text must not break the Telegram message."""
import importlib.metadata
from pathlib import Path

from notifier import _format_message

ROOT = Path(__file__).resolve().parents[1]


def _requirements():
    text = (ROOT / "requirements.txt").read_bytes().decode("utf-8")  # UTF-16 would fail here
    return {line.split("==")[0].strip().lower() for line in text.splitlines() if line.strip()}


def test_requirements_is_plain_utf8_text():
    _requirements()


def test_the_gemini_package_in_requirements_is_the_one_the_code_imports():
    source = (ROOT / "ai_summary.py").read_text(encoding="utf-8")
    assert "from google import genai" in source
    provided = {str(f).split("/")[1] for f in importlib.metadata.files("google-genai") if str(f).startswith("google/")}
    assert "genai" in provided
    assert "google-genai" in _requirements()
    assert "google-generativeai" not in _requirements()


def test_html_in_user_fields_is_escaped():
    text = _format_message({"name": "<b>Bob</b> & Co", "summary": "a < b", "label": "HOT"})
    assert "&lt;b&gt;Bob&lt;/b&gt; &amp; Co" in text
    assert "a &lt; b" in text


def test_an_unstored_lead_is_flagged_in_the_message():
    assert "NOT SAVED" in _format_message({"label": "HOT", "stored": False})
    assert "NOT SAVED" not in _format_message({"label": "HOT", "stored": True})
