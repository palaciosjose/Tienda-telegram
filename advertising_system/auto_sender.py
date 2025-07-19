import time
import sqlite3
import logging
from datetime import datetime
import sys
import os
sys.path.insert(0, '/home/telegram-bot')
import types
try:
    import config
except Exception:  # pragma: no cover - allow import without dotenv
    config = types.SimpleNamespace()
import telebot
from .scheduler import CampaignScheduler
from .rate_limiter import IntelligentRateLimiter
from .statistics import StatisticsManager
from .telegram_multi import TelegramMultiBot

class AutoSender:
    def __init__(self, config):
        db_path = config.get('db_path')
        shop_id = config.get('shop_id', 1)
        self.scheduler = CampaignScheduler(db_path, shop_id)
        self.rate_limiter = IntelligentRateLimiter(db_path, shop_id)
        self.stats = StatisticsManager(db_path, shop_id)
        self.logger = logging.getLogger(__name__)
        self.telegram_tokens = config.get('telegram_tokens', [])

    def _get_connection(self):
        import files
        if self.scheduler.db_path == files.main_db:
            return sqlite3.connect(files.main_db), True
        return sqlite3.connect(self.scheduler.db_path), False

    def _check_and_send_campaigns(self):
        pending_sends = self.scheduler.get_pending_sends()
        processed = False
        for send_data in pending_sends:
            if len(send_data) < 6:
                continue
            schedule_id, campaign_id = send_data[0], send_data[1]
            platforms = send_data[5]
            if not platforms:
                continue
            if isinstance(platforms, str):
                platforms = platforms.split(',')
            for platform in platforms:
                if platform == 'telegram':
                    self._send_telegram_campaign(campaign_id, schedule_id, send_data)
                    processed = True
                    time.sleep(2)
        return processed

    def process_campaigns(self):
        return self._check_and_send_campaigns()

    def _send_telegram_campaign(self, campaign_id, schedule_id, campaign_data):
        conn, shared = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT group_id, topic_id FROM target_groups WHERE status = "active" AND shop_id = ?', 
                          (self.scheduler.shop_id,))
            groups = cursor.fetchall()
            
            if not groups:
                return
            
            cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
            campaign = cursor.fetchone()
            
            if not campaign:
                return
            
            title = campaign[1]
            message_text = campaign[2]
            media_file_id = campaign[3] if campaign[3] else None
            button_text = campaign[6] if campaign[6] else None
            button_url = campaign[7] if campaign[7] else None
            
            full_message = f"📢 {title}\n\n{message_text}" if message_text else f"📢 {title}"
            
            # Obtener tokens
            tokens = self.telegram_tokens
            if not tokens:
                tokens_env = os.getenv("TELEGRAM_TOKEN")
                if not tokens_env:
                    print("❌ No hay tokens de Telegram configurados")
                    return
                tokens = [t.strip() for t in tokens_env.split(',') if t.strip()]
            telegram_bot = TelegramMultiBot(tokens)
            
            # Preparar botones
            buttons = None
            if button_text and button_url:
                buttons = {
                    'button1_text': button_text,
                    'button1_url': button_url
                }
            
            for group in groups:
                group_id = group[0]
                topic_id = group[1]
                # Debug information about the target group/topic
                self.logger.debug("group_id=%s, topic_id=%s", group_id, topic_id)
                try:
                    success, result = telegram_bot.send_message(
                        group_id,
                        full_message,
                        media_file_id=media_file_id,
                        media_type='photo' if media_file_id else None,
                        buttons=buttons,
                        topic_id=topic_id
                    )
                    
                    if success:
                        topic_info = f" (Topic: {topic_id})" if topic_id else " (Grupo principal)"
                        print(f'🎉 Campaña automática {campaign_id} enviada a grupo {group_id}{topic_info}')
                    else:
                        print(f'❌ Error enviando campaña {campaign_id} a {group_id}: {result}')
                        
                except Exception as e:
                    print(f'❌ Error enviando campaña {campaign_id} a {group_id}: {e}')
            
            self.scheduler.update_next_send(schedule_id, 'telegram')
            
        finally:
            if not shared:
                conn.close()

    def start(self):
        print(f"AutoSender iniciado: {datetime.now()}")
        return self.process_campaigns()
