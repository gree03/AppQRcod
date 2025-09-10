import asyncio
import os

from aiogram import Bot, Dispatcher

from bot.admins import router as admin_router
from bot.db import init_db
from bot.guest import router as guest_router


async def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is missing")

    db_path = os.environ.get("DATABASE_PATH", "./bot.db")
    conn = init_db(db_path)

    bot = Bot(token)
    dp = Dispatcher()
    dp["conn"] = conn
    dp.include_router(admin_router)
    dp.include_router(guest_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
