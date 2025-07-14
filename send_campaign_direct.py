#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/telegram-bot')
import config
from bot_instance import bot
import telebot
import sqlite3
import json
from datetime import datetime, timedelta

def should_send_now():
    conn = sqlite3.connect('data/db/main_data.db')
    cursor = conn.cursor()
    
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    current_day = now.strftime('%A').lower()
    
    time_range = []
    for offset in [-1, 0, 1]:
        time_check = (now + timedelta(minutes=offset)).strftime('%H:%M')
        time_range.append(time_check)
    
    cursor.execute('SELECT * FROM campaign_schedules WHERE is_active = 1')
    schedules = cursor.fetchall()
    
    for schedule in schedules:
        schedule_json = json.loads(schedule[4])
        campaign_id = schedule[1]
        schedule_id = schedule[0]
        last_sent = schedule[7]
        
        if current_day in schedule_json:
            times = schedule_json[current_day]
            for t in times:
                if t in time_range:
                    today_str = now.strftime('%Y-%m-%d')
                    if last_sent and today_str in last_sent:
                        continue
                    
                    send_campaign(campaign_id)
                    
                    next_send_time = f"{today_str} {t}"
                    cursor.execute('UPDATE campaign_schedules SET next_send_telegram = ? WHERE id = ?', 
                                 (next_send_time, schedule_id))
                    conn.commit()
                    print(f"✅ Marcado como enviado: {next_send_time}")
                    
                    conn.close()
                    return True
    
    conn.close()
    return False

def send_campaign(campaign_id):
    conn = sqlite3.connect('data/db/main_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT group_id FROM target_groups WHERE status = "active"')
    groups = cursor.fetchall()
    
    cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
    campaign = cursor.fetchone()
    
    if campaign and groups:
        title = campaign[1]           # name
        message_text = campaign[2]    # message_text  
        media_file_id = campaign[3]   # media_file_id
        media_type = campaign[4]      # media_type
        button_text = campaign[6]     # button1_text
        button_url = campaign[7]      # button1_url
        
        full_message = f"{title}\n\n{message_text}" if message_text else title
        
        markup = None
        if button_text and button_url:
            markup = telebot.types.InlineKeyboardMarkup()
            button = telebot.types.InlineKeyboardButton(button_text, url=button_url)
            markup.add(button)
        
        for group in groups:
            try:
                # ENVIAR CON MULTIMEDIA
                if media_file_id and media_type == 'photo':
                    bot.send_photo(group[0], media_file_id, caption=full_message, reply_markup=markup)
                elif media_file_id and media_type == 'video':
                    bot.send_video(group[0], media_file_id, caption=full_message, reply_markup=markup)
                else:
                    bot.send_message(group[0], full_message, reply_markup=markup)
                
                print(f'🎉 CAMPAÑA {campaign_id} CON MULTIMEDIA ENVIADA A {group[0]}')
            except Exception as e:
                print(f'❌ Error multimedia: {e}')
                # Si falla multimedia, enviar solo texto
                try:
                    bot.send_message(group[0], full_message, reply_markup=markup)
                    print(f'🎉 CAMPAÑA {campaign_id} SOLO TEXTO ENVIADA A {group[0]}')
                except Exception as e2:
                    print(f'❌ Error total: {e2}')
    
    conn.close()

if __name__ == '__main__':
    should_send_now()
