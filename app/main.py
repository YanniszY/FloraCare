"""
app/main.py

Все AI-эндпоинты:
  POST   /chats                        — создать новый чат
  GET    /chats/{user_id}              — список чатов пользователя
  GET    /chats/{chat_id}/messages     — история сообщений чата
  DELETE /chats/{chat_id}              — удалить чат
  POST   /chats/{chat_id}/message      — отправить сообщение, получить ответ ИИ
  POST   /analyze                      — анализ фото растения (без чата)

Подключается к основному приложению через include_router или запускается отдельно.
"""

import json
import os
import shutil

from fastapi import FastAPI, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, engine, Base
from models import Chat, Message, User
from app.ai.pipeline import analyze_plant
from app.ai.llm import ask_llm_chat
from app.data.memory import get_chat_history, save_message, build_user_context_text

# Создаём таблицы если ещё нет (Chat, Message и остальные)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Plant Care AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # на проде заменить на конкретный домен фронта
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("temp", exist_ok=True)

with open("app/ai/plant_knowledge.json") as f:
    plant_knowledge = json.load(f)

# --- Системный промпт для чата ---
SYSTEM_PROMPT = """\
Ты опытный специалист по комнатным растениям.

ПРАВИЛА:
- Отвечай на том же языке, что и вопрос пользователя
- Не смешивай языки
- Пиши просто, естественно и понятно
- Давай практичные советы, которые можно применить сразу
- Если не уверен — скажи об этом
- Не придумывай факты

Структура ответа:
1. Коротко объясни ситуацию
2. Дай конкретное практическое решение
3. Если есть компромисс — предложи его
"""


# ───────────────────────────────────────────
# Schemas
# ───────────────────────────────────────────

class CreateChatRequest(BaseModel):
    user_id: int
    title: str = "Новый чат"


class SendMessageRequest(BaseModel):
    user_id: int
    text: str


# ───────────────────────────────────────────
# Chats
# ───────────────────────────────────────────

@app.post("/chats", summary="Создать новый чат")
def create_chat(body: CreateChatRequest, db: Session = Depends(get_db)):
    chat = Chat(user_id=body.user_id, title=body.title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {
        "id": chat.id,
        "user_id": chat.user_id,
        "title": chat.title,
        "created_at": chat.created_at,
    }


@app.get("/chats/{user_id}", summary="Список чатов пользователя")
def list_chats(user_id: int, db: Session = Depends(get_db)):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in chats
    ]


@app.get("/chats/{chat_id}/messages", summary="История сообщений чата")
def get_messages(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in messages
    ]


@app.delete("/chats/{chat_id}", summary="Удалить чат")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.query(Message).filter(Message.chat_id == chat_id).delete()
    db.delete(chat)
    db.commit()
    return {"status": "deleted"}


# ───────────────────────────────────────────
# Send message → get AI reply
# ───────────────────────────────────────────

@app.post("/chats/{chat_id}/message", summary="Отправить сообщение и получить ответ ИИ")
def send_message(
    chat_id: int,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Сохраняем сообщение пользователя
    save_message(chat_id=chat_id, role="user", content=body.text, db=db)

    # Строим историю для модели (последние 20 сообщений)
    history = get_chat_history(chat_id=chat_id, db=db, limit=20)

    # Добавляем контекст растений пользователя в системный промпт
    user_context = build_user_context_text(user_id=body.user_id, db=db)

    # Добавляем базу знаний по растениям
    knowledge_text = "\n".join(
        f"{plant}: {info}" for plant, info in plant_knowledge.items()
    )

    system = (
        SYSTEM_PROMPT
        + f"\n\nКонтекст пользователя:\n{user_context}"
        + f"\n\nБаза знаний по растениям:\n{knowledge_text}"
    )

    # Запрашиваем ответ у модели
    answer = ask_llm_chat(messages=history, system=system)

    # Сохраняем ответ ассистента
    save_message(chat_id=chat_id, role="assistant", content=answer, db=db)

    # Обновляем updated_at чата
    chat.updated_at = datetime.utcnow()
    db.commit()

    # Если это первое сообщение — обновляем заголовок чата
    msg_count = db.query(Message).filter(Message.chat_id == chat_id).count()
    if msg_count <= 2:  # user + assistant = 2
        short_title = body.text[:50] + ("..." if len(body.text) > 50 else "")
        chat.title = short_title
        db.commit()

    return {
        "chat_id": chat_id,
        "answer": answer,
    }


# ───────────────────────────────────────────
# Analyze photo (без чата, отдельный эндпоинт)
# ───────────────────────────────────────────

@app.post("/analyze", summary="Анализ фото растения")
async def analyze(file: UploadFile):
    path = f"temp/{file.filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = analyze_plant(path)
    finally:
        # Удаляем временный файл после анализа
        if os.path.exists(path):
            os.remove(path)

    return {"result": result}
