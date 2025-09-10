"""Assignment heuristics for distributing guests among tables."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from sqlalchemy.orm import Session

from .db import User


@dataclass
class Table:
    number: int
    capacity: int

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError("Capacity must be positive")


@dataclass
class AssignmentResult:
    table_for_user: Dict[int, int]


def assign_tables(session: Session, tables: Sequence[Table]) -> AssignmentResult:
    """Greedy assignment of invited users to tables.

    Users are taken in ascending order of telegram id to make the result
    deterministic. Each table is filled before moving to the next.
    """
    invited_users = (
        session.query(User)
        .filter_by(invited=True, onboarding_complete=True, table_assignment=None)
        .order_by(User.telegram_id)
        .all()
    )
    table_for_user: Dict[int, int] = {}
    table_iter = iter(tables)
    current = next(table_iter, None)
    filled = 0
    for user in invited_users:
        while current and filled >= current.capacity:
            current = next(table_iter, None)
            filled = 0
        if not current:
            break
        user.table_assignment = current.number
        table_for_user[user.telegram_id] = current.number
        filled += 1
    session.commit()
    return AssignmentResult(table_for_user=table_for_user)
