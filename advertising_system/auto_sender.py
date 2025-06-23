import sqlite3
import time
import threading
import logging
from .scheduler import CampaignScheduler
from .telegram_multi import TelegramMultiBot
from .whaticket_api import WHATicketAPI
from .rate_limiter import IntelligentRateLimiter
from .statistics import StatisticsManager

class AutoSender:
    def __init__(self, config):
        self.scheduler = CampaignScheduler(config['db_path'])
        self.rate_limiter = IntelligentRateLimiter(config['db_path'])
        self.stats = StatisticsManager(config['db_path'])
        self.telegram = TelegramMultiBot(config['telegram_tokens'])
        self.whatsapp = WHATicketAPI(config['whaticket_url'], config['whaticket_token'])
        self.running = False
        self.thread = None
        logging.basicConfig(filename='data/advertising.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def start(self):
        if self.running:
            return False
        self.running = True
        self.thread = threading.Thread(target=self._main_loop)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("AutoSender iniciado")
        return True

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.logger.info("AutoSender detenido")

    def _main_loop(self):
        while self.running:
            try:
                self._check_and_send_campaigns()
                time.sleep(30)
            except Exception as e:
                self.logger.error(f"Error en main loop: {e}")
                time.sleep(60)

    def _check_and_send_campaigns(self):
        pending_sends = self.scheduler.get_pending_sends()
        for send_data in pending_sends:
            schedule_id = send_data[0]
            campaign_id = send_data[1]
            platforms = send_data[6].split(',')
            for platform in platforms:
                if platform == 'telegram':
                    self._send_telegram_campaign(campaign_id, schedule_id, send_data)
                elif platform == 'whatsapp':
                    self._send_whatsapp_campaign(campaign_id, schedule_id, send_data)
                time.sleep(2)

    def _get_telegram_groups(self):
        conn = sqlite3.connect(self.scheduler.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, group_id, group_name FROM target_groups WHERE platform = 'telegram' AND status = 'active'")
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'group_id': r[1], 'group_name': r[2]} for r in rows]

    def _get_whatsapp_groups(self):
        conn = sqlite3.connect(self.scheduler.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, group_id, group_name FROM target_groups WHERE platform = 'whatsapp' AND status = 'active'")
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'group_id': r[1], 'group_name': r[2]} for r in rows]

    def _mark_group_blocked(self, group_id):
        conn = sqlite3.connect(self.scheduler.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE target_groups SET status = 'blocked' WHERE id = ?", (group_id,))
        conn.commit()
        conn.close()

    def _send_telegram_campaign(self, campaign_id, schedule_id, campaign_data):
        groups = self._get_telegram_groups()
        for group in groups:
            can_send, reason = self.rate_limiter.can_send('telegram')
            if not can_send:
                self.logger.warning(f"Rate limit Telegram: {reason}")
                time.sleep(60)
                continue
            message_data = {
                'message': campaign_data[8],
                'media_file_id': campaign_data[9],
                'media_type': campaign_data[10],
                'buttons': {
                    'button1_text': campaign_data[11],
                    'button1_url': campaign_data[12],
                    'button2_text': campaign_data[13],
                    'button2_url': campaign_data[14]
                }
            }
            success, result = self.telegram.send_message(
                group['group_id'],
                message_data['message'],
                message_data['media_file_id'],
                message_data['media_type'],
                message_data['buttons']
            )
            self.rate_limiter.register_send('telegram', success)
            self.stats.log_send(campaign_id, group['group_id'], 'telegram', success, str(result))
            if success:
                self.logger.info(f"Telegram enviado a {group['group_name']}")
            else:
                self.logger.error(f"Error Telegram {group['group_name']}: {result}")
                if "bloqueado" in result.lower():
                    self._mark_group_blocked(group['id'])
            delay = self.rate_limiter.get_optimal_delay('telegram')
            time.sleep(delay)
        self.scheduler.update_next_send(schedule_id, 'telegram')

    def _send_whatsapp_campaign(self, campaign_id, schedule_id, campaign_data):
        groups = self._get_whatsapp_groups()
        for group in groups:
            can_send, reason = self.rate_limiter.can_send('whatsapp')
            if not can_send:
                self.logger.warning(f"Rate limit WhatsApp: {reason}")
                time.sleep(120)
                continue
            message = campaign_data[8]
            if campaign_data[11]:
                message += f"\n\n🔗 {campaign_data[11]}: {campaign_data[12]}"
            if campaign_data[13]:
                message += f"\n🔗 {campaign_data[13]}: {campaign_data[14]}"
            success, result = self.whatsapp.send_message(
                group['group_id'],
                message,
                campaign_data[9] if campaign_data[10] == 'photo' else None
            )
            self.rate_limiter.register_send('whatsapp', success)
            self.stats.log_send(campaign_id, group['group_id'], 'whatsapp', success, str(result))
            if success:
                self.logger.info(f"WhatsApp enviado a {group['group_name']}")
            else:
                self.logger.error(f"Error WhatsApp {group['group_name']}: {result}")
            delay = self.rate_limiter.get_optimal_delay('whatsapp')
            time.sleep(delay)
        self.scheduler.update_next_send(schedule_id, 'whatsapp')
