
from fastapi import FastAPI, UploadFile, Body
import shutil
import os
import json

from app.ai.pipeline import analyze_plant
from app.ai.llm import ask_llm
from app.data.memory import get_user_context, add_user_note

app = FastAPI()

os.makedirs("temp", exist_ok=True)

with open("app/ai/plant_knowledge.json") as f:
    plant_knowledge = json.load(f)


@app.post("/analyze")
async def analyze(file: UploadFile):
    path = f"temp/{file.filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = analyze_plant(path)

    return {"result": result}



@app.post("/chat")
async def chat(message: str = Body(...)):

    knowledge_text = ""

    user_context = get_user_context("user_1")

    # можно просто добавить всю базу (на старте норм)
    for plant, info in plant_knowledge.items():
        knowledge_text += f"{plant}: {info}\n"

    prompt = f"""
Ты опытный специалист по комнатным растениям.

ВАЖНЫЕ ПРАВИЛА:
- Отвечай на ТОМ ЖЕ ЯЗЫКЕ, что и вопрос пользователя
- Не смешивай языки
- Не используй слова из других языков
- Пиши просто, естественно и понятно
- Не придумывай слова
- Давай практичные советы, которые можно применить в жизни
- Если не уверен — скажи об этом

Контекст по растениям:
{knowledge_text}


Контекст пользователя:
{user_context}


Пример хорошего ответа:
If plants need different humidity, you don’t have to separate them into different rooms.

What you can do:
- don’t mist plants that don’t need it (like hoya)
- place a humidifier closer to humidity-loving plants
- group similar plants together

---

Вопрос:
{message}

Ответь:
1. Коротко объясни ситуацию
2. Дай практическое решение
3. Если есть компромисс — предложи его

Перед ответом:
- проверь язык
- если есть смешение языков — исправь
"""

    answer = ask_llm(prompt)
    add_user_note("user_1", message)

    return {"result": answer}