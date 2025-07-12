import sqlite3
import json
from datetime import datetime

# Simular lo que hace advertising_cron.py
now = datetime.now()
current_time = now.strftime('%H:%M')
day_map = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
today = day_map[now.weekday()]

print(f"Hora que busca el sistema: {current_time}")
print(f"Día que busca: {today}")

# Ver programaciones
conn = sqlite3.connect('data/db/main_data.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT cs.schedule_json, c.name, cs.campaign_id
    FROM campaign_schedules cs
    JOIN campaigns c ON cs.campaign_id = c.id
    WHERE cs.is_active = 1 AND c.status = 'active'
""")

pending = []
for row in cursor.fetchall():
    try:
        schedule = json.loads(row[0])
        print(f"\nCampaña: {row[1]}")
        print(f"Schedule JSON: {schedule}")
        
        if current_time in schedule.get(today, []):
            pending.append(row)
            print(f"✅ MATCH ENCONTRADO para {current_time}")
        else:
            print(f"❌ No match. Busca '{current_time}' en {schedule.get(today, [])}")
    except Exception as e:
        print(f"Error parseando: {e}")

print(f"\nTotal matches encontrados: {len(pending)}")
