"""Admin chat command handlers."""

from __future__ import annotations

import os
from typing import List

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import invite_users
from bot.guest import QUESTIONS


router = Router()

ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", 0))


def _is_admin(message: Message) -> bool:
    return message.chat.id == ADMIN_CHAT_ID


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not _is_admin(message):
        return
    await message.answer(
        "/help — список команд.\n"
        "/status — сводка.\n"
        "/invite_add <id...> — пополнение белого списка.\n"
        "/questions — показать текущую анкету.\n"
        "/set_tables — настроить количество столов.\n"
        "/set_rules — правила группировки.\n"
        "/assign — выполнить распределение.\n"
        "/assign_dry — сухой прогон.\n"
        "/notify_tables — оповестить гостей о столах.\n"
        "/export — выгрузка реестра.\n"
        "/reset_assignments — сброс назначений.\n"
        "/ban <id> — отозвать доступ.\n"
        "/unban <id> — вернуть доступ.\n"
        "/broadcast <текст> — рассылка гостям."
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    if not _is_admin(message):
        return
    conn = message.bot["conn"]
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    completed = conn.execute(
        "SELECT COUNT(*) FROM users WHERE onboarding_complete = 1"
    ).fetchone()[0]
    percent = (completed / total * 100) if total else 0
    await message.answer(
        f"Всего гостей: {total}\nАнкет завершено: {completed} ({percent:.0f}%)"
    )


@router.message(Command("invite_add"))
async def cmd_invite_add(message: Message) -> None:
    if not _is_admin(message):
        return
    parts = message.text.split()[1:]
    ids: List[int] = []
    for part in parts:
        try:
            ids.append(int(part))
        except ValueError:
            continue
    if not ids:
        await message.answer("Не указаны идентификаторы")
        return
    conn = message.bot["conn"]
    invite_users(conn, ids)
    await message.answer("ok")


@router.message(Command("questions"))
async def cmd_questions(message: Message) -> None:
    if not _is_admin(message):
        return
    text = "\n".join(f"{q.id}. {q.text}" for q in QUESTIONS)
    await message.answer(text)


@router.message(Command("set_tables"))
async def cmd_set_tables(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("set_rules"))
async def cmd_set_rules(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("assign"))
async def cmd_assign(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("assign_dry"))
async def cmd_assign_dry(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("notify_tables"))
async def cmd_notify_tables(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("reset_assignments"))
async def cmd_reset_assignments(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("ban"))
async def cmd_ban(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("unban"))
async def cmd_unban(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")

