import pytest

from bot.db import create_engine_and_tables, add_user, User
from bot.assignment import Table, assign_tables
from sqlalchemy.orm import Session


def create_session():
    engine = create_engine_and_tables("sqlite:///:memory:")
    return Session(engine)


def test_assign_tables_greedy():
    session = create_session()
    # Add invited users and mark onboarding complete
    for tid in [10, 11, 12, 13, 14]:
        user = add_user(session, telegram_id=tid, invited=True)
        user.onboarding_complete = True
    session.commit()

    tables = [Table(number=1, capacity=2), Table(number=2, capacity=2)]
    result = assign_tables(session, tables)

    assert result.table_for_user == {10: 1, 11: 1, 12: 2, 13: 2}
    # Last user should remain unassigned due to capacity limits
    assert session.query(User).filter_by(telegram_id=14).one().table_assignment is None
