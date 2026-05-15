# from aiogram.fsm.state import State, StatesGroup
# from aiogram.fsm.context import FSMContext

# class AskAI(StatesGroup):
#     waiting = State()

# # Кнопка "Вопрос ИИ"
# @router.message(F.text == "🤖 Вопрос ИИ")
# async def ask_button(message: Message, state: FSMContext):
#     await state.set_state(AskAI.waiting)
#     await message.answer("Задайте вопрос 🌿")

# # Пользователь написал вопрос
# @router.message(AskAI.waiting)
# async def handle_question(message: Message, state: FSMContext):
#     await state.clear()  # сразу выходим из состояния
#     await message.answer("⏳ Думаю...")
    
#     res = await httpx.AsyncClient().post(
#         "http://localhost:8000/ai/ask",
#         json={"user_id": 1, "text": message.text}
#     )
#     answer = res.json()["answer"]
#     await message.answer(answer)




from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import httpx


class AskAI(StatesGroup):
    waiting = State()


router = Router()


@router.message(F.text == "ask AI")
async def ask_ai(message: Message, state: FSMContext):
    await state.set_state(AskAI.waiting)
    await message.answer("Задавайте вопрос")


@router.message(AskAI.waiting)
async def handle_question(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("thinking...")

    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            "http://localhost:8000/ai/ask",
            json={"user_id": 1, "text": message.text}
        )
    answer = res.json()['answer']
    await message.answer(answer)