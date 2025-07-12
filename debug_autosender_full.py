import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("=== DEBUG AUTO_SENDER COMPLETO ===")
print(f"Hora: {datetime.now()}")

# Importar scheduler y verificar
from advertising_system.scheduler import CampaignScheduler
scheduler = CampaignScheduler('data/db/main_data.db', shop_id=1)
pending_sends = scheduler.get_pending_sends()

print(f"Programaciones pendientes: {len(pending_sends)}")

if pending_sends:
    for send_data in pending_sends:
        schedule_id = send_data[0]
        campaign_id = send_data[1] 
        platforms = send_data[6].split(',')
        print(f"Schedule ID: {schedule_id}")
        print(f"Campaign ID: {campaign_id}")
        print(f"Platforms: {platforms}")
        
        # Verificar si hay grupos telegram
        import sqlite3
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, group_id, group_name FROM target_groups WHERE platform = 'telegram' AND status = 'active'",
        )
        groups = cursor.fetchall()
        print(f"Grupos Telegram activos: {len(groups)}")
        for g in groups:
            print(f"  - {g[2]} ({g[1]})")
        
        # Verificar token
        tokens_env = os.getenv("TELEGRAM_TOKEN")
        if tokens_env:
            telegram_tokens = [t.strip() for t in tokens_env.split(',') if t.strip()]
            print(f"Tokens disponibles: {len(telegram_tokens)}")
        else:
            print("❌ No hay TELEGRAM_TOKEN")
        
        conn.close()
else:
    print("❌ No hay programaciones pendientes en este momento")
