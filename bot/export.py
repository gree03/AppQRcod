"""Export command for administrators."""
from __future__ import annotations

import sqlite3
from typing import List

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import (
    list_tables,
    get_table_guests,
    get_unassigned_guests,
)

router = Router()
ADMIN_CHAT_ID = 0


def _format_table_block(conn: sqlite3.Connection) -> List[str]:
    tables = list_tables(conn)
    if not tables:
        return ["Столы не настроены"]
    max_cap = max(t["capacity"] for t in tables)
    header = " | ".join(f"Стол {t['table_no']}" for t in tables) + " | Не распределены"
    lines: List[str] = [header]
    # Pre-fetch unassigned
    unassigned = get_unassigned_guests(conn)
    # Build guest lookup per table
    table_guests = {t["table_no"]: get_table_guests(conn, t["table_no"]) for t in tables}
    for seat in range(1, max_cap + 1):
        row_parts = []
        for t in tables:
            guests = table_guests[t["table_no"]]
            g = next((g for g in guests if g["seat"] == seat), None)
            if g:
                row_parts.append(f"{seat}. {g['name']}")
            else:
                row_parts.append(f"{seat}. —")
        if seat == 1:
            unassigned_names = ", ".join(g["name"] for g in unassigned) or "нет"
            row_parts.append(unassigned_names)
        else:
            row_parts.append("")
        lines.append(" | ".join(row_parts))
    return lines


def _format_guest_block(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute(
        "SELECT COALESCE(full_name, username, telegram_id) AS name, "
        "accepted, cuisine, allergies, companions, atmosphere, alcohol "
        "FROM users WHERE invited = 1 ORDER BY id"
    )
    lines = ["", "Гости и ответы:"]
    for row in cur.fetchall():
        parts = [
            f"Принято: {'Да' if row['accepted'] else 'Нет' if row['accepted'] is not None else '—'}",
            f"Кухня: {row['cuisine'] or '—'}",
            f"Аллергии: {row['allergies'] or '—'}",
            f"Друзья: {row['companions'] or '—'}",
            f"Атмосфера: {row['atmosphere'] or '—'}",
            f"Спиртное: {'Да' if row['alcohol'] else 'Нет' if row['alcohol'] is not None else '—'}",
        ]
        lines.append(f"{row['name']} — " + "; ".join(parts))
    return lines


@router.message(Command("export"))
async def cmd_export(message: Message, conn: sqlite3.Connection) -> None:
    if message.chat.id != ADMIN_CHAT_ID:
        return
    lines = _format_table_block(conn) + _format_guest_block(conn)
    text = "\n".join(lines)
    await message.answer(text)
