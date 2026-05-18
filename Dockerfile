# Використовуємо легкий образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо залежності та встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код
COPY . .

# Відкриваємо порт
EXPOSE 8000

# Запускаємо додаток
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]