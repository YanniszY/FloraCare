from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Dashboard")],
        [KeyboardButton(text="Ai helper")],
    ]
)