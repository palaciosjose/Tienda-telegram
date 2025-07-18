#!/usr/bin/env python3
import os
import sys
from datetime import datetime
import sqlite3
import json
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
    """Enviar campaña usando AutoSender"""
    try:
        from advertising_system.auto_sender import AutoSender
        
        config = {
            'db_path': 'data/db/main_data.db',
            'telegram_tokens': [os.getenv('TELEGRAM_TOKEN')],
            'shop_id': 1
        }
        
        auto_sender = AutoSender(config)
        groups = auto_sender._get_telegram_groups()
        
        message = campaign_data[12]  # message_text
        campaign_name = campaign_data[11]  # name
        
        sent_count = 0
        for group in groups:
            success, result = auto_sender.telegram.send_message(
                group['group_id'],
                f"📢 {campaign_name}\n\n{message}",
                media_file_id=campaign_data[13],  # media_file_id
                media_type=campaign_data[14],     # media_type
                buttons={
                    'button1_text': campaign_data[15],  # button1_text
                    'button1_url': campaign_data[16],   # button1_url
                    'button2_text': campaign_data[17],  # button2_text
                    'button2_url': campaign_data[18]    # button2_url
                }
            )
            if success:
                sent_count += 1
                
        print(f"📤 Campaña enviada a {sent_count} grupos")
        return True
        
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
