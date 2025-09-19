from __future__ import annotations

import asyncio
import logging
from datetime import date

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import Settings, get_settings
from bot.handlers import router
from bot.keyboards import main_menu_keyboard
from bot.repositories import ScheduleRepository, UserRepository
from bot.utils import format_schedule_day, get_day_name_for_date
from bot.week_fetcher import fetch_current_week

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def broadcast_daily_schedule(
    bot: Bot,
    settings: Settings,
    schedule_repo: ScheduleRepository,
    user_repo: UserRepository,
) -> None:
    schedule = schedule_repo.load()
    try:
        week = await fetch_current_week(settings.week_source_url)
    except Exception as exc:  # pragma: no cover - network failure branch
        logger.exception("Failed to fetch academic week for broadcast: %s", exc)
        week = None

    day_name = get_day_name_for_date(date.today())
    text = format_schedule_day(
        day_name,
        week,
        schedule,
        show_all_when_week_missing=True,
    )
    if week is None:
        text += (
            "\n\n⚠️ Не удалось автоматически определить номер учебной недели."
        )

    users = user_repo.list_users()
    for chat_id in users:
        try:
            await bot.send_message(chat_id, text, reply_markup=main_menu_keyboard())
        except Exception as exc:  # pragma: no cover - depends on Telegram API
            logger.warning("Failed to send daily schedule to %s: %s", chat_id, exc)


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="today", description="Расписание на сегодня"),
        BotCommand(command="tomorrow", description="Расписание на завтра"),
        BotCommand(command="edit", description="Изменить расписание"),
        BotCommand(command="cancel", description="Отменить редактирование"),
    ]
    await bot.set_my_commands(commands)


async def main() -> None:
    settings = get_settings()
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    schedule_repo = ScheduleRepository(settings.schedule_path)
    user_repo = UserRepository(settings.users_path)

    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    dp.include_router(router)

    dp["settings"] = settings
    dp["schedule_repo"] = schedule_repo
    dp["user_repo"] = user_repo

    async def on_startup(bot: Bot) -> None:
        await set_bot_commands(bot)
        scheduler.add_job(
            broadcast_daily_schedule,
            trigger=CronTrigger(
                hour=settings.daily_push_hour,
                minute=settings.daily_push_minute,
                timezone=settings.timezone,
            ),
            kwargs={
                "bot": bot,
                "settings": settings,
                "schedule_repo": schedule_repo,
                "user_repo": user_repo,
            },
            id="daily_schedule",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "Daily schedule broadcast scheduled at %02d:%02d",
            settings.daily_push_hour,
            settings.daily_push_minute,
        )

    async def on_shutdown(bot: Bot) -> None:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
