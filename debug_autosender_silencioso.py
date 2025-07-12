import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("=== DEBUG AUTOSENDER ERRORES SILENCIOSOS ===")

# Simular EXACTAMENTE lo que hace advertising_cron.py
def load_config():
    tokens_env = os.getenv("TELEGRAM_TOKEN")
    if not tokens_env:
        raise SystemExit("TELEGRAM_TOKEN environment variable is required")
    telegram_tokens = [t.strip() for t in tokens_env.split(',') if t.strip()]
    if not telegram_tokens:
        raise SystemExit("TELEGRAM_TOKEN is empty")
    return {
        'db_path': 'data/db/main_data.db',
        'telegram_tokens': telegram_tokens
    }

# Cargar config como lo hace advertising_cron.py
config = load_config()
print(f"Config: {config}")

# Importar y crear AutoSender como lo hace advertising_cron.py
from advertising_system.auto_sender import AutoSender

print("Creando AutoSender...")
auto_sender = AutoSender(config)
print(f"AutoSender creado. Shop ID: {getattr(auto_sender.scheduler, 'shop_id', 'No definido')}")

# Llamar al método que se ejecuta en el loop principal
print("\nEjecutando _check_and_send_campaigns...")
try:
    result = auto_sender._check_and_send_campaigns()
    print(f"Resultado: {result}")
    print(f"Tipo de resultado: {type(result)}")
except Exception as e:
    print(f"ERROR CAPTURADO: {e}")
    import traceback
    traceback.print_exc()

# Verificar si el problema está en el constructor del AutoSender
print(f"\nVerificaciones finales:")
print(f"  Scheduler shop_id: {auto_sender.scheduler.shop_id}")
print(f"  Rate limiter: {auto_sender.rate_limiter is not None}")
print(f"  Telegram bot: {auto_sender.telegram is not None}")
print(f"  Stats: {auto_sender.stats is not None}")
