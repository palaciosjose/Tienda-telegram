import sqlite3
from datetime import datetime
import files
import db

class CampaignDB:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_connection(self):
        if self.db_path == files.main_db:
            return db.get_db_connection(), True
        return sqlite3.connect(self.db_path), False

    def insert_campaign(self, data):
        conn, shared = self._get_connection()
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
        if not shared:
            conn.close()
        return campaign_id

    def fetch_all_campaigns(self):
        conn, shared = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, status FROM campaigns")
        rows = cursor.fetchall()
        if not shared:
            conn.close()
        result = []
        for r in rows:
            result.append({'id': r[0], 'name': r[1], 'status': r[2], 'sent_count': 0, 'last_sent': ''})
        return result

    def update_campaign(self, campaign_id, fields):
        """Actualizar campos de una campaña existente."""
        if not fields:
            return False

        conn, shared = self._get_connection()
        cursor = conn.cursor()

        columns = []
        params = []
        for key, value in fields.items():
            columns.append(f"{key} = ?")
            params.append(value)

        params.append(campaign_id)
        sql = "UPDATE campaigns SET " + ", ".join(columns) + " WHERE id = ?"
        cursor.execute(sql, tuple(params))
        conn.commit()
        updated = cursor.rowcount
        if not shared:
            conn.close()
        return updated > 0
