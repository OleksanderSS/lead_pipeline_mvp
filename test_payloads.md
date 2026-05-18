# Test Payloads

## HOT lead (high score — company + phone + budget + business email)
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name":    "Олена Ковальчук",
    "email":   "o.kovalchuk@techstartup.ua",
    "phone":   "0671234567",
    "company": "TechStartup UA",
    "message": "Нам потрібна CRM-система для відділу продажів (15 менеджерів). Хочемо інтеграцію з Telegram і Google Sheets. Бюджет є, терміни — до кінця кварталу.",
    "budget":  "5000",
    "source":  "google"
  }'
```

## WARM lead (medium score — no company, gmail, short message)
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name":    "Андрій Мельник",
    "email":   "andrii.melnyk@gmail.com",
    "phone":   "+380501112233",
    "company": "",
    "message": "Цікавить автоматизація маркетингу",
    "budget":  "1000",
    "source":  "instagram"
  }'
```

## COLD lead (minimal info)
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name":    "Петро",
    "email":   "petro@yahoo.com",
    "message": "Привіт"
  }'
```

## Health check
```bash
curl http://localhost:8000/
```

## Interactive docs (Swagger UI)
Open in browser: http://localhost:8000/docs
