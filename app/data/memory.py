"""
app/data/memory.py

Контекст пользователя для промпта — берётся из БД.
JSON-файл больше не используется.
"""

from sqlalchemy.orm import Session
from models import Plant, Message, Chat


def get_user_plants(user_id: int, db: Session) -> list[str]:
    """Возвращает список названий растений пользователя."""
    plants = db.query(Plant).filter(Plant.user_id == user_id).all()
    return [p.nickname or p.name for p in plants]


def get_chat_history(chat_id: int, db: Session, limit: int = 20) -> list[dict]:
    """
    Возвращает последние `limit` сообщений чата в формате
    [{"role": "user", "content": "..."}, ...]
    — готово для подстановки в промпт Ollama.
    """
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    # Возвращаем в хронологическом порядке
    return [{"role": m.role, "content": m.content} for m in reversed(messages)]


def save_message(chat_id: int, role: str, content: str, db: Session) -> Message:
    """Сохраняет одно сообщение в БД и возвращает объект."""
    msg = Message(chat_id=chat_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def build_user_context_text(user_id: int, db: Session) -> str:
    """
    Строит текстовый контекст пользователя для системного промпта:
    какие растения есть у юзера.
    """
    plants = get_user_plants(user_id, db)
    if not plants:
        return "У пользователя пока нет добавленных растений."
    return "Растения пользователя: " + ", ".join(plants)
