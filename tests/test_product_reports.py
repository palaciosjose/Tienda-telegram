from tests.test_categories import setup_dop
import sqlite3


def test_create_product_report(monkeypatch, tmp_path):
    dop = setup_dop(monkeypatch, tmp_path)
    dop.ensure_database_schema()

    assert dop.create_product_report(1, 'user', 'P1', 'bad', 1)

    conn = sqlite3.connect(tmp_path / 'main.db')
    cur = conn.cursor()
    cur.execute("SELECT product_name, description FROM product_reports")
    row = cur.fetchone()
    conn.close()
    assert row == ('P1', 'bad')
