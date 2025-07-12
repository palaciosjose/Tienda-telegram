import sqlite3
import json
from datetime import datetime, timedelta

# Simular exactamente las 00:40 (cuando se ejecutó el cron)
test_time = datetime(2025, 7, 12, 0, 40, 8)
day_map = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
today = day_map[test_time.weekday()]

# Rango que habría usado el sistema a las 00:40:08
time_range = []
for offset in [-2, -1, 0, 1, 2]:
    time_check = (test_time + timedelta(minutes=offset)).strftime('%H:%M')
    time_range.append(time_check)

print(f"Simulando: {test_time}")
print(f"Día: {today}")
print(f"Rango que buscó: {time_range}")

# Buscar la programación específica para 00:39
conn = sqlite3.connect('data/db/main_data.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT cs.schedule_json, c.name
    FROM campaign_schedules cs
    JOIN campaigns c ON cs.campaign_id = c.id
    WHERE cs.is_active = 1 AND c.status = 'active'
    AND cs.schedule_json LIKE '%00:39%'
""")

for row in cursor.fetchall():
    schedule = json.loads(row[0])
    scheduled_times = schedule.get(today, [])
    
    print(f"\nCampaña: {row[1]}")
    print(f"Programada para: {scheduled_times}")
    
    if any(t in scheduled_times for t in time_range):
        print("✅ DEBERÍA HABER FUNCIONADO!")
    else:
        print("❌ No funcionó")
        print(f"Buscaba: {time_range}")
        print(f"En: {scheduled_times}")
        
        # Verificar si 00:39 está en el rango
        if '00:39' in time_range:
            print("🔍 '00:39' SÍ está en el rango - HAY UN BUG")
        else:
            print("🔍 '00:39' NO está en el rango - problema de timing")

conn.close()
