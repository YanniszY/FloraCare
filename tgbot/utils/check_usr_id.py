


from database import SessionLocal
from models import User # Убедись, что модели тоже доступны

def check_user_telegram_id(user_id: int):
    # Создаем сессию вручную
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()

        if not user:
            new_user = User(telegram_id=user_id)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
    except Exception as e:
        db.rollback() # Откатываем, если что-то пошло не так
        print(f"Ошибка БД: {e}")
    finally:
        db.close() # ОБЯЗАТЕЛЬНО закрываем соединение