import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import init_db, get_user


async def main() -> None:
    token = os.environ["BOT_TOKEN"]
    db_path = os.environ.get("DATABASE_PATH", "./bot.db")
    conn = init_db(db_path)

    bot = Bot(token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(message: Message) -> None:
        user = get_user(conn, message.from_user.id)
        if not user or not user.invited:
            await message.answer("Доступ по приглашению")
            return
        if not user.onboarding_complete:
            conn.execute(
                "UPDATE users SET onboarding_complete = 1 WHERE telegram_id = ?",
                (message.from_user.id,),
            )
            conn.commit()
        await message.answer(
            "Анкета пока не реализована, ожидайте дальнейших инструкций."
        )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
