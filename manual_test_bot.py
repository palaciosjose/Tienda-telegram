import pytest
pytest.skip("manual script not intended for pytest", allow_module_level=True)

import telebot
import config # Importa tu archivo config para obtener el token y admin_id

try:
    # Inicializa el bot con tu token
    bot = telebot.TeleBot(config.token)
    print("Bot TeleBot inicializado correctamente.") # Mensaje de depuración

    # Intenta enviar un mensaje de prueba a tu ID de administrador
    bot.send_message(config.admin_id, "¡Hola! Este es un mensaje de prueba desde tu bot en el hosting.")
    print(f"Mensaje de prueba enviado a admin_id: {config.admin_id}.") # Mensaje de depuración

    # Esto hará que el bot escuche por actualizaciones (de forma muy básica)
    # bot.polling() # Comentamos esto por ahora para ver la salida inmediata
    print("El script test_bot.py terminó de ejecutarse.")

except Exception as e:
    print(f"¡Ocurrió un error al iniciar o enviar mensaje!: {e}")
    print("Asegúrate de que tu token en config.py sea correcto y que tu admin_id sea un número entero.")
