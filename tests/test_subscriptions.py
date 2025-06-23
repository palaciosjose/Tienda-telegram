import os
import sqlite3
import importlib
import sys
import types

import files


def test_init_subscription_db(tmp_path, monkeypatch):
    # Prepare environment and dummy modules
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy")
    monkeypatch.setenv("TELEGRAM_ADMIN_ID", "1")

    sys.modules.setdefault('dotenv', types.SimpleNamespace(load_dotenv=lambda *a, **k: None))
    sys.modules.setdefault('telebot', types.SimpleNamespace(TeleBot=lambda *a, **k: None))

    db_path = tmp_path / "main_data.db"
    monkeypatch.setattr(files, "main_db", str(db_path))

    subscriptions = importlib.import_module('subscriptions')
    importlib.reload(subscriptions)

    subscriptions.init_subscription_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert 'subscription_products' in tables
    assert 'user_subscriptions' in tables

    cursor.execute("PRAGMA index_list('user_subscriptions')")
    indexes = {row[1] for row in cursor.fetchall()}
    assert 'idx_user_subscriptions_end_date' in indexes
    conn.close()
