import sqlite3
import sys
import types
import json

sys.modules.setdefault(
    "telebot",
    types.SimpleNamespace(
        TeleBot=lambda *a, **k: None,
        types=types.SimpleNamespace(
            InlineKeyboardMarkup=lambda *a, **k: None,
            InlineKeyboardButton=lambda *a, **k: None,
        ),
    ),
)
sys.modules.setdefault(
    "advertising_system.auto_sender", types.SimpleNamespace(AutoSender=object)
)
sys.modules.setdefault(
    "advertising_system.telegram_multi",
    types.SimpleNamespace(TelegramMultiBot=lambda *a, **k: None),
)

from advertising_system.ad_manager import AdvertisingManager


CREATE_CAMPAIGNS_TABLE = """CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    message_text TEXT NOT NULL,
    media_file_id TEXT,
    media_type TEXT,
    media_caption TEXT,
    button1_text TEXT,
    button1_url TEXT,
    button2_text TEXT,
    button2_url TEXT,
    status TEXT DEFAULT 'active',
    created_date TEXT,
    created_by INTEGER,
    daily_limit INTEGER DEFAULT 3,
    priority INTEGER DEFAULT 1
)"""

CREATE_SEND_LOGS_TABLE = """CREATE TABLE IF NOT EXISTS send_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER,
    group_id TEXT,
    platform TEXT,
    status TEXT,
    sent_date TEXT,
    response_time REAL,
    error_message TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
)"""

CREATE_TARGET_GROUPS_TABLE = """CREATE TABLE IF NOT EXISTS target_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    group_id TEXT NOT NULL,
    group_name TEXT,
    category TEXT,
    status TEXT DEFAULT 'active',
    last_sent TEXT,
    success_rate REAL DEFAULT 1.0,
    added_date TEXT,
    notes TEXT
)"""

CREATE_SCHEDULES_TABLE = """CREATE TABLE IF NOT EXISTS campaign_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER,
    schedule_name TEXT,
    frequency TEXT,
    schedule_json TEXT,
    target_platforms TEXT,
    is_active INTEGER DEFAULT 1,
    next_send_telegram TEXT,
    created_date TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
)"""


def init_ads_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(CREATE_CAMPAIGNS_TABLE)
    cur.execute(CREATE_SEND_LOGS_TABLE)
    cur.execute(CREATE_TARGET_GROUPS_TABLE)
    cur.execute(CREATE_SCHEDULES_TABLE)
    conn.commit()
    conn.close()


def test_create_campaign_inserts(tmp_path):
    db_path = tmp_path / "ads.db"
    init_ads_db(db_path)
    manager = AdvertisingManager(str(db_path))
    data = {"name": "Test Campaign", "message_text": "Hello", "created_by": 1}
    campaign_id = manager.create_campaign(data)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, message_text FROM campaigns WHERE id = ?", (campaign_id,))
    row = cur.fetchone()
    conn.close()

    assert row == ("Test Campaign", "Hello")


def test_get_today_stats_empty_db(tmp_path):
    db_path = tmp_path / "ads.db"
    init_ads_db(db_path)
    manager = AdvertisingManager(str(db_path))

    stats = manager.get_today_stats()

    assert stats == {"sent": 0, "success_rate": 100, "groups": 0}


def test_send_campaign_now(tmp_path, monkeypatch):
    db_path = tmp_path / "ads.db"
    init_ads_db(db_path)
    manager = AdvertisingManager(str(db_path))

    camp_id = manager.create_campaign({"name": "Camp", "message_text": "Hi", "created_by": 1})
    manager.add_target_group("telegram", "111")

    sent = []

    class DummyTG:
        def __init__(self, *a, **k):
            pass

        def send_message(self, gid, msg, media_file_id=None, media_type=None, buttons=None):
            sent.append(("tg", gid, msg))
            return True, "ok"


    import advertising_system.ad_manager as mod
    monkeypatch.setattr(mod, "TelegramMultiBot", DummyTG)
    monkeypatch.setenv("TELEGRAM_TOKEN", "x")

    ok, msg = manager.send_campaign_now(camp_id, ["telegram"])
    assert ok

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT platform, status FROM send_logs ORDER BY id")
    rows = cur.fetchall()
    conn.close()

    assert len(rows) == 1
    assert sent == [("tg", "111", "Hi")]
    assert all(r[1] == "sent" for r in rows)


def test_schedule_campaign_records_json(tmp_path):
    db_path = tmp_path / "ads.db"
    init_ads_db(db_path)
    manager = AdvertisingManager(str(db_path))
    camp_id = manager.create_campaign({"name": "Camp2", "message_text": "Hi", "created_by": 1})

    ok, msg = manager.schedule_campaign(camp_id, ["lunes"], ["10:00", "15:00"])
    assert ok

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT schedule_json FROM campaign_schedules WHERE campaign_id = ?", (camp_id,))
    row = cur.fetchone()
    conn.close()
    assert row is not None
    data = json.loads(row[0])
    assert data == {"lunes": ["10:00", "15:00"]}

