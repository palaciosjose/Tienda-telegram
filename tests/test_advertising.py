import sqlite3
import sys
import types

sys.modules.setdefault('telebot', types.SimpleNamespace(TeleBot=lambda *a, **k: None,
                                                        types=types.SimpleNamespace(InlineKeyboardMarkup=None,
                                                                                     InlineKeyboardButton=None)))
sys.modules.setdefault('requests', types.SimpleNamespace(
    post=lambda *a, **k: types.SimpleNamespace(status_code=200, json=lambda: {}, text=''),
    get=lambda *a, **k: types.SimpleNamespace(status_code=200, json=lambda: {})
))

from advertising_system.ad_manager import AdvertisingManager
from setup_advertising import SQL_TABLES


def setup_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    for sql in SQL_TABLES:
        cur.execute(sql)
    conn.commit()
    conn.close()


def test_create_campaign(tmp_path):
    db = tmp_path / "ad.db"
    setup_db(db)
    manager = AdvertisingManager(str(db))
    cid = manager.create_campaign({'name': 'camp1', 'message_text': 'hi', 'created_by': 1})
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM campaigns WHERE id=?", (cid,))
    row = cur.fetchone()
    conn.close()
    assert row[0] == 'camp1'


def test_schedule_and_groups(tmp_path):
    db = tmp_path / "ad.db"
    setup_db(db)
    manager = AdvertisingManager(str(db))
    gid1 = manager.add_target_group('telegram', '1', 'tg1')
    gid2 = manager.add_target_group('whatsapp', '2', 'wa2')
    cid = manager.create_campaign({'name': 'camp2', 'message_text': 'msg', 'created_by': 1})
    manager.schedule_campaign(cid)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM target_groups")
    assert cur.fetchone()[0] == 2
    cur.execute("SELECT COUNT(*) FROM campaign_schedules WHERE campaign_id=?", (cid,))
    count = cur.fetchone()[0]
    conn.close()
    assert count > 0
    assert manager.remove_target_group(gid1)
