"""Assignment heuristics for distributing guests among tables."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Dict, Sequence

from bot.db import assign_user_to_table


@dataclass
class Table:
    number: int
    capacity: int

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("Capacity must be positive")


@dataclass
class AssignmentResult:
    table_for_user: Dict[int, int]


def assign_tables(conn: sqlite3.Connection, tables: Sequence[Table]) -> AssignmentResult:
    cur = conn.execute(
        "SELECT telegram_id FROM users WHERE invited = 1 AND onboarding_complete = 1 "
        "AND table_assignment IS NULL ORDER BY telegram_id"
    )
    users = [row[0] for row in cur.fetchall()]
    table_for_user: Dict[int, int] = {}
    table_iter = iter(tables)
    current = next(table_iter, None)
    filled = 0
    for uid in users:
        while current and filled >= current.capacity:
            current = next(table_iter, None)
            filled = 0
        if not current:
            break
        assign_user_to_table(conn, uid, current.number)
        table_for_user[uid] = current.number
        filled += 1
    return AssignmentResult(table_for_user=table_for_user)
