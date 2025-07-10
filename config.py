import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Obtener valores de las variables de entorno
admin_id_env = os.getenv('TELEGRAM_ADMIN_ID')
if not admin_id_env:
    raise RuntimeError('TELEGRAM_ADMIN_ID must be set')
admin_id = int(admin_id_env)
token = os.getenv('TELEGRAM_BOT_TOKEN')

# Parámetros opcionales para telebot.polling
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '2'))
POLL_TIMEOUT = int(os.getenv('POLL_TIMEOUT', '10'))
LONG_POLLING_TIMEOUT = int(os.getenv('LONG_POLLING_TIMEOUT', '10'))

# Verificar que el token esté configurado
if not token:
    print("ERROR: No se encontró TELEGRAM_BOT_TOKEN en el archivo .env")
    print("Asegúrate de que el archivo .env existe y contiene tu token")
    exit(1)

print("✅ Configuración cargada correctamente")
