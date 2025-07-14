import time
import sqlite3
import logging
from datetime import datetime
import sys
import os

sys.path.insert(0, '/home/telegram-bot')
import config
from bot_instance import bot
import telebot

from .scheduler import CampaignScheduler

class AutoSender:
    def __init__(self, db_path, shop_id=1):
        self.scheduler = CampaignScheduler(db_path, shop_id)
        self.logger = logging.getLogger(__name__)

    def _get_connection(self):
        import files
        if self.scheduler.db_path == files.main_db:
            return sqlite3.connect(files.main_db), True
        return sqlite3.connect(self.scheduler.db_path), False

    def process_campaigns(self):
        processed = False
        pending_sends = self.scheduler.get_pending_sends()
        
        for send_data in pending_sends:
            if len(send_data) >= 3:
                schedule_id = send_data[0]
                campaign_id = send_data[1]
                if send_data[2] == 'telegram':
                    self._send_telegram_campaign(campaign_id, schedule_id, send_data)
                    processed = True
                    time.sleep(2)
        return processed

    def _send_telegram_campaign(self, campaign_id, schedule_id, campaign_data):
        conn, shared = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT group_id FROM target_groups WHERE status = "active" AND shop_id = ?', 
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
            
            full_message = f"{title}\n\n{message_text}" if message_text else title
            
            markup = None
            if button_text and button_url:
                markup = telebot.types.InlineKeyboardMarkup()
                button = telebot.types.InlineKeyboardButton(button_text, url=button_url)
                markup.add(button)
            
            for group in groups:
                group_id = group[0]
                try:
                    if media_file_id:
                        try:
                            bot.send_photo(group_id, media_file_id, caption=full_message, reply_markup=markup)
                        except:
                            bot.send_message(group_id, full_message, reply_markup=markup)
                    else:
                        bot.send_message(group_id, full_message, reply_markup=markup)
                    
                    print(f'🎉 Campaña automática {campaign_id} enviada a grupo {group_id}')
                except Exception as e:
                    print(f'❌ Error enviando campaña {campaign_id} a {group_id}: {e}')
            
            self.scheduler.update_next_send(schedule_id, 'telegram')
            
        finally:
            if not shared:
                conn.close()

    def start(self):
        print(f"AutoSender iniciado: {datetime.now()}")
        return self.process_campaigns()
