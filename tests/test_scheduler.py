import sqlite3
import json
from advertising_system.scheduler import CampaignScheduler

CREATE_CAMPAIGNS = """CREATE TABLE campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    message_text TEXT,
    media_file_id TEXT,
    media_type TEXT,
    button1_text TEXT,
    button1_url TEXT,
    button2_text TEXT,
    button2_url TEXT,
    status TEXT,
    shop_id INTEGER DEFAULT 1
)"""

CREATE_SCHEDULES = """CREATE TABLE campaign_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER,
    schedule_name TEXT,
    frequency TEXT,
    schedule_json TEXT,
    target_platforms TEXT,
    is_active INTEGER DEFAULT 1,
    next_send_telegram TEXT,
    created_date TEXT,
    shop_id INTEGER DEFAULT 1
)"""

CREATE_SHOPS = """CREATE TABLE shops (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, name TEXT)"""


def test_get_pending_sends_json(monkeypatch, tmp_path):
    db_path = tmp_path / "db.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(CREATE_SHOPS)
    cur.execute(CREATE_CAMPAIGNS)
    cur.execute(CREATE_SCHEDULES)
    cur.execute(
        "INSERT INTO campaigns (name, message_text, media_file_id, media_type, button1_text, button1_url, button2_text, button2_url, status, shop_id)"
        " VALUES ('c','m',NULL,NULL,NULL,NULL,NULL,NULL,'active',1)"
    )
    camp_id = cur.lastrowid
    schedule = {"lunes": ["10:00"]}
    cur.execute("INSERT INTO campaign_schedules (campaign_id, schedule_name, frequency, schedule_json, target_platforms, is_active, created_date, shop_id) VALUES (?,?,?,?,?,1,'now',1)", (camp_id,'manual','weekly',json.dumps(schedule),'telegram'))
    conn.commit()
    conn.close()

    import advertising_system.scheduler as mod
    class DummyDatetime(mod.datetime):
        @classmethod
        def now(cls):
            return cls(2023, 1, 2, 10, 0)  # Monday
    monkeypatch.setattr(mod, 'datetime', DummyDatetime)

    sch = CampaignScheduler(str(db_path))
    rows = sch.get_pending_sends()
    assert len(rows) == 1

