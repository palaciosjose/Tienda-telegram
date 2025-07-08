import telebot, sqlite3, shelve, os
import config, dop, files, subscriptions
from bot_instance import bot

def in_adminka(chat_id, message_text, username, name_user):
    """Función principal de administración"""
    if chat_id in dop.get_adminlist():
        if message_text == 'Volver al menú principal' or message_text == '/adm':
            if dop.get_sost(chat_id):
                with shelve.open(files.sost_bd) as bd: 
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
            
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('💬 Respuestas')
            user_markup.row('📦 Surtido', '➕ Producto')
            user_markup.row('💼 Suscripciones')
            user_markup.row('💰 Pagos')
            user_markup.row('📊 Stats', '📣 Difusión')
            user_markup.row('⚙️ Otros')
            bot.send_message(chat_id, '¡Panel de administración!\nPara salir: /start', reply_markup=user_markup)
        
        elif message_text == '💼 Suscripciones':
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Crear plan de suscripción')
            user_markup.row('Lista de planes')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Gestión de suscripciones:', reply_markup=user_markup)
        
        elif message_text == 'Lista de planes':
            try:
                plans = subscriptions.get_all_subscription_products()
                if plans:
                    text = '📋 *Planes disponibles:*\n\n'
                    for plan in plans:
                        if len(plan) >= 7:
                            pid, name, desc, price, currency, duration, unit = plan[:7]
                            text += f'- {pid}. {name} - ${price} {currency}/{duration}{unit}\n'
                        else:
                            text += f'- Plan incompleto: {plan}\n'
                else:
                    text = 'No hay planes de suscripción.'
                bot.send_message(chat_id, text, parse_mode='Markdown')
            except Exception as e:
                bot.send_message(chat_id, f'Error mostrando planes: {e}')
        
        elif message_text == '📊 Stats':
            try:
                result = dop.get_daily_sales()
                bot.send_message(chat_id, result, parse_mode='Markdown')
            except Exception as e:
                bot.send_message(chat_id, f'Stats: {dop.get_profit()} USD total')

def text_analytics(message_text, chat_id):
    """Función para analizar texto del admin"""
    if message_text in ('Volver al menú principal', '/adm'):
        with shelve.open(files.sost_bd) as bd:
            if str(chat_id) in bd:
                del bd[str(chat_id)]
        in_adminka(chat_id, 'Volver al menú principal', None, None)
        return

    if dop.get_sost(chat_id):
        with shelve.open(files.sost_bd) as bd:
            sost_num = bd.get(str(chat_id), 0)
        
        if sost_num == 1:  # Guardar mensaje
            try:
                message_type = 'start'  # Por defecto
                if os.path.exists(f'data/Temp/{chat_id}.txt'):
                    with open(f'data/Temp/{chat_id}.txt', 'r', encoding='utf-8') as f:
                        message_type = f.read().strip()
                
                with shelve.open(files.bot_message_bd) as bd_msg:
                    bd_msg[message_type] = message_text
                
                bot.send_message(chat_id, '✅ Mensaje guardado')
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
            except Exception as e:
                bot.send_message(chat_id, f'Error: {e}')

def ad_inline(callback_data, chat_id, message_id):
    """Manejar callbacks inline del admin"""
    if callback_data == 'Volver al menú principal de administración':
        if dop.get_sost(chat_id):
            with shelve.open(files.sost_bd) as bd:
                if str(chat_id) in bd:
                    del bd[str(chat_id)]
        
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('💬 Respuestas')
        user_markup.row('📦 Surtido', '➕ Producto')
        user_markup.row('💼 Suscripciones')
        user_markup.row('💰 Pagos')
        user_markup.row('⚙️ Otros')
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        bot.send_message(chat_id, '¡Panel de administración!', reply_markup=user_markup)

def handle_multimedia(message):
    """Manejar multimedia - versión básica"""
    chat_id = message.chat.id

    try:
        with shelve.open(files.sost_bd) as bd:
            state = bd.get(str(chat_id))

        if state not in (32, 48):
            return

        if state == 32:
            temp_path = f"data/Temp/{chat_id}media_product.txt"
        else:
            temp_path = f"data/Temp/{chat_id}media_plan.txt"

        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                product_name = f.read()
        except FileNotFoundError:
            bot.send_message(chat_id, '❌ La sesión anterior se perdió.')
            with shelve.open(files.sost_bd) as bd:
                if str(chat_id) in bd:
                    del bd[str(chat_id)]
            in_adminka(chat_id, 'Volver al menú principal', None, None)
            return

        file_id = None
        media_type = None
        caption = message.caption if message.caption else None

        if message.photo:
            file_id = message.photo[-1].file_id
            media_type = "photo"
        elif message.video:
            file_id = message.video.file_id
            media_type = "video"
        elif message.document:
            file_id = message.document.file_id
            media_type = "document"
        elif message.audio:
            file_id = message.audio.file_id
            media_type = "audio"
        elif message.animation:
            file_id = message.animation.file_id
            media_type = "animation"

        if file_id and media_type:
            if state == 32:
                saved = dop.save_product_media(product_name, file_id, media_type, caption)
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row("🎬 Multimedia productos")
                user_markup.row("Volver al menú principal")
            else:
                saved = subscriptions.save_plan_media(product_name, file_id, media_type, caption)
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row("🎬 Multimedia suscripciones")
                user_markup.row("Volver al menú principal")

            media_names = {
                "photo": "📸 Imagen",
                "video": "🎥 Video",
                "document": "📄 Documento",
                "audio": "🎵 Audio",
                "animation": "🎬 GIF",
            }

            if saved:
                target = "producto" if state == 32 else "plan"
                bot.send_message(
                    chat_id,
                    f"✅ {media_names.get(media_type, 'Archivo')} agregado al {target}: {product_name}",
                    reply_markup=user_markup,
                )
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
            else:
                bot.send_message(chat_id, "❌ Error guardando multimedia")
        else:
            bot.send_message(
                chat_id,
                "❌ Tipo de archivo no soportado. Envía: foto, video, documento, audio o GIF",
            )
    except Exception:
        pass
