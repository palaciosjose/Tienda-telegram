from datetime import datetime
from advertising_system.scheduler import CampaignScheduler

now = datetime.now()
print(f"Hora actual: {now}")
print(f"Hora formateada: {now.strftime('%H:%M')}")

# Crear rango de ±2 minutos
from datetime import timedelta
time_range = []
for offset in [-2, -1, 0, 1, 2]:
    time_check = (now + timedelta(minutes=offset)).strftime('%H:%M')
    time_range.append(time_check)

print(f"Rango de búsqueda: {time_range}")

scheduler = CampaignScheduler('data/db/main_data.db', shop_id=1)
pending = scheduler.get_pending_sends()
print(f"Pending encontrados: {len(pending)}")

# Buscar específicamente la programación 01:16
import sqlite3
conn = sqlite3.connect('data/db/main_data.db')
cursor = conn.cursor()
cursor.execute("SELECT schedule_json FROM campaign_schedules WHERE schedule_json LIKE '%01:16%'")
result = cursor.fetchall()
if result:
    print(f"✅ Programación 01:16 existe: {result[0][0]}")
    if '01:16' in time_range:
        print("✅ 01:16 está en el rango actual")
    else:
        print("❌ 01:16 NO está en el rango actual")
else:
    print("❌ No existe programación para 01:16")
conn.close()
