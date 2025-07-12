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
        
        bot.process_new_updates([update])
        print("✅ Update enviado al bot")
        return "OK", 200
    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        return f"Error: {e}", 500

@app.route('/test')
def test():
    return "Bot funcionando", 200

@bot.message_handler(commands=['start'])
def start_command(message):
    print(f"🎯 Comando /start recibido de {message.from_user.id}")
    bot.reply_to(message, "¡Hola! El bot está funcionando correctamente.")

@bot.message_handler(commands=['test'])
def test_command(message):
    print(f"🧪 Comando /test recibido de {message.from_user.id}")
    bot.reply_to(message, "✅ Test exitoso!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(f"💬 Mensaje recibido: {message.text}")
    bot.reply_to(message, f"Recibido: {message.text}")

if __name__ == '__main__':
    print("🚀 Bot debug iniciando...")
    app.run(host='0.0.0.0', port=8443, debug=True)
