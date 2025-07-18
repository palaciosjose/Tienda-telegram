#!/usr/bin/env python3
import os
import sys
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Añadir ruta del bot
sys.path.append('/root/telegram-bot')

def get_pending_campaigns():
    """Función corregida para detectar campañas programadas"""
    try:
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        
        now = datetime.now()
        current_day = now.strftime('%A').lower()
        current_time = now.strftime('%H:%M')
        
        # Mapeo días inglés -> español
        days_map = {
            'monday': 'lunes', 'tuesday': 'martes', 'wednesday': 'miercoles',
            'thursday': 'jueves', 'friday': 'viernes', 'saturday': 'sabado', 'sunday': 'domingo'
        }
        
        day_spanish = days_map.get(current_day, current_day)
        
        print(f"🔍 Buscando: día={day_spanish}, hora={current_time}")
        
        # Buscar programaciones activas
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
            schedule_json = schedule[4]  # schedule_json column
            try:
                schedule_data = json.loads(schedule_json)
                
                # Verificar si hay programación para hoy
                if day_spanish in schedule_data:
                    times = schedule_data[day_spanish]
                    if current_time in times:
                        print(f"✅ ENCONTRADA: Campaña {schedule[1]} programada para {current_time}")
                        pending.append(schedule)
                        
            except json.JSONDecodeError:
                print(f"❌ Error JSON en schedule {schedule[0]}")
                continue
        
        conn.close()
        return pending
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_campaign(campaign_data):
    """Enviar campaña usando bot directo"""
    try:
        import config
        from bot_instance import bot
        
        campaign_id = campaign_data[1]
        campaign_name = campaign_data[10]
        message = campaign_data[11]  # message_text
        media_file_id = campaign_data[12]  # media_file_id
        media_type = campaign_data[13]     # media_type
        button1_text = campaign_data[14]   # button1_text
        button1_url = campaign_data[15]    # button1_url
        button2_text = campaign_data[16]   # button2_text
        button2_url = campaign_data[17]    # button2_url
        
        # Obtener grupos activos
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT group_id, group_name FROM target_groups WHERE platform = 'telegram' AND status = 'active' AND shop_id = 1"
        )
        groups = cursor.fetchall()
        conn.close()
        
        if not groups:
            print("❌ No hay grupos activos configurados")
            return False
            
        print(f"📤 Enviando a {len(groups)} grupos")
        
        # Construir markup si hay botones
        markup = None
        if button1_text and button1_url:
            import telebot
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(button1_text, url=button1_url))
            if button2_text and button2_url:
                markup.add(telebot.types.InlineKeyboardButton(button2_text, url=button2_url))
        
        # Mensaje completo
        full_message = f"📢 {campaign_name}\n\n{message}" if message else f"📢 {campaign_name}"
        
        sent_count = 0
        for group_id, group_name in groups:
            try:
                if media_file_id and media_type:
                    if media_type == 'photo':
                        bot.send_photo(group_id, media_file_id, caption=full_message, reply_markup=markup, parse_mode='Markdown')
                    elif media_type == 'video':
                        bot.send_video(group_id, media_file_id, caption=full_message, reply_markup=markup, parse_mode='Markdown')
                    elif media_type == 'document':
                        bot.send_document(group_id, media_file_id, caption=full_message, reply_markup=markup, parse_mode='Markdown')
                    else:
                        bot.send_message(group_id, full_message, reply_markup=markup, parse_mode='Markdown')
                else:
                    bot.send_message(group_id, full_message, reply_markup=markup, parse_mode='Markdown')
                    
                print(f"✅ Enviado a {group_name} ({group_id})")
                sent_count += 1
                
            except Exception as e:
                print(f"❌ Error enviando a {group_id}: {e}")
                
        print(f"📊 Campaña enviada a {sent_count}/{len(groups)} grupos")
        return sent_count > 0
        
    except Exception as e:
        print(f"❌ Error enviando: {e}")
        return False

if __name__ == "__main__":
    print(f"AutoSender CORREGIDO iniciado: {datetime.now()}")
    
    pending_campaigns = get_pending_campaigns()
    
    if pending_campaigns:
        print(f"🎯 Encontradas {len(pending_campaigns)} campañas para enviar")
        for campaign in pending_campaigns:
            send_campaign(campaign)
    else:
        print("⏳ No hay campañas programadas para este momento")
