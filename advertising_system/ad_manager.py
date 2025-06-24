import sqlite3
import re
from datetime import datetime
from .campaign_database import CampaignDB
from .scheduler import CampaignScheduler
from .telegram_multi import TelegramMultiBot
from .whaticket_api import WHATicketAPI
import os

class AdvertisingManager:
    """Gestión de campañas publicitarias"""

    def __init__(self, db_path):
        self.db = CampaignDB(db_path)
        self.scheduler = CampaignScheduler(db_path)
        self.db_path = db_path

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

    def schedule_campaign(self, campaign_id, send_time, platforms=None):
        """Programar una campaña para enviarse a una hora específica."""
        if platforms is None:
            platforms = ['telegram']

        if not re.match(r'^\d{2}:\d{2}$', send_time):
            return False, 'Formato de hora inválido'

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM campaigns WHERE id = ?', (campaign_id,))
        if not cur.fetchone():
            conn.close()
            return False, 'Campaña no encontrada'

        try:
            cur.execute(
                """INSERT INTO campaign_schedules
                   (campaign_id, schedule_name, frequency, send_times,
                    target_platforms, created_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    campaign_id,
                    'manual',
                    'once',
                    send_time,
                    ','.join(platforms),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()
            return True, 'Programación creada'
        except Exception as e:
            conn.close()
            return False, str(e)

    def add_target_group(self, platform, group_id, group_name=None):
        """Registrar un nuevo grupo objetivo."""
        platform = platform.lower()
        if platform not in ('telegram', 'whatsapp'):
            return False, 'Plataforma inválida'
        if not re.match(r'^-?\d+$', str(group_id)):
            return False, 'ID de grupo inválido'

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO target_groups
                   (platform, group_id, group_name, added_date)
                   VALUES (?, ?, ?, ?)""",
                (
                    platform,
                    str(group_id),
                    group_name,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()
            return True, 'Grupo agregado'
        except Exception as e:
            conn.close()
            return False, str(e)

    def remove_target_group(self, group_id):
        """Eliminar un grupo objetivo por su ID."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('DELETE FROM target_groups WHERE group_id = ?', (str(group_id),))
        conn.commit()
        removed = cur.rowcount
        conn.close()
        if removed:
            return True, 'Grupo eliminado'
        return False, 'Grupo no encontrado'

    def get_platform_configs(self):
        """Obtener la configuración de plataformas."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT platform, config_data, is_active FROM platform_config')
        rows = cur.fetchall()
        conn.close()
        return [
            {'platform': r[0], 'config_data': r[1], 'is_active': bool(r[2])}
            for r in rows
        ]

    def update_platform_config(self, platform, config_data=None, is_active=None):
        """Actualizar o crear la configuración de una plataforma."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM platform_config WHERE platform = ?', (platform,))
        exists = cur.fetchone() is not None
        if exists:
            fields = []
            params = []
            if config_data is not None:
                fields.append('config_data = ?')
                params.append(config_data)
            if is_active is not None:
                fields.append('is_active = ?')
                params.append(1 if is_active else 0)
            if fields:
                fields.append('last_updated = ?')
                params.append(datetime.now().isoformat())
                sql = 'UPDATE platform_config SET ' + ', '.join(fields) + ' WHERE platform = ?'
                params.append(platform)
                cur.execute(sql, tuple(params))
        else:
            cur.execute(
                'INSERT INTO platform_config (platform, config_data, is_active, last_updated) VALUES (?, ?, ?, ?)',
                (
                    platform,
                    config_data,
                    1 if is_active in (None, True) else 0,
                    datetime.now().isoformat(),
                ),
            )
        conn.commit()
        conn.close()
        return True

    def send_campaign_now(self, campaign_id, platforms=None):
        """Enviar una campaña inmediatamente registrando los envíos."""
        if platforms is None:
            platforms = ['telegram']

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """SELECT name, message_text, media_file_id, media_type,
                      button1_text, button1_url, button2_text, button2_url
                   FROM campaigns WHERE id = ? AND status = 'active'""",
            (campaign_id,),
        )
        campaign = cur.fetchone()
        if not campaign:
            conn.close()
            return False, 'Campaña no encontrada'

        telegram_tokens = [t.strip() for t in os.getenv('TELEGRAM_TOKEN', '').split(',') if t.strip()]
        telegram_bot = TelegramMultiBot(telegram_tokens) if telegram_tokens else None
        whatsapp_api = WHATicketAPI(
            os.getenv('WHATICKET_URL', 'https://whaticket.local'),
            os.getenv('WHATICKET_TOKEN', 'token'),
        )

        for platform in platforms:
            cur.execute(
                "SELECT group_id FROM target_groups WHERE platform = ? AND status = 'active'",
                (platform,),
            )
            groups = [g[0] for g in cur.fetchall()]
            for gid in groups:
                if platform == 'telegram' and telegram_bot:
                    success, resp = telegram_bot.send_message(
                        gid,
                        campaign[1],
                        campaign[2],
                        campaign[3],
                        {
                            'button1_text': campaign[4],
                            'button1_url': campaign[5],
                            'button2_text': campaign[6],
                            'button2_url': campaign[7],
                        },
                    )
                elif platform == 'whatsapp':
                    msg = campaign[1]
                    if campaign[4]:
                        msg += f"\n\n{campaign[4]}: {campaign[5]}"
                    if campaign[6]:
                        msg += f"\n{campaign[6]}: {campaign[7]}"
                    media = campaign[2] if campaign[3] == 'photo' else None
                    success, resp = whatsapp_api.send_message(gid, msg, media)
                else:
                    success, resp = False, 'Plataforma no soportada'

                cur.execute(
                    """INSERT INTO send_logs
                           (campaign_id, group_id, platform, status, sent_date, response_time, error_message)
                           VALUES (?, ?, ?, ?, ?, 0, ?)""",
                    (
                        campaign_id,
                        gid,
                        platform,
                        'sent' if success else 'failed',
                        datetime.now().isoformat(),
                        '' if success else str(resp),
                    ),
                )

        conn.commit()
        conn.close()
        return True, 'Campaña enviada'
