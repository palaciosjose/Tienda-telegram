import sqlite3
import json
from datetime import datetime, timedelta

now = datetime.now()
current_time = now.strftime('%H:%M')
day_map = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
today = day_map[now.weekday()]

# Mismo rango que usa el scheduler modificado
time_range = []
for offset in [-2, -1, 0, 1, 2]:
    time_check = (now + timedelta(minutes=offset)).strftime('%H:%M')
    time_range.append(time_check)

print(f"Hora actual: {current_time}")
print(f"Día: {today}")
print(f"Rango de búsqueda: {time_range}")

# Buscar programaciones como lo hace el sistema
conn = sqlite3.connect('data/db/main_data.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT cs.schedule_json, c.name
    FROM campaign_schedules cs
    JOIN campaigns c ON cs.campaign_id = c.id
    WHERE cs.is_active = 1 AND c.status = 'active'
""")

found = 0
for row in cursor.fetchall():
    schedule = json.loads(row[0])
    scheduled_times = schedule.get(today, [])
    
    if any(t in scheduled_times for t in time_range):
        print(f"✅ MATCH ENCONTRADO: {row[1]} - {scheduled_times}")
        found += 1
    else:
        print(f"❌ Sin match: {row[1]} - {scheduled_times}")

print(f"\nTotal matches: {found}")
