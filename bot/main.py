"""Entry point for running the Telegram bot.

The bot uses aiogram's polling mode. For production deployment a webhook
configuration can be added by integrating FastAPI or similar framework.
"""
from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from .config import Config
from .db import create_engine_and_tables, User, Question, Answer, add_user, invite_users
from sqlalchemy.orm import Session


async def main() -> None:
    config = Config.load()
    engine = create_engine_and_tables(config.database_url)
    bot = Bot(config.bot_token)
    dp = Dispatcher()

    session = Session(engine)

    @dp.message(Command("start"))
    async def start(message: Message) -> None:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).one_or_none()
        if not user or not user.invited:
            await message.answer("Доступ по приглашению")
            return
        if not user.onboarding_complete:
            user.onboarding_complete = True
            session.commit()
        await message.answer("Анкета пока не реализована, ожидайте дальнейших инструкций.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
