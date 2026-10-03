# Lead Processing Pipeline — MVP

A small webhook service that takes a landing-page form submission and carries it to the sales team in
seconds: clean the fields, summarise the request with an LLM, score the lead, store it, notify.

```
POST /submit → normalize → LLM summary → score → Google Sheets → Telegram
```

## What each step does

| File | Step |
|---|---|
| `main.py` | FastAPI app. Validates the payload with Pydantic (name required, email lower-cased, phone at least 7 digits) and runs the steps in order. |
| `normalizer.py` | Trims every field, title-cases the name, normalises the phone to `+380…`, maps free-text budgets to fixed buckets, canonicalises the source label. |
| `ai_summary.py` | Two-sentence summary of the request from Gemini (`gemini-2.0-flash`). If the call fails, a plain-text fallback is used instead. |
| `classifier.py` | Rule-based score 0–100, with the reasons listed (table below). |
| `sheets.py` | Appends the record to a Google Sheet through a service account. |
| `notifier.py` | Sends a formatted message through the Telegram Bot API. |

## Scoring

| Signal | Points |
|---|---|
| Company given | +30 |
| Phone given | +20 |
| Message longer than 50 characters | +20 |
| Budget $2k or more | +15 |
| Any other budget stated | +5 |
| Business email domain (not gmail, ukr.net, …) | +10 |

**HOT** ≥ 60 · **WARM** 30–59 · **COLD** < 30. The rules are explicit on purpose: a sales team can read
why a lead got its label, and change a weight without retraining anything.

## Run

Create `.env` with five variables — `GEMINI_API_KEY`, `GOOGLE_SHEET_ID`, `GOOGLE_CREDENTIALS_JSON` (or a
`service_account.json` file next to the code), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — then:

```bash
docker compose up
```

Example payloads are in `test_payloads.md`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

23 tests cover the scoring rules, budget parsing, what the caller is told when a step fails, that no
personal data reaches the log, that user text cannot break the Telegram message, and that a clean install
provides every module the code imports. They run on every push (GitHub Actions).

## Failure behaviour

| What fails | Response | What the team sees |
|---|---|---|
| nothing | `200 received` | the lead in Telegram and in the sheet |
| Gemini | `200 received` | a plain-text summary instead of the AI one |
| Google Sheets | `502 not_stored` — the form can retry | the lead in Telegram, marked **NOT SAVED** |
| Telegram | `200 received`, `notified: false` | the lead in the sheet |

## Known limitations

This is an MVP. Before production it would still need:

- authentication or rate limiting on `/submit` (CORS is open to any origin);
- a retry queue, so a lead survives both Sheets and Telegram being down at once;
- email format validation (today it is only trimmed and lower-cased).
