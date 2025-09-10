from bot.db import init_db, invite_users


def test_invite_users_creates_and_marks():
    conn = init_db(":memory:")
    invite_users(conn, [1, 2])
    rows = conn.execute("SELECT telegram_id, invited FROM users ORDER BY telegram_id").fetchall()
    assert [r[0] for r in rows] == [1, 2]
    assert all(r[1] for r in rows)

    invite_users(conn, [2, 3])
    rows = conn.execute("SELECT telegram_id, invited FROM users ORDER BY telegram_id").fetchall()
    assert [r[0] for r in rows] == [1, 2, 3]
    assert all(r[1] for r in rows)
