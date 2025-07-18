import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from advertising_system.auto_sender import AutoSender

load_dotenv()

print("=== DEBUG AUTOSENDER ===")
print(f"Hora: {datetime.now()}")

config = {
    'db_path': 'data/db/main_data.db',
    'telegram_tokens': ['7275890221:AAHjeLMyikGG_pnjA1SXtn1bC1UJ-G3UXDg']
}

# Simular AutoSender pero con debug
from advertising_system.scheduler import CampaignScheduler

scheduler = CampaignScheduler('data/db/main_data.db', shop_id=1)
pending = scheduler.get_pending_sends()

print(f"Programaciones pendientes encontradas: {len(pending)}")
for i, p in enumerate(pending):
    print(f"Pendiente {i+1}: Campaña ID {p[1]}, Schedule: {p[4]}")

if pending:
    print("✅ HAY PROGRAMACIONES PENDIENTES - El envío debería ocurrir")
else:
    print("❌ NO hay programaciones pendientes - Por eso no se envía")
