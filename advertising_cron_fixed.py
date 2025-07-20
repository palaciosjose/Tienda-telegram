#!/usr/bin/env python3
import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.append('/root/telegram-bot')

def get_pending_campaigns():
    """Función con rango de tiempo ±2 minutos"""
    try:
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()

        now = datetime.now()
        current_day = now.strftime('%A').lower()
        
        # Crear rango de ±2 minutos
        time_range = []
        for offset in [-2, -1, 0, 1, 2]:
            time_check = (now + timedelta(minutes=offset)).strftime('%H:%M')
            time_range.append(time_check)

        days_map = {
            'monday': 'lunes', 'tuesday': 'martes', 'wednesday': 'miercoles',
            'thursday': 'jueves', 'friday': 'viernes', 'saturday': 'sabado', 'sunday': 'domingo'
        }

        day_spanish = days_map.get(current_day, current_day)
        print(f"🔍 Buscando: día={day_spanish}, rango={time_range}")

        cursor.execute('''
        SELECT cs.*, c.name, c.message_text, c.media_file_id, c.media_type,
               c.button1_text, c.button1_url, c.button2_text, c.button2_url
        FROM campaign_schedules cs
        JOIN campaigns c ON cs.campaign_id = c.id
        WHERE cs.is_active = 1 AND c.status = 'active'
        ''')

        schedules = cursor.fetchall()
        pending = []

        for schedule in schedules:
            schedule_json = schedule[4]
            try:
                schedule_data = json.loads(schedule_json)
                if day_spanish in schedule_data:
                    times = schedule_data[day_spanish]
                    # Buscar en el rango de tiempo
                    if any(t in times for t in time_range):
                        print(f"✅ ENCONTRADA: Campaña {schedule[1]}")
                        pending.append(schedule)
            except json.JSONDecodeError:
                continue

        conn.close()
        return pending
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_campaign(campaign_data):
    """Enviar campaña completa con multimedia y botones"""
    try:
        import config
        from bot_instance import bot
        import telebot

        campaign_name = campaign_data[10]
        message = campaign_data[11] or ""
        media_file_id = campaign_data[12]
        media_type = campaign_data[13]
        button1_text = campaign_data[14]
        button1_url = campaign_data[15]

        # Truncar mensaje si es muy largo (límite 1000 caracteres)
        if len(message) > 800:
            message = message[:800] + "... [Ver más en el bot]"

        # Crear botón si existe
        markup = None
        if button1_text and button1_url:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(button1_text, url=button1_url))

        # Obtener grupos
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT group_id, group_name FROM target_groups WHERE platform = 'telegram' AND status = 'active'"
        )
        groups = cursor.fetchall()
        conn.close()

        sent_count = 0
        for group_id, group_name in groups:
            try:
                # Enviar con multimedia si existe
                if media_file_id and media_type == 'video':
                    bot.send_video(group_id, media_file_id, caption=message, reply_markup=markup)
                elif media_file_id and media_type == 'photo':
                    bot.send_photo(group_id, media_file_id, caption=message, reply_markup=markup)
                else:
                    bot.send_message(group_id, message, reply_markup=markup)
                
                print(f"✅ Enviado a {group_name}")
                sent_count += 1
            except Exception as e:
                print(f"❌ Error: {e}")

        return sent_count > 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print(f"AutoSender MEJORADO iniciado: {datetime.now()}")
    pending_campaigns = get_pending_campaigns()
    if pending_campaigns:
        for campaign in pending_campaigns:
            send_campaign(campaign)
    else:
        print("⏳ No hay campañas programadas")
