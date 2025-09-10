"""Simple SQLite helpers for the Telegram bot."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class User:
    id: int
    telegram_id: int
    username: str | None
    invited: bool
    onboarding_complete: bool
    table_assignment: int | None


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            invited INTEGER DEFAULT 0,
            onboarding_complete INTEGER DEFAULT 0,
            table_assignment INTEGER
        )
        """
    )
    conn.commit()
    return conn


def add_user(
    conn: sqlite3.Connection,
    telegram_id: int,
    username: str | None = None,
    invited: bool = False,
) -> User:
    conn.execute(
        "INSERT INTO users (telegram_id, username, invited) VALUES (?, ?, ?)",
        (telegram_id, username, int(invited)),
    )
    conn.commit()
    return get_user(conn, telegram_id)


def get_user(conn: sqlite3.Connection, telegram_id: int) -> Optional[User]:
    cur = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    row = cur.fetchone()
    if not row:
        return None
    return User(
        id=row["id"],
        telegram_id=row["telegram_id"],
        username=row["username"],
        invited=bool(row["invited"]),
        onboarding_complete=bool(row["onboarding_complete"]),
        table_assignment=row["table_assignment"],
    )


def invite_users(conn: sqlite3.Connection, ids: Iterable[int]) -> None:
    for uid in ids:
        if get_user(conn, uid):
            conn.execute(
                "UPDATE users SET invited = 1 WHERE telegram_id = ?", (uid,)
            )
        else:
            conn.execute(
                "INSERT INTO users (telegram_id, invited) VALUES (?, 1)", (uid,)
            )
    conn.commit()
