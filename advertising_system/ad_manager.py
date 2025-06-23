import sqlite3
from datetime import datetime
from .campaign_database import CampaignDB

class AdvertisingManager:
    """Gestión de campañas publicitarias"""

    def __init__(self, db_path):
        self.db = CampaignDB(db_path)

    def create_campaign(self, data):
        """Crear una nueva campaña"""
        return self.db.insert_campaign(data)

    def get_all_campaigns(self):
        """Obtener todas las campañas"""
        return self.db.fetch_all_campaigns()

    def get_today_stats(self):
        """Obtener estadísticas rápidas del día"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "SELECT COUNT(*) FROM send_logs WHERE DATE(sent_date) = ?",
            (today,)
        )
        sent = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM target_groups WHERE status = 'active'",
        )
        groups = cursor.fetchone()[0]
        conn.close()
        return {
            'sent': sent,
            'success_rate': 100,
            'groups': groups
        }
