from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import SessionLocal
from models import Plant
from .services import plant_status

from .bot_sender import send_telegram_message

#from bot_sender import send_telegram_message  # сделаем ниже


def check_plants():

    print("check_plants work!")

    db = SessionLocal()
    # Собираем словарь {user_id: [список имен растений]}
    to_notify = {}

    plants = db.query(Plant).all()
    for plant in plants:
        status = plant_status(plant)
        if status["needs_watering"]:
            if plant.user_id not in to_notify:
                to_notify[plant.user_id] = []
            to_notify[plant.user_id].append(plant.name)

    # Теперь отправляем по одному сообщению каждому юзеру
    for user_id, plants_list in to_notify.items():
        count = len(plants_list)
        names_str = ", ".join(plants_list[:3]) # Первые три имени
        if count > 3:
            names_str += "..."
            
        send_telegram_message(
            chat_id=5736729318, #user_id, # Убедись, что это telegram_id, а не просто ID в базе
            plants_count=count,
            plant_names=names_str
        )
    
    db.close()


def start_scheduler():

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_plants,
        trigger="cron",
        hour=8,
        minute=0,
    )

    scheduler.start()