from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart


from tgbot.keyboards.main_reply_kb import main_kb
from tgbot.utils.check_usr_id import check_user_telegram_id

router = Router()



@router.message(CommandStart())
async def start(message: Message):

    check_user_telegram_id(message.from_user.id)

    await message.answer("Привет, я бот FloraCare. Чем могу помочь?", reply_markup=main_kb)
