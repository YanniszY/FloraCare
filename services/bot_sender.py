import requests
import json
from tgbot.config_reader import BOT_TOKEN

URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(chat_id: int, plants_count: int, plant_names: str):
    # Формируем текст
    message_text = (
        f"🌿 <b>Пора полить растения!</b>\n\n"
        f"Нуждаются в уходе: {plant_names}\n"
        f"Всего позиций: {plants_count}"
    )

    # Формируем клавиатуру (в формате словаря для JSON)
    keyboard = {
        "inline_keyboard": [
            [{"text": "✅ Полить всё", "callback_data": "water_all"}],
            [{"text": "📋 Список в боте", "callback_data": "show_todo"}]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard) # Обязательно в строку JSON
    }

    try:
        response = requests.post(URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")