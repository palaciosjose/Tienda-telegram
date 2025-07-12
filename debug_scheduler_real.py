import sqlite3
import json
from datetime import datetime, timedelta
import files
import db

# Copiar exactamente la lógica del scheduler modificado
def debug_get_pending_sends():
    print("=== DEBUG SCHEDULER REAL ===")
    
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    
    # Crear rango de ±2 minutos para matching más flexible
    time_range = []
    for offset in [-2, -1, 0, 1, 2]:
        time_check = (now + timedelta(minutes=offset)).strftime('%H:%M')
        time_range.append(time_check)
    
    print(f"Hora actual: {now}")
    print(f"Hora formateada: {current_time}")
    print(f"Rango de búsqueda: {time_range}")
    
    # Usar la misma conexión que usa el scheduler
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    # Misma query que usa el scheduler
    shop_id = 1
    cursor.execute(
        """SELECT cs.*, c.name, c.message_text, c.media_file_id, c.media_type,
                   c.button1_text, c.button1_url, c.button2_text, c.button2_url
               FROM campaign_schedules cs
               JOIN campaigns c ON cs.campaign_id = c.id
               WHERE cs.is_active = 1 AND c.status = 'active' AND cs.shop_id = ? AND c.shop_id = ?""",
        (shop_id, shop_id),
    )
    rows = cursor.fetchall()
    print(f"Filas obtenidas de BD: {len(rows)}")
    
    pending = []
    day_map = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    today = day_map[now.weekday()]
    print(f"Día actual: {today}")
    
    for i, row in enumerate(rows):
        print(f"\n--- Fila {i+1} ---")
        print(f"Campaign ID: {row[1]}")
        print(f"Schedule JSON raw: {row[4]}")
        
        try:
            schedule = json.loads(row[4] or '{}')
            print(f"Schedule parsed: {schedule}")
            
            scheduled_for_today = schedule.get(today, [])
            print(f"Programado para {today}: {scheduled_for_today}")
            
            # Buscar en el rango de tiempo en lugar de hora exacta
            match_found = any(t in scheduled_for_today for t in time_range)
            print(f"¿Hay match? {match_found}")
            
            if match_found:
                print("✅ AGREGANDO A PENDING")
                pending.append(row)
            else:
                print("❌ Sin match")
                
        except Exception as e:
            print(f"Error parseando JSON: {e}")
            continue
    
    print(f"\nTotal pending encontrados: {len(pending)}")
    return pending

# Ejecutar debug
result = debug_get_pending_sends()
