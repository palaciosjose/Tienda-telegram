import sqlite3
import importlib
import sys
import types
from pathlib import Path

import pytest


def test_init_subscription_db_creates_tables(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TEST")
    monkeypatch.setenv("TELEGRAM_ADMIN_ID", "1")

    # Ensure project root is on sys.path when tests run from the tests directory
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    import files
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(files, "main_db", str(db_path))

    # Stub telebot and dotenv modules to avoid missing dependencies
    telebot_stub = types.ModuleType("telebot")
    telebot_stub.TeleBot = lambda token: None
    sys.modules["telebot"] = telebot_stub

    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *a, **kw: None
    sys.modules["dotenv"] = dotenv_stub

    subscriptions = importlib.import_module("subscriptions")
    importlib.reload(subscriptions)

    subscriptions.init_subscription_db()

    assert db_path.exists(), "Database file should be created"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    assert 'subscription_products' in tables
    assert 'user_subscriptions' in tables

    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cur.fetchall()}
    assert 'idx_user_subscriptions_end_date' in indexes
    conn.close()
