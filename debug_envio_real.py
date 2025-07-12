import os
from datetime import datetime
from dotenv import load_dotenv
from advertising_system.scheduler import CampaignScheduler

load_dotenv()

print(f"=== DEBUG ENVÍO REAL - {datetime.now()} ===")

# Obtener programaciones pendientes
scheduler = CampaignScheduler('data/db/main_data.db', shop_id=1)
pending_sends = scheduler.get_pending_sends()

print(f"Programaciones pendientes: {len(pending_sends)}")

if pending_sends:
    send_data = pending_sends[0]
    schedule_id = send_data[0]
    campaign_id = send_data[1]
    platforms = send_data[5].split(',')  # Corregido: [5] no [6]
    
    print(f"Schedule ID: {schedule_id}")
    print(f"Campaign ID: {campaign_id}")
    print(f"Platforms: {platforms}")
    
    # Verificar grupos telegram
    import sqlite3
    conn = sqlite3.connect('data/db/main_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, group_id, group_name FROM target_groups WHERE platform = 'telegram' AND status = 'active' AND shop_id = 1",
    )
    groups = cursor.fetchall()
    print(f"Grupos Telegram activos: {len(groups)}")
    
    if groups:
        for g in groups:
            print(f"  - {g[2]} ({g[1]})")
        print("✅ HAY GRUPOS PARA ENVIAR")
    else:
        print("❌ NO HAY GRUPOS ACTIVOS")
    
    # Verificar mensaje de campaña
    message_text = send_data[11]
    print(f"Mensaje a enviar: {message_text[:100]}...")
    
    conn.close()
else:
    print("❌ No hay programaciones pendientes")
