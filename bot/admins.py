"""Admin chat command handlers."""

from __future__ import annotations

from typing import List
import sqlite3

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import invite_users, add_invite_tokens, get_invited_user_ids, reset_tables_default
from bot.guest import QUESTIONS


router = Router()

ADMIN_CHAT_ID = 0


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
        "/broadcast <текст> — рассылка гостям.\n"
        "/set_rules — правила группировки.\n"
        "/assign — выполнить распределение.\n"
        "/assign_dry — сухой прогон.\n"
        "/notify_tables — оповестить гостей о столах.\n"
        "/export — выгрузка реестра.\n"
        "/reset_assignments — сброс назначений.\n"
        "/ban <id> — отозвать доступ.\n"
        "/unban <id> — вернуть доступ."
    )


@router.message(Command("status"))
async def cmd_status(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    completed = conn.execute(
        "SELECT COUNT(*) FROM users WHERE onboarding_complete = 1"
    ).fetchone()[0]
    assigned = conn.execute(
        "SELECT COUNT(*) FROM users WHERE table_assignment IS NOT NULL"
    ).fetchone()[0]
    percent = (completed / total * 100) if total else 0
    tables_loaded = (
        conn.execute("SELECT COUNT(*) FROM tables").fetchone()[0] > 0
    )
    unassigned = total - assigned
    await message.answer(
        "Всего гостей: {}\nОнбординг завершили: {}\nАнкет завершили: {} ({:.0f}%)\n"
        "Назначены за столы: {} / {}\nСтолов настроено: {}".format(
            total,
            completed,
            completed,
            percent,
            assigned,
            unassigned,
            "да" if tables_loaded else "нет",
        )
    )


@router.message(Command("invite_add"))
async def cmd_invite_add(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    parts = message.text.split()[1:]
    ids: List[int] = []
    count = 0
    for part in parts:
        if part.startswith("count="):
            try:
                count = int(part.split("=", 1)[1])
            except ValueError:
                pass
        else:
            try:
                ids.append(int(part))
            except ValueError:
                continue
    lines: List[str] = []
    if ids:
        invite_users(conn, ids)
        lines.append(f"IDs добавлены: {len(ids)}")
    if count:
        tokens = add_invite_tokens(conn, count)
        lines.append("Токены: " + " ".join(tokens))
    if not lines:
        await message.answer("Использование: /invite_add <id...> [count=N]")
    else:
        await message.answer("\n".join(lines))


@router.message(Command("questions"))
async def cmd_questions(message: Message) -> None:
    if not _is_admin(message):
        return
    text = "\n".join(f"{q.id}. {q.text}" for q in QUESTIONS)
    await message.answer(text)


@router.message(Command("set_tables"))
async def cmd_set_tables(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    reset_tables_default(conn)
    await message.answer("Создано 3 стола по 4 места")


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
async def cmd_broadcast(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Нужно указать текст")
        return
    text = parts[1]
    for uid in get_invited_user_ids(conn):
        try:
            await message.bot.send_message(uid, text)
        except Exception:
            continue
    await message.answer("Рассылка отправлена")

