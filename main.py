from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import Settings, get_settings
from bot.handlers import router
from bot.repositories import ScheduleRepository, UserRepository
from bot.utils import (
    format_schedule_day,
    get_academic_week_number,
    get_day_name_for_date,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _current_local_date(settings: Settings) -> date:
    return datetime.now(settings.timezone).date()


async def _send_reminders_for_kind(
    *,
    bot: Bot,
    schedule_repo: ScheduleRepository,
    user_repo: UserRepository,
    target_date: date,
    reminder_kind: str,
) -> None:
    chat_ids = user_repo.list_reminder_chats(reminder_kind)
    if not chat_ids:
        return

    schedule = schedule_repo.load()
    week = get_academic_week_number(target_date)
    day_name = get_day_name_for_date(target_date)
    body = format_schedule_day(day_name, week, schedule)
    prefix = "⏰ <b>Напоминание</b>" if reminder_kind == "morning" else "🌙 <b>Напоминание</b>"
    text = f"{prefix}\n\n{body}"

    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, text)
        except Exception as exc:  # pragma: no cover - depends on Telegram API
            logger.warning(
                "Failed to send %s reminder to %s: %s",
                reminder_kind,
                chat_id,
                exc,
            )


async def send_morning_reminders(
    bot: Bot,
    settings: Settings,
    schedule_repo: ScheduleRepository,
    user_repo: UserRepository,
) -> None:
    today = _current_local_date(settings)
    await _send_reminders_for_kind(
        bot=bot,
        schedule_repo=schedule_repo,
        user_repo=user_repo,
        target_date=today,
        reminder_kind="morning",
    )


async def send_evening_reminders(
    bot: Bot,
    settings: Settings,
    schedule_repo: ScheduleRepository,
    user_repo: UserRepository,
) -> None:
    today = _current_local_date(settings)
    target_date = today + timedelta(days=1)
    await _send_reminders_for_kind(
        bot=bot,
        schedule_repo=schedule_repo,
        user_repo=user_repo,
        target_date=target_date,
        reminder_kind="evening",
    )


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="today", description="Расписание на сегодня"),
        BotCommand(command="tomorrow", description="Расписание на завтра"),
        BotCommand(command="week", description="Расписание на неделю"),
        BotCommand(command="notify", description="Напоминания о расписании"),
        BotCommand(command="edit", description="Изменить расписание"),
        BotCommand(command="cancel", description="Отменить редактирование"),
    ]
    await bot.set_my_commands(commands)


async def main() -> None:
    settings = get_settings()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
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
            send_morning_reminders,
            trigger=CronTrigger(
                hour=settings.morning_push_hour,
                minute=settings.morning_push_minute,
                timezone=settings.timezone,
            ),
            kwargs={
                "bot": bot,
                "settings": settings,
                "schedule_repo": schedule_repo,
                "user_repo": user_repo,
            },
            id="morning_schedule",
            replace_existing=True,
        )
        scheduler.add_job(
            send_evening_reminders,
            trigger=CronTrigger(
                hour=settings.evening_push_hour,
                minute=settings.evening_push_minute,
                timezone=settings.timezone,
            ),
            kwargs={
                "bot": bot,
                "settings": settings,
                "schedule_repo": schedule_repo,
                "user_repo": user_repo,
            },
            id="evening_schedule",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "Morning reminders scheduled at %02d:%02d",
            settings.morning_push_hour,
            settings.morning_push_minute,
        )
        logger.info(
            "Evening reminders scheduled at %02d:%02d",
            settings.evening_push_hour,
            settings.evening_push_minute,
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
