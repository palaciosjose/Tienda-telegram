import telebot, sqlite3, shelve, os
import config, dop, files
from bot_instance import bot

def in_adminka(chat_id, message_text, username, name_user):
    """Función principal de administración"""
    if chat_id in dop.get_adminlist():
        normalized = message_text.strip().lower()
        if normalized in ('volver al menú principal', 'volver al menu principal', '/adm'):
            if dop.get_sost(chat_id):
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
            
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('💬 Respuestas')
            user_markup.row('📦 Surtido', '➕ Producto')
            user_markup.row('💰 Pagos')
            user_markup.row('📊 Stats', '📣 Difusión')
            user_markup.row('⚙️ Otros')
            bot.send_message(chat_id, '¡Panel de administración!\nPara salir: /start', reply_markup=user_markup)

        
        elif message_text == '📊 Stats':
            try:
                result = dop.get_daily_sales()
                bot.send_message(chat_id, result, parse_mode='Markdown')
            except Exception as e:
                bot.send_message(chat_id, f'Stats: {dop.get_profit()} USD total')

def text_analytics(message_text, chat_id):
    """Función para analizar texto del admin"""
    normalized = message_text.strip().lower()
    if normalized in ('volver al menú principal', 'volver al menu principal', '/adm'):
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

        if state != 32:
            return

        temp_path = f"data/Temp/{chat_id}media_product.txt"

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
            saved = dop.save_product_media(product_name, file_id, media_type, caption)
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row("🎬 Multimedia productos")
            user_markup.row("Volver al menú principal")

            media_names = {
                "photo": "📸 Imagen",
                "video": "🎥 Video",
                "document": "📄 Documento",
                "audio": "🎵 Audio",
                "animation": "🎬 GIF",
            }

            if saved:
                bot.send_message(
                    chat_id,
                    f"✅ {media_names.get(media_type, 'Archivo')} agregado al producto: {product_name}",
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
