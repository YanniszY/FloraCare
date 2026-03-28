
# routers/ai.py

import json
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Chat, Message
from app.ai.pipeline import analyze_plant
from app.ai.llm import ask_llm_chat
from app.data.memory import get_chat_history, save_message, build_user_context_text

router = APIRouter()

os.makedirs("temp", exist_ok=True)

with open("app/ai/plant_knowledge.json") as f:
    plant_knowledge = json.load(f)

SYSTEM_PROMPT = """\
Ты опытный специалист по комнатным растениям.
ПРАВИЛА:
- Отвечай на том же языке, что и вопрос пользователя
- Не смешивай языки
- Пиши просто, естественно и понятно
- Давай практичные советы
- Если не уверен — скажи об этом
Структура ответа:
1. Коротко объясни ситуацию
2. Дай конкретное практическое решение
3. Если есть компромисс — предложи его
"""

class CreateChatRequest(BaseModel):
    user_id: int
    title: str = "Новый чат"

class SendMessageRequest(BaseModel):
    user_id: int
    text: str


@router.post("/chats")
def create_chat(body: CreateChatRequest, db: Session = Depends(get_db)):
    chat = Chat(user_id=body.user_id, title=body.title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {"id": chat.id, "user_id": chat.user_id, "title": chat.title, "created_at": chat.created_at}


@router.get("/chats/{user_id}")
def list_chats(user_id: int, db: Session = Depends(get_db)):
    chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.updated_at.desc()).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at, "updated_at": c.updated_at} for c in chats]


@router.get("/chats/{chat_id}/messages")
def get_messages(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
    return [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]


@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.query(Message).filter(Message.chat_id == chat_id).delete()
    db.delete(chat)
    db.commit()
    return {"status": "deleted"}


@router.post("/chats/{chat_id}/message")
def send_message(chat_id: int, body: SendMessageRequest, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    save_message(chat_id=chat_id, role="user", content=body.text, db=db)

    history = get_chat_history(chat_id=chat_id, db=db, limit=20)
    user_context = build_user_context_text(user_id=body.user_id, db=db)
    knowledge_text = "\n".join(f"{p}: {i}" for p, i in plant_knowledge.items())

    system = SYSTEM_PROMPT + f"\n\nРастения пользователя:\n{user_context}\n\nБаза знаний:\n{knowledge_text}"

    answer = ask_llm_chat(messages=history, system=system)
    save_message(chat_id=chat_id, role="assistant", content=answer, db=db)

    chat.updated_at = datetime.utcnow()
    msg_count = db.query(Message).filter(Message.chat_id == chat_id).count()
    if msg_count <= 2:
        chat.title = body.text[:50] + ("..." if len(body.text) > 50 else "")
    db.commit()

    return {"chat_id": chat_id, "answer": answer}


@router.post("/analyze")
async def analyze(file: UploadFile):
    path = f"temp/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        result = analyze_plant(path)
    finally:
        if os.path.exists(path):
            os.remove(path)
    return {"result": result}