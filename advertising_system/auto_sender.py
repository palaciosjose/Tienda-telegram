import sqlite3
import time
import threading
import logging
import os
import files
import db
from .scheduler import CampaignScheduler
from .telegram_multi import TelegramMultiBot
from .rate_limiter import IntelligentRateLimiter
from .statistics import StatisticsManager

class AutoSender:
    def __init__(self, config):
        shop_id = config.get('shop_id', 1)
        self.scheduler = CampaignScheduler(config['db_path'], shop_id)
        self.rate_limiter = IntelligentRateLimiter(config['db_path'], shop_id)
        self.stats = StatisticsManager(config['db_path'], shop_id)
        self.telegram = TelegramMultiBot(config['telegram_tokens'])
        self.running = False
        self.thread = None
        logging.basicConfig(filename='data/advertising.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _get_connection(self):
        if self.scheduler.db_path == files.main_db:
            return db.get_db_connection(), True
        return sqlite3.connect(self.scheduler.db_path), False

    def start(self):
        if self.running:
            return False
        self.running = True
        # Save PID so other processes can check if we are running
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/autosender.pid', 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self.logger.error(f"No se pudo escribir autosender.pid: {e}")
        self.thread = threading.Thread(target=self._main_loop)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("AutoSender iniciado")
        return True

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        try:
            pid_file = 'data/autosender.pid'
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid_in_file = f.read().strip()
                if pid_in_file == str(os.getpid()):
                    os.remove(pid_file)
        except Exception as e:
            self.logger.error(f"No se pudo eliminar autosender.pid: {e}")
        self.logger.info("AutoSender detenido")

    def _main_loop(self):
        while self.running:
            try:
                sent_any = self._check_and_send_campaigns()
                time.sleep(30 if sent_any else 60)
            except Exception as e:
                self.logger.error(f"Error en main loop: {e}")
                time.sleep(60)

    def _check_and_send_campaigns(self):
        pending_sends = self.scheduler.get_pending_sends()
        processed = False
        for send_data in pending_sends:
            schedule_id = send_data[0]
            campaign_id = send_data[1]
            if not send_data[5]:
                continue
            platforms = send_data[5].split(',')
            for platform in platforms:
                if platform == 'telegram':
                    self._send_telegram_campaign(campaign_id, schedule_id, send_data)
                    processed = True
                    time.sleep(2)
        return processed

    def _get_telegram_groups(self):
        conn, shared = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, group_id, group_name FROM target_groups WHERE platform = 'telegram' AND status = 'active' AND shop_id = ?",
            (self.scheduler.shop_id,)
        )
        rows = cursor.fetchall()
        if not shared:
            conn.close()
        return [{'id': r[0], 'group_id': r[1], 'group_name': r[2]} for r in rows]

    def _mark_group_blocked(self, group_id):
        conn, shared = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE target_groups SET status = 'blocked' WHERE id = ? AND shop_id = ?",
            (group_id, self.scheduler.shop_id),
        )
        conn.commit()
        if not shared:
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
                'message': campaign_data[11],
                'media_file_id': campaign_data[12],
                'media_type': campaign_data[13],
                'buttons': {
                    'button1_text': campaign_data[14],
                    'button1_url': campaign_data[15],
                    'button2_text': campaign_data[16],
                    'button2_url': campaign_data[17]
                }
            }
            success, result = self.telegram.send_message(
                group['group_id'],
                message_data['message'],
                media_file_id=message_data['media_file_id'],
                media_type=message_data['media_type'],
                buttons=message_data['buttons']
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

