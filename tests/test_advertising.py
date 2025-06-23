import sqlite3
import sys
import types

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


def init_ads_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(CREATE_CAMPAIGNS_TABLE)
    cur.execute(CREATE_SEND_LOGS_TABLE)
    cur.execute(CREATE_TARGET_GROUPS_TABLE)
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

