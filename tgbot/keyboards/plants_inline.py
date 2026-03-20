from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def plant_todo_keyboard(plant_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💧 Полил",
                    callback_data=f"water_{plant_id}"
                )
            ]
        ]
    )