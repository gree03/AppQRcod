from bot.db import create_engine_and_tables, invite_users, User
from sqlalchemy.orm import Session


def test_invite_users_creates_and_marks():
    engine = create_engine_and_tables("sqlite:///:memory:")
    session = Session(engine)
    # initially no users
    invite_users(session, [1, 2])
    # Should create users
    users = session.query(User).order_by(User.telegram_id).all()
    assert [u.telegram_id for u in users] == [1, 2]
    assert all(u.invited for u in users)

    # inviting existing user keeps invitation
    invite_users(session, [2, 3])
    users = session.query(User).order_by(User.telegram_id).all()
    assert [u.telegram_id for u in users] == [1, 2, 3]
    assert all(u.invited for u in users)
