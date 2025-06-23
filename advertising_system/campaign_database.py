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
