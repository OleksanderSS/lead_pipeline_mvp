# Lead Processing Pipeline — MVP

Легковажний webhook-сервіс для наскрізної обробки заявок із лендингу.  
Автоматизує шлях ліда від заповнення форми до запису в таблицю та сповіщення команди в Telegram.

```
POST /submit → normalize → AI summary → classify → Google Sheets → Telegram
```

---

## Architecture

```
Landing page form
       │
       ▼
POST /submit (FastAPI)
       │
       ├─► normalizer.py  — очищення та стандартизація полів (Regex)
       ├─► ai_summary.py  — Gemini 1.5 Flash генерує резюме (2–3 речення)
       ├─► classifier.py  — скоринг 0–100 → мітки HOT / WARM / COLD
       ├─► sheets.py      — запис рядка через Google Sheets API
       └─► notifier.py    — надсилання сповіщення через Telegram Bot API
```

---

## Scoring Logic (`classifier.py`)

| Сигнал                       | Бали |
|------------------------------|------|
| Вказана компанія             | +30  |
| Вказаний телефон             | +20  |
| Повідомлення > 50 симв.      | +20  |
| Бюджет ≥ $2k                 | +15  |
| Бізнес-пошта (не gmail тощо) | +10  |
| Будь-який бюджет             | +5   |

- 🔥 **HOT** (≥ 60 балів) — термінова обробка, до 1 години
- 🟡 **WARM** (30–59 балів) — стандартний фоллоу-ап, до 24 годин
- 🧊 **COLD** (< 30 балів) — додавання в базу для nurture-розсилки

---

## Quick Start

### 1. Локальний запуск

```bash
git clone https://github.com/OleksanderSS/lead-pipeline-mvp.git
cd lead-pipeline-mvp

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API: `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

### 2. Запуск через Docker

```bash
docker build -t lead-pipeline .
docker run -p 8000:8000 --env-file .env lead-pipeline
```

---

## Environment Variables

Створіть файл `.env` на основі `.env.example`:

| Змінна                   | Опис                                              |
|--------------------------|---------------------------------------------------|
| `GEMINI_API_KEY`         | Ключ Google AI Studio для Gemini 1.5 Flash        |
| `TELEGRAM_BOT_TOKEN`     | Токен від @BotFather                              |
| `TELEGRAM_CHAT_ID`       | ID чату або каналу для сповіщень                  |
| `GOOGLE_SHEET_ID`        | ID таблиці (з URL)                                |
| `GOOGLE_CREDENTIALS_JSON`| Повний вміст JSON-ключа Service Account           |

---

## Google Sheets Setup

1. Відкрийте [Google Cloud Console](https://console.cloud.google.com/) → створіть проєкт → увімкніть **Google Sheets API**
2. Створіть **Service Account** → завантажте JSON-ключ
3. Скопіюйте вміст JSON-файлу → вставте як значення `GOOGLE_CREDENTIALS_JSON` в `.env`
4. Відкрийте таблицю → **Share** із email Service Account (права Editor)
5. Скопіюйте ID таблиці з URL → вкажіть у `GOOGLE_SHEET_ID`

Колонки, що створюються автоматично при першому запуску:
```
created_at | name | email | phone | company | budget | source | message | score | label | reasons | summary
```

---

## Telegram Setup

1. Напишіть боту [@BotFather](https://t.me/botfather) → `/newbot` → отримайте токен
2. Додайте бота в робочий чат або канал як адміністратора
3. Отримайте Chat ID:
   - Групи: використайте [@userinfobot](https://t.me/userinfobot) або перевірте `getUpdates`
   - Канали: числовий ID починається з `-100`
4. Вкажіть значення в `TELEGRAM_BOT_TOKEN` та `TELEGRAM_CHAT_ID` в `.env`

---

## API Response Example

```json
{
  "status": "received",
  "label": "HOT",
  "score": 95,
  "summary": "Олена Ковальчук (TechStartup UA) шукає CRM з інтеграцією Telegram. Бюджет $5k, дедлайн до кінця кварталу."
}
```

---

## Reliability & Fallbacks

MVP спроєктовано з урахуванням відмовостійкості зовнішніх сервісів:

- **AI Summary Fallback** — якщо Gemini API недоступне, система генерує базове резюме з перших 100 символів повідомлення. Обробка ліда не переривається.
- **Async Processing** — взаємодія з Sheets та Telegram асинхронна і не блокує основний потік, що забезпечує миттєву відповідь клієнту.
- **Graceful Errors** — збій в одному модулі (наприклад, Telegram) не заважає успішному запису в Google Sheets.

---

## Deployment (Railway)

1. Завантажте код на GitHub
2. Увійдіть у [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Додайте змінні оточення у вкладці **Variables**
4. Railway автоматично виявить `Dockerfile` та розгорне публічний вебхук

Підключення до форми на лендингу:

```html
<form id="lead-form">
  <!-- поля форми -->
  <button type="submit">Надіслати</button>
</form>

<script>
  document.getElementById('lead-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    await fetch('https://your-app.up.railway.app/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  });
</script>
```

---

## Test Payloads

Готові `curl`-приклади описані у файлі `test_payloads.md`.

Приклад відправки HOT ліда:

```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name":    "Олена Ковальчук",
    "email":   "o.kovalchuk@techstartup.ua",
    "phone":   "0671234567",
    "company": "TechStartup UA",
    "message": "Нам потрібна CRM-система для відділу продажів. Хочемо інтеграцію з Telegram. Терміни — до кінця кварталу.",
    "budget":  "5000",
    "source":  "google"
  }'
```

---

## What's Intentionally Out of Scope (MVP Note)

Цей проєкт — функціональний прототип, що вирішує ключову бізнес-задачу найшвидшим шляхом.  
У Production-версії рекомендується додати:

- **Persistent Queue** (Redis/Celery) — гарантована доставка при тимчасових збоях сторонніх API
- **API Authentication** — захист публічного ендпоінту (API Keys або JWT Bearer Tokens)
- **Relational DB** (PostgreSQL) — для складних звітів і виходу за межі лімітів Google Sheets
- **Unit & Integration Tests** — покриття логіки класифікації, скорингу та regex нормалізатора