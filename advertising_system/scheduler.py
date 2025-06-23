import sqlite3
from datetime import datetime, timedelta
import json

class CampaignScheduler:
    def __init__(self, db_path):
        self.db_path = db_path
        self.optimal_times = ['10:00', '15:00', '20:00']
        self.platform_delays = {
            'telegram': 60,
            'whatsapp': 90
        }

    def create_daily_schedule(self, campaign_id, platforms=['telegram', 'whatsapp']):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for platform in platforms:
            cursor.execute(
                "SELECT COUNT(*) FROM target_groups WHERE platform = ? AND status = 'active'",
                (platform,)
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
                    'send_time': send_time,
                    'group_range': f'{start_groups}-{end_groups}',
                    'estimated_duration': estimated_duration
                }
                self.save_schedule(schedule_data)

        conn.close()

    def save_schedule(self, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO campaign_schedules
               (campaign_id, schedule_name, frequency, send_times, target_platforms, created_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                data['campaign_id'], 'auto', 'daily', data['send_time'], data['platform'], datetime.now().isoformat()
            )
        )
        conn.commit()
        conn.close()

    def get_pending_sends(self):
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT cs.*, c.name, c.message_text, c.media_file_id, c.media_type,
                   c.button1_text, c.button1_url, c.button2_text, c.button2_url
               FROM campaign_schedules cs
               JOIN campaigns c ON cs.campaign_id = c.id
               WHERE cs.is_active = 1 AND c.status = 'active' AND cs.send_times LIKE ?""",
            (f'%{current_time}%',)
        )
        pending = cursor.fetchall()
        conn.close()
        return pending

    def update_next_send(self, schedule_id, platform):
        next_send = datetime.now() + timedelta(days=1)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if platform == 'telegram':
            cursor.execute("UPDATE campaign_schedules SET next_send_telegram = ? WHERE id = ?", (next_send.isoformat(), schedule_id))
        else:
            cursor.execute("UPDATE campaign_schedules SET next_send_whatsapp = ? WHERE id = ?", (next_send.isoformat(), schedule_id))
        conn.commit()
        conn.close()
