import asyncio
from aiogram import Bot, Dispatcher
from config.settings import BOT_TOKEN
from handlers.registration import router as registration_router
from handlers.admin import router as admin_router
from handlers.start import router as start_router
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
# include handlers
dp.include_router(registration_router)
dp.include_router(admin_router)
dp.include_router(start_router)
async def main():
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__=="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")