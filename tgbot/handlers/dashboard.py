from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from tgbot.api.api import get_dashboard

from tgbot.utils.formatters import dashboard_text

router = Router()


@router.message(F.text == "Dashboard")
async def dashboard(message: Message):

    data = get_dashboard()
    await message.answer(dashboard_text(data), parse_mode="HTML")


