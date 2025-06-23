import sqlite3
from datetime import datetime

class CampaignDB:
    def __init__(self, db_path):
        self.db_path = db_path

    def insert_campaign(self, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO campaigns 
            (name, message_text, media_file_id, media_type, media_caption,
             button1_text, button1_url, button2_text, button2_url, created_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data['name'], data['message_text'], data.get('media_file_id'),
                data.get('media_type'), data.get('media_caption'),
                data.get('button1_text'), data.get('button1_url'),
                data.get('button2_text'), data.get('button2_url'),
                datetime.now().isoformat(), data.get('created_by')
            )
        )
        campaign_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return campaign_id

    def fetch_all_campaigns(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, status FROM campaigns")
        rows = cursor.fetchall()
        conn.close()
        result = []
        for r in rows:
            result.append({'id': r[0], 'name': r[1], 'status': r[2], 'sent_count': 0, 'last_sent': ''})
        return result

    def fetch_campaign(self, campaign_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, name, message_text, media_file_id, media_type, media_caption,
                      button1_text, button1_url, button2_text, button2_url
               FROM campaigns WHERE id = ?""",
            (campaign_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        keys = ['id', 'name', 'message_text', 'media_file_id', 'media_type', 'media_caption',
                'button1_text', 'button1_url', 'button2_text', 'button2_url']
        return dict(zip(keys, row))

    def insert_target_group(self, platform, group_id, group_name, category=None, notes=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO target_groups (platform, group_id, group_name, category, added_date, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (platform, str(group_id), group_name, category, datetime.now().isoformat(), notes)
        )
        gid = cursor.lastrowid
        conn.commit()
        conn.close()
        return gid

    def remove_target_group(self, group_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM target_groups WHERE id = ? OR group_id = ?", (group_id, str(group_id)))
        removed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return removed

    def fetch_target_groups(self, platform=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if platform:
            cursor.execute(
                "SELECT id, platform, group_id, group_name FROM target_groups WHERE status='active' AND platform=?",
                (platform,)
            )
        else:
            cursor.execute(
                "SELECT id, platform, group_id, group_name FROM target_groups WHERE status='active'"
            )
        rows = cursor.fetchall()
        conn.close()
        return [
            {'id': r[0], 'platform': r[1], 'group_id': r[2], 'group_name': r[3]}
            for r in rows
        ]
