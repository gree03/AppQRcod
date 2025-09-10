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
    cuisine: str | None
    allergies: str | None
    companions: str | None
    atmosphere: str | None
    alcohol: bool | None
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
            cuisine TEXT,
            allergies TEXT,
            companions TEXT,
            atmosphere TEXT,
            alcohol INTEGER,
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
        cuisine=row["cuisine"],
        allergies=row["allergies"],
        companions=row["companions"],
        atmosphere=row["atmosphere"],
        alcohol=(bool(row["alcohol"]) if row["alcohol"] is not None else None),
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


def set_cuisine(conn: sqlite3.Connection, telegram_id: int, cuisine: str) -> None:
    conn.execute(
        "UPDATE users SET cuisine = ? WHERE telegram_id = ?",
        (cuisine, telegram_id),
    )
    conn.commit()


def set_allergies(conn: sqlite3.Connection, telegram_id: int, allergies: str) -> None:
    conn.execute(
        "UPDATE users SET allergies = ? WHERE telegram_id = ?",
        (allergies, telegram_id),
    )
    conn.commit()


def set_companions(conn: sqlite3.Connection, telegram_id: int, companions: str) -> None:
    conn.execute(
        "UPDATE users SET companions = ? WHERE telegram_id = ?",
        (companions, telegram_id),
    )
    conn.commit()


def set_atmosphere(conn: sqlite3.Connection, telegram_id: int, atmosphere: str) -> None:
    conn.execute(
        "UPDATE users SET atmosphere = ? WHERE telegram_id = ?",
        (atmosphere, telegram_id),
    )
    conn.commit()


def set_alcohol(conn: sqlite3.Connection, telegram_id: int, alcohol: bool) -> None:
    conn.execute(
        "UPDATE users SET alcohol = ? WHERE telegram_id = ?",
        (int(alcohol), telegram_id),
    )
    conn.commit()
