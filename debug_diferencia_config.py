import os
from datetime import datetime
from dotenv import load_dotenv
from advertising_system.auto_sender import AutoSender
from advertising_system.scheduler import CampaignScheduler

load_dotenv()

print(f"=== DEBUG DIFERENCIA CONFIG - {datetime.now()} ===")

# 1. Scheduler manual (funciona)
print("1. SCHEDULER MANUAL:")
scheduler_manual = CampaignScheduler('data/db/main_data.db', shop_id=1)
pending_manual = scheduler_manual.get_pending_sends()
print(f"   Shop ID: 1")
print(f"   Pending: {len(pending_manual)}")

# 2. AutoSender (no funciona)
print("\n2. AUTOSENDER:")
token = os.getenv("TELEGRAM_TOKEN")
if not token:
    raise RuntimeError("Set TELEGRAM_TOKEN environment variable with your bot token")

config = {
    'db_path': 'data/db/main_data.db',
    'telegram_tokens': [token],
    'shop_id': 1
}
auto_sender = AutoSender(config)
pending_auto = auto_sender.scheduler.get_pending_sends()
print(f"   Shop ID AutoSender: {auto_sender.scheduler.shop_id}")
print(f"   Pending AutoSender: {len(pending_auto)}")

# 3. Crear scheduler igual que AutoSender
print("\n3. SCHEDULER COMO AUTOSENDER:")
shop_id_auto = config.get('shop_id', 1)
scheduler_como_auto = CampaignScheduler(config['db_path'], shop_id_auto)
pending_como_auto = scheduler_como_auto.get_pending_sends()
print(f"   Shop ID como auto: {shop_id_auto}")
print(f"   Pending como auto: {len(pending_como_auto)}")

# 4. Verificar AutoSender.__init__
print(f"\n4. VERIFICACIÓN AUTOSENDER:")
print(f"   Config recibido: {config}")
print(f"   DB path: {auto_sender.scheduler.db_path}")
print(f"   Shop ID final: {auto_sender.scheduler.shop_id}")

# 5. Debug detallado de la query del AutoSender
print(f"\n5. DEBUG QUERY AUTOSENDER:")
import sqlite3
conn = sqlite3.connect('data/db/main_data.db')
cursor = conn.cursor()
shop_id_test = auto_sender.scheduler.shop_id
cursor.execute(
    """SELECT COUNT(*) FROM campaign_schedules cs
       JOIN campaigns c ON cs.campaign_id = c.id
       WHERE cs.is_active = 1 AND c.status = 'active' AND cs.shop_id = ? AND c.shop_id = ?""",
    (shop_id_test, shop_id_test),
)
count = cursor.fetchone()[0]
print(f"   Filas que encuentra AutoSender con shop_id {shop_id_test}: {count}")
conn.close()
