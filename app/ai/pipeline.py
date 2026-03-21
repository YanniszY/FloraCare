from app.ai.vision import analyze_image_clip, analyze_plant_disease_torch, detect_plant_type
from app.ai.llm import ask_llm

import json

# Загружаем базу знаний один раз
with open("app/ai/plant_knowledge.json") as f:
    plant_knowledge = json.load(f)

def analyze_plant(image_path: str):
    clip_results = analyze_image_clip(image_path)
    disease_results = analyze_plant_disease_torch(image_path, top_k=3)
    plant_type = detect_plant_type(image_path)

    disease_summary = ", ".join([f"{r['label']} ({r['score']*100:.1f}%)" for r in disease_results])

    # Добавляем контекст по уходу
    care_info = plant_knowledge.get(plant_type.lower(), {})
    care_text = "\n".join([f"{k}: {v}" for k, v in care_info.items()])

    prompt = f"""
Ты эксперт по комнатным растениям.

ВАЖНЫЕ ПРАВИЛА:
- Отвечай на ТОМ ЖЕ ЯЗЫКЕ, что и пользователь
- Не смешивай языки
- Не используй английские слова в других языках
- Пиши просто и понятно
- Не придумывай слова
- Давай только реальные и полезные советы
- Если не уверен — скажи об этом

Контекст:
Тип растения: {plant_type}
Симптомы: {clip_results}
Возможные проблемы: {disease_summary}
Информация по уходу:
{care_text}

Пример хорошего ответа:
The leaves are soft — this is usually a sign of overwatering. The soil is too wet and roots may start to rot.

What to do:
- let the soil dry out
- reduce watering
- check drainage

---

Теперь ответь:

1. Что происходит с растением (простым языком)
2. Возможные причины (2-3 варианта)
3. Что делать (конкретные действия списком)

Перед ответом:
- проверь текст
- если есть смешение языков — исправь
"""
    return ask_llm(prompt)