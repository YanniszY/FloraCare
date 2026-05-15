import asyncio

from aiogram import Bot, Dispatcher
from tgbot.config_reader import BOT_TOKEN

from tgbot.handlers.start import router as start_router
from tgbot.handlers.dashboard import router as dashboard_router
from tgbot.handlers.watering import router as watering_router
from tgbot.handlers.askAI import router as ask_ai_router



bot = Bot(BOT_TOKEN)
dp = Dispatcher()



dp.include_router(start_router)
dp.include_router(dashboard_router)
dp.include_router(watering_router)
dp.include_router(ask_ai_router)




if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
