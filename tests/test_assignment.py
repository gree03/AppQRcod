from bot.db import init_db, add_user
from bot.assignment import Table, assign_tables


def create_conn():
    return init_db(":memory:")


def test_assign_tables_greedy():
    conn = create_conn()
    for tid in [10, 11, 12, 13, 14]:
        add_user(conn, telegram_id=tid, invited=True)
        conn.execute("UPDATE users SET onboarding_complete=1 WHERE telegram_id=?", (tid,))
    conn.commit()

    tables = [Table(number=1, capacity=2), Table(number=2, capacity=2)]
    result = assign_tables(conn, tables)

    assert result.table_for_user == {10: 1, 11: 1, 12: 2, 13: 2}
    cur = conn.execute("SELECT table_assignment FROM users WHERE telegram_id=14")
    assert cur.fetchone()[0] is None
