import sqlite3
from datetime import datetime

class StatisticsManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def log_send(self, campaign_id, group_id, platform, success, result):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO send_logs (campaign_id, group_id, platform, status, sent_date, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                group_id,
                platform,
                'sent' if success else 'failed',
                datetime.now().isoformat(),
                '' if success else result,
            ),
        )
        conn.commit()
        conn.close()

    def get_real_time_dashboard(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN platform = 'telegram' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN platform = 'whatsapp' THEN 1 ELSE 0 END)
            FROM send_logs
            WHERE DATE(sent_date) = ?
            """,
            (today,),
        )
        stats = cursor.fetchone()
        success_rate = (stats[1] / stats[0] * 100) if stats[0] else 0
        dashboard = f"""📊 **Dashboard de Marketing - {today}**

📤 **Mensajes enviados:** {stats[0]}
✅ **Exitosos:** {stats[1]} ({success_rate:.1f}%)
❌ **Fallidos:** {stats[0] - stats[1]}

📱 **Por plataforma:**
- Telegram: {stats[2]}
- WhatsApp: {stats[3]}"""
        conn.close()
        return dashboard
