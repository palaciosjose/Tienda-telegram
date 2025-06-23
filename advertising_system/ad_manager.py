import sqlite3
import time
from datetime import datetime
from .campaign_database import CampaignDB
from .scheduler import CampaignScheduler

class AdvertisingManager:
    """Gestión de campañas publicitarias"""

    def __init__(self, db_path):
        self.db = CampaignDB(db_path)
        self.scheduler = CampaignScheduler(db_path)

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

    def schedule_campaign(self, campaign_id, platforms=None):
        """Crear un calendario diario para la campaña"""
        if platforms is None:
            platforms = ['telegram', 'whatsapp']
        self.scheduler.create_daily_schedule(campaign_id, platforms)

    def add_target_group(self, platform, group_id, group_name, category=None, notes=None):
        """Añadir un grupo objetivo"""
        return self.db.insert_target_group(platform, group_id, group_name, category, notes)

    def remove_target_group(self, group_id):
        """Eliminar un grupo objetivo"""
        return self.db.remove_target_group(group_id)

    def send_campaign_now(self, campaign_id, platforms=None):
        """Enviar una campaña de inmediato (versión simplificada)"""
        if platforms is None:
            platforms = ['telegram', 'whatsapp']
        campaign = self.db.fetch_campaign(campaign_id)
        if not campaign:
            raise ValueError('Campaign not found')
        groups = self.db.fetch_target_groups()
        targets = [g for g in groups if g['platform'] in platforms]
        # En un sistema real se enviarían mensajes aquí
        return len(targets)
