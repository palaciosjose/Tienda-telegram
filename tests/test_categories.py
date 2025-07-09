import importlib, sqlite3, sys, types
from pathlib import Path
import builtins


def setup_dop(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("TELEGRAM_ADMIN_ID", "1")
    sys.modules.setdefault(
        "dotenv", types.SimpleNamespace(load_dotenv=lambda *a, **k: None)
    )

    telebot_stub = types.SimpleNamespace(
        TeleBot=lambda *a, **k: types.SimpleNamespace(),
        types=types.SimpleNamespace(InlineKeyboardMarkup=lambda *a, **k: None,
                                    InlineKeyboardButton=lambda *a, **k: None),
    )
    sys.modules["telebot"] = telebot_stub
    bot_stub = telebot_stub.TeleBot()
    sys.modules["bot_instance"] = types.SimpleNamespace(bot=bot_stub)

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    import files
    monkeypatch.setattr(files, "main_db", str(tmp_path / "main.db"))

    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE goods (name TEXT PRIMARY KEY, description TEXT, format TEXT, minimum INTEGER, price INTEGER, stored TEXT)")
    conn.commit()
    conn.close()

    sys.modules.pop("db", None)
    sys.modules.pop("dop", None)
    dop = importlib.import_module("dop")
    return dop


def test_category_creation_and_assignment(monkeypatch, tmp_path):
    dop = setup_dop(monkeypatch, tmp_path)
    dop.ensure_database_schema()

    conn = sqlite3.connect(tmp_path / "main.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
    assert cur.fetchone() is not None

    cur.execute("PRAGMA table_info(goods)")
    cols = [c[1] for c in cur.fetchall()]
    assert "category_id" in cols

    cat_id = dop.create_category("Test")
    assert cat_id

    cur.execute("INSERT INTO goods (name, description, format, minimum, price, stored, category_id) VALUES ('P', 'd', 'text', 1, 2, 'f', ?)", (cat_id,))
    conn.commit()

    cur.execute("SELECT category_id FROM goods WHERE name='P'")
    assert cur.fetchone()[0] == cat_id
    conn.close()
