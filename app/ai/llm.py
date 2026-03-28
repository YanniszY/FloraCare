"""
app/ai/llm.py

Работает с Ollama. Поддерживает:
- одиночный вызов ask_llm(prompt) — для анализа фото
- мультитёрновый чат ask_llm_chat(messages, system) — для /chat эндпоинта
"""

import requests
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"


def ask_llm(prompt: str) -> str:
    """
    Простой одиночный запрос к модели.
    Используется в pipeline.py для анализа растения по фото.
    """
    response = requests.post(
        OLLAMA_GENERATE_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"]


def ask_llm_chat(
    messages: list[dict],
    system: Optional[str] = None,
) -> str:
    """
    Мультитёрновый чат. Принимает историю сообщений в формате:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]

    `system` — системный промпт (инструкция для модели).

    Ollama /api/chat принимает именно такой формат, поэтому
    история передаётся напрямую и модель видит весь контекст разговора.
    """
    payload_messages = []

    if system:
        payload_messages.append({"role": "system", "content": system})

    payload_messages.extend(messages)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": payload_messages,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]
