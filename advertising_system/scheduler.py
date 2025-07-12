import sqlite3
import json
from datetime import datetime, timedelta
import files
import db

class CampaignScheduler:
    def __init__(self, db_path, shop_id=1):
        self.db_path = db_path
        self.shop_id = shop_id
        self.optimal_times = ['10:00', '15:00', '20:00']
        self.platform_delays = {
            'telegram': 60
        }

    def _get_connection(self):
        if self.db_path == files.main_db:
            return db.get_db_connection(), True
        return sqlite3.connect(self.db_path), False

    def create_daily_schedule(self, campaign_id, platforms=['telegram']):
        conn, shared = self._get_connection()
        cursor = conn.cursor()

        for platform in platforms:
            cursor.execute(
                "SELECT COUNT(*) FROM target_groups WHERE platform = ? AND status = 'active' AND shop_id = ?",
                (platform, self.shop_id)
            )
            group_count = cursor.fetchone()[0]
            if group_count == 0:
                continue

            groups_per_time = group_count // len(self.optimal_times)

            for i, send_time in enumerate(self.optimal_times):
                start_groups = i * groups_per_time
                end_groups = start_groups + groups_per_time
                estimated_duration = groups_per_time * (self.platform_delays[platform] / 60)
                schedule_data = {
                    'campaign_id': campaign_id,
                    'platform': platform,
                    'schedule_json': json.dumps({d: [send_time] for d in ['lunes','martes','miercoles','jueves','viernes','sabado','domingo']}),
                    'group_range': f'{start_groups}-{end_groups}',
                    'estimated_duration': estimated_duration,
                    'shop_id': self.shop_id
                }
                self.save_schedule(schedule_data)

        if not shared:
            conn.close()

    def save_schedule(self, data):
        conn, shared = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO campaign_schedules
               (campaign_id, schedule_name, frequency, schedule_json, target_platforms, created_date, shop_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                data['campaign_id'],
                'auto',
                'daily',
                data['schedule_json'],
                data['platform'],
                datetime.now().isoformat(),
                data.get('shop_id', self.shop_id),
            )
        )
        conn.commit()
        if not shared:
            conn.close()

    def get_pending_sends(self):
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    
    # Crear rango de ±2 minutos
    time_range = []
    for offset in [-2, -1, 0, 1, 2]:
        time_check = (now + timedelta(minutes=offset)).strftime('%H:%M')
        time_range.append(time_check)
        conn, shared = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT cs.*, c.name, c.message_text, c.media_file_id, c.media_type,
                   c.button1_text, c.button1_url, c.button2_text, c.button2_url
               FROM campaign_schedules cs
               JOIN campaigns c ON cs.campaign_id = c.id
               WHERE cs.is_active = 1 AND c.status = 'active' AND cs.shop_id = ? AND c.shop_id = ?""",
            (self.shop_id, self.shop_id),
        )
        rows = cursor.fetchall()
        pending = []
        day_map = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        today = day_map[now.weekday()]
        for row in rows:
            try:
                schedule = json.loads(row[4] or '{}')
            except Exception:
                continue
            if current_time in schedule.get(today, []):
                pending.append(row)

        if not shared:
            conn.close()
        return pending
    def update_next_send(self, schedule_id, platform):
        next_send = datetime.now() + timedelta(days=1)
        conn, shared = self._get_connection()
        cursor = conn.cursor()
        if platform == 'telegram':
            cursor.execute(
                "UPDATE campaign_schedules SET next_send_telegram = ? WHERE id = ?",
                (next_send.isoformat(), schedule_id))
        conn.commit()
        if not shared:
            conn.close()
