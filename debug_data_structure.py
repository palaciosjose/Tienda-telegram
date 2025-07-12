import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("=== DEBUG ESTRUCTURA DE DATOS ===")
print(f"Hora: {datetime.now()}")

# Importar scheduler y verificar
from advertising_system.scheduler import CampaignScheduler
scheduler = CampaignScheduler('data/db/main_data.db', shop_id=1)
pending_sends = scheduler.get_pending_sends()

print(f"Programaciones pendientes: {len(pending_sends)}")

if pending_sends:
    for i, send_data in enumerate(pending_sends):
        print(f"\n=== SEND_DATA {i+1} ===")
        print(f"Tipo: {type(send_data)}")
        print(f"Longitud: {len(send_data)}")
        
        # Mostrar cada campo con su índice
        for j, field in enumerate(send_data):
            print(f"[{j}]: {field} ({type(field)})")
        
        # Intentar identificar los campos importantes
        print(f"\nAnálisis:")
        print(f"  Schedule ID (probablemente [0]): {send_data[0]}")
        print(f"  Campaign ID (probablemente [1]): {send_data[1]}")
        
        # Buscar el campo que contiene 'telegram'
        for j, field in enumerate(send_data):
            if isinstance(field, str) and 'telegram' in field:
                print(f"  Platforms field encontrado en [{j}]: {field}")
                break
        else:
            print("  ❌ No se encontró campo de platforms")
        
        break  # Solo mostrar el primero para evitar spam
else:
    print("❌ No hay programaciones pendientes en este momento")
