"""Simple SQLite helpers for the Telegram bot."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Optional, List


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
    table: int | None


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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invite_tokens (
            token TEXT PRIMARY KEY,
            uses_left INTEGER DEFAULT 1
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tables (
            table_no INTEGER PRIMARY KEY,
            label TEXT,
            capacity INTEGER NOT NULL,
            occupied INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            version INTEGER DEFAULT 1
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
        table=row["table_assignment"],
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


def add_invite_tokens(conn: sqlite3.Connection, count: int) -> List[str]:
    import secrets

    tokens: List[str] = []
    for _ in range(count):
        token = secrets.token_hex(4)
        conn.execute(
            "INSERT INTO invite_tokens (token, uses_left) VALUES (?, 1)", (token,)
        )
        tokens.append(token)
    conn.commit()
    return tokens


def use_invite_token(conn: sqlite3.Connection, token: str) -> bool:
    cur = conn.execute(
        "SELECT uses_left FROM invite_tokens WHERE token = ?", (token,)
    )
    row = cur.fetchone()
    if not row or row["uses_left"] <= 0:
        return False
    conn.execute(
        "UPDATE invite_tokens SET uses_left = uses_left - 1 WHERE token = ?",
        (token,),
    )
    conn.commit()
    return True


def reset_tables_default(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM tables")
    for table_no in range(1, 4):
        cur.execute(
            "INSERT INTO tables (table_no, capacity, occupied, active, version) VALUES (?, 4, 0, 1, 1)",
            (table_no,),
        )
    conn.commit()


def get_invited_user_ids(conn: sqlite3.Connection) -> List[int]:
    cur = conn.execute("SELECT telegram_id FROM users WHERE invited = 1")
    return [row["telegram_id"] for row in cur.fetchall() if row["telegram_id"]]


def get_assigned_users(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """Return guests that already have table assignments."""
    cur = conn.execute(
        "SELECT telegram_id, table_assignment, "
        "COALESCE(full_name, username, CAST(telegram_id AS TEXT)) AS name "
        "FROM users WHERE table_assignment IS NOT NULL"
    )
    return cur.fetchall()


def list_guests(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    cur = conn.execute(
        "SELECT telegram_id, COALESCE(full_name, username, telegram_id) AS name "
        "FROM users WHERE invited = 1 ORDER BY id"
    )
    return cur.fetchall()


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


def list_tables(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    cur = conn.execute(
        "SELECT table_no, label, capacity FROM tables ORDER BY table_no"
    )
    return cur.fetchall()


def add_table(conn: sqlite3.Connection, label: str = "", capacity: int = 4) -> int:
    cur = conn.execute("SELECT COALESCE(MAX(table_no), 0) + 1 FROM tables")
    new_no = cur.fetchone()[0]
    conn.execute(
        "INSERT INTO tables (table_no, label, capacity, occupied, active, version) "
        "VALUES (?, ?, ?, 0, 1, 1)",
        (new_no, label, capacity),
    )
    conn.commit()
    return new_no


def update_table_label(conn: sqlite3.Connection, table_no: int, label: str) -> None:
    conn.execute("UPDATE tables SET label = ? WHERE table_no = ?", (label, table_no))
    conn.commit()


def update_table_capacity(conn: sqlite3.Connection, table_no: int, capacity: int) -> None:
    assigned = conn.execute(
        "SELECT COUNT(*) FROM users WHERE table_assignment = ?", (table_no,)
    ).fetchone()[0]
    if capacity < assigned:
        raise ValueError("Capacity less than assigned guests")
    conn.execute(
        "UPDATE tables SET capacity = ? WHERE table_no = ?", (capacity, table_no)
    )
    conn.commit()


def delete_table(conn: sqlite3.Connection, table_no: int) -> None:
    cur = conn.execute(
        "SELECT COUNT(*) FROM users WHERE table_assignment = ?", (table_no,)
    )
    if cur.fetchone()[0] > 0:
        raise ValueError("Table has assigned guests")
    conn.execute("DELETE FROM tables WHERE table_no = ?", (table_no,))
    conn.commit()


def get_table(conn: sqlite3.Connection, table_no: int) -> Optional[sqlite3.Row]:
    cur = conn.execute(
        "SELECT table_no, label, capacity FROM tables WHERE table_no = ?",
        (table_no,),
    )
    return cur.fetchone()


def get_table_guests(conn: sqlite3.Connection, table_no: int) -> List[sqlite3.Row]:
    cur = conn.execute(
        "SELECT telegram_id, COALESCE(full_name, username, telegram_id) AS name "
        "FROM users WHERE table_assignment = ? ORDER BY id",
        (table_no,),
    )
    return cur.fetchall()


def get_unassigned_guests(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    cur = conn.execute(
        "SELECT telegram_id, COALESCE(full_name, username, telegram_id) AS name "
        "FROM users WHERE invited = 1 AND onboarding_complete = 1 "
        "AND table_assignment IS NULL ORDER BY id"
    )
    return cur.fetchall()


def assign_user_to_table(conn: sqlite3.Connection, telegram_id: int, table_no: int) -> None:
    conn.execute(
        "UPDATE users SET table_assignment = ? WHERE telegram_id = ?",
        (table_no, telegram_id),
    )
    occ = conn.execute(
        "SELECT COUNT(*) FROM users WHERE table_assignment = ?", (table_no,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE tables SET occupied = ? WHERE table_no = ?", (occ, table_no)
    )
    conn.commit()


def unassign_user(conn: sqlite3.Connection, telegram_id: int) -> None:
    cur = conn.execute(
        "SELECT table_assignment FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = cur.fetchone()
    if not row or row["table_assignment"] is None:
        return
    table_no = row["table_assignment"]
    conn.execute(
        "UPDATE users SET table_assignment = NULL WHERE telegram_id = ?",
        (telegram_id,),
    )
    occ = conn.execute(
        "SELECT COUNT(*) FROM users WHERE table_assignment = ?", (table_no,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE tables SET occupied = ? WHERE table_no = ?", (occ, table_no)
    )
    conn.commit()


def uninvite_user(conn: sqlite3.Connection, telegram_id: int) -> None:
    unassign_user(conn, telegram_id)
    conn.execute(
        "UPDATE users SET invited = 0 WHERE telegram_id = ?",
        (telegram_id,),
    )
    conn.commit()
