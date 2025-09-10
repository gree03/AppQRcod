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
    full_name: str | None
    accepted: bool | None
    guests_count: int | None
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
            full_name TEXT,
            accepted INTEGER,
            guests_count INTEGER,
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
        full_name=row["full_name"],
        accepted=(bool(row["accepted"]) if row["accepted"] is not None else None),
        guests_count=row["guests_count"],
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


def set_full_name(conn: sqlite3.Connection, telegram_id: int, full_name: str) -> None:
    conn.execute(
        "UPDATE users SET full_name = ? WHERE telegram_id = ?",
        (full_name, telegram_id),
    )
    conn.commit()


def set_acceptance(conn: sqlite3.Connection, telegram_id: int, accepted: bool) -> None:
    conn.execute(
        "UPDATE users SET accepted = ? WHERE telegram_id = ?",
        (int(accepted), telegram_id),
    )
    conn.commit()


def set_guests_count(conn: sqlite3.Connection, telegram_id: int, count: int) -> None:
    conn.execute(
        "UPDATE users SET guests_count = ? WHERE telegram_id = ?",
        (count, telegram_id),
    )
    conn.commit()
