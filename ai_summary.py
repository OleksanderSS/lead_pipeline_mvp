import os
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Ініціалізація клієнта (автоматично шукає GEMINI_API_KEY у змінних середовища)
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    logger.error(f"Не вдалося ініціалізувати клієнт Gemini: {e}")
    client = None

async def generate_summary(lead: dict) -> str:
    """
    Генерує короткий опис на основі даних ліда за допомогою AI (Google GenAI SDK).
    """
    if not client:
        raise EnvironmentError("Клієнт Gemini не налаштований")

    prompt = _build_prompt(lead)
    
    try:
        # Використовуємо модель gemini-2.0-flash (вона актуальна і швидка)
        response = client.models.generate_content(
            model='gemini-2.0-flash',  # Використовуємо модель, яку бачить діагностика
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Помилка Gemini API: {e}")
        raise

def _build_prompt(lead: dict) -> str:
    return f"""
    Ти — асистент відділу продажів. Зроби стисле резюме заявки (2 речення).
    
    Дані клієнта:
    - Ім'я: {lead.get('name')}
    - Компанія: {lead.get('company', 'не вказано')}
    - Бюджет: {lead.get('budget', 'не вказано')}
    - Повідомлення: {lead.get('message', 'відсутнє')}
    
    Виділи головний запит. Пиши українською мовою.
    """