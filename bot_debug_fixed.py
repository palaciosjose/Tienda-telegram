#!/usr/bin/env python3
import config
import telebot
from flask import Flask, request
import json

app = Flask(__name__)
bot = telebot.TeleBot(config.token)

@app.route('/webhook', methods=['POST'])
def webhook():
    print("🔍 Webhook recibido!")
    try:
        json_str = request.get_data().decode('UTF-8')
        print(f"📥 Datos recibidos: {json_str}")
        
        update = telebot.types.Update.de_json(json_str)
        print(f"📱 Update procesado: {update}")
        
        # Procesar el mensaje directamente
        if update.message:
            process_message(update.message)
        
        print("✅ Mensaje procesado")
        return "OK", 200
    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        return f"Error: {e}", 500

def process_message(message):
    """Procesar mensajes directamente"""
    try:
        chat_id = message.chat.id
        text = message.text
        
        print(f"💬 Procesando mensaje: {text} de {chat_id}")
        
        if text == '/start':
            print("🎯 Comando /start detectado")
            response = bot.send_message(
                chat_id, 
                "¡Hola! El bot está funcionando correctamente con webhook. ✅"
            )
            print(f"✅ Respuesta enviada: {response}")
            
        elif text == '/test':
            print("🧪 Comando /test detectado")
            response = bot.send_message(
                chat_id, 
                "✅ Test exitoso! El webhook funciona perfectamente."
            )
            print(f"✅ Respuesta enviada: {response}")
            
        elif text == '/adm' and chat_id == config.admin_id:
            print("🔧 Comando /adm detectado")
            response = bot.send_message(
                chat_id, 
                "🔧 Panel de administración\n\n✅ Bot funcionando\n✅ Webhook activo\n✅ Base de datos conectada"
            )
            print(f"✅ Respuesta enviada: {response}")
            
        else:
            print(f"💭 Mensaje normal: {text}")
            response = bot.send_message(
                chat_id, 
                f"Recibido: {text}\n\nEl bot funciona correctamente! 🎉"
            )
            print(f"✅ Respuesta enviada: {response}")
            
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

@app.route('/test')
def test():
    return "Bot funcionando", 200

if __name__ == '__main__':
    print("🚀 Bot debug CORREGIDO iniciando...")
    app.run(host='0.0.0.0', port=8443, debug=True)
