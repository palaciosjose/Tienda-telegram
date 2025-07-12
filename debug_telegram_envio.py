import os
from dotenv import load_dotenv
from advertising_system.auto_sender import AutoSender

load_dotenv()

print("=== DEBUG ENVÍO TELEGRAM ===")

config = {
    'db_path': 'data/db/main_data.db',
    'telegram_tokens': ['7275890221:AAHjeLMyikGG_pnjA1SXtn1bC1UJ-G3UXDg'],
    'shop_id': 1
}

# Crear AutoSender y verificar si envía
auto_sender = AutoSender(config)

# Obtener grupos telegram
groups = auto_sender._get_telegram_groups()
print(f"Grupos telegram obtenidos: {len(groups)}")
for g in groups:
    print(f"  - {g}")

# Verificar tokens
print(f"Telegram bot inicializado: {auto_sender.telegram is not None}")

# Intentar envío manual a un grupo
if groups:
    group_id = groups[0]['group_id']
    print(f"Probando envío a {group_id}")
    
    success, result = auto_sender.telegram.send_message(
        group_id,
        "🔧 Mensaje de prueba del sistema automático",
        media_file_id=None,
        media_type=None,
        buttons=None
    )
    
    print(f"Resultado del envío: {success}")
    print(f"Mensaje de respuesta: {result}")
