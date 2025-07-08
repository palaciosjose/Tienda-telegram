import telebot, sqlite3, shelve, os
import config, dop, files
import db
from advertising_system import AdvertisingManager
from bot_instance import bot

advertising = AdvertisingManager(files.main_db)


def show_discount_menu(chat_id):
    """Mostrar menú de configuración de descuentos"""
    config_dis = dop.get_discount_config()

    status = 'Activado ✅' if config_dis['enabled'] else 'Desactivado ❌'
    show_fake = 'Sí' if config_dis['show_fake_price'] else 'No'

    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    toggle = 'Desactivar descuentos' if config_dis['enabled'] else 'Activar descuentos'
    toggle_fake = 'Ocultar precios tachados' if config_dis['show_fake_price'] else 'Mostrar precios tachados'
    user_markup.row(toggle)
    user_markup.row('Cambiar texto', 'Cambiar multiplicador')
    user_markup.row(toggle_fake)
    user_markup.row('Vista previa', 'Volver al menú principal')

    message = (
        f"💸 *Configuración de Descuentos*\n\n"
        f"Estado: {status}\n"
        f"Texto: {config_dis['text']}\n"
        f"Multiplicador: x{config_dis['multiplier']}\n"
        f"Mostrar precios tachados: {show_fake}"
    )

    bot.send_message(chat_id, message, reply_markup=user_markup, parse_mode='Markdown')


def _send_media(chat_id, text, media):
    """Enviar media con caption al chat"""
    mtype = media.get('type')
    fid = media.get('file_id')
    if mtype == 'photo':
        bot.send_photo(chat_id, fid, caption=text)
    elif mtype == 'video':
        bot.send_video(chat_id, fid, caption=text)
    elif mtype == 'document':
        bot.send_document(chat_id, fid, caption=text)
    elif mtype == 'audio':
        bot.send_audio(chat_id, fid, caption=text)
    elif mtype == 'animation':
        bot.send_animation(chat_id, fid, caption=text)
    else:
        bot.send_message(chat_id, text)


def send_broadcast(group, amount, text, media=None):
    """Enviar un boletín a un grupo de usuarios"""
    good_send = 0
    lose_send = 0
    i = 0

    if group == 'all':
        try:
            with open(files.users_list, encoding='utf-8') as f:
                users = f.readlines()

            while i < int(amount) and i < len(users):
                chat_id = int(users[i].strip())
                try:
                    if media:
                        _send_media(chat_id, text, media)
                    else:
                        bot.send_message(chat_id, text)
                    good_send += 1
                except Exception:
                    lose_send += 1
                    dop.new_blockuser(chat_id)
                i += 1
        except Exception:
            pass

    elif group == 'buyers':
        try:
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute("SELECT id FROM buyers LIMIT ?;", (int(amount),))
            buyers = cursor.fetchall()

            for buyer in buyers:
                chat_id = int(buyer[0])
                try:
                    if media:
                        _send_media(chat_id, text, media)
                    else:
                        bot.send_message(chat_id, text)
                    good_send += 1
                except Exception:
                    lose_send += 1
                    dop.new_blockuser(chat_id)
        except Exception:
            pass

    return (
        f'¡{good_send} usuarios recibieron el mensaje exitosamente!\n'
        f'{lose_send} usuarios bloquearon el bot y fueron agregados a la lista de usuarios bloqueados'
    )

def in_adminka(chat_id, message_text, username, name_user):
    if chat_id in dop.get_adminlist():
        normalized = message_text.strip().lower()
        if normalized in ('volver al menú principal', 'volver al menu principal', '/adm'):
            if dop.get_sost(chat_id) is True:
                with shelve.open(files.sost_bd) as bd:
                    del bd[str(chat_id)]
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('💬 Respuestas')
            user_markup.row('📦 Surtido', '➕ Producto')
            user_markup.row('💰 Pagos')
            user_markup.row('📊 Stats', '📣 Difusión')
            user_markup.row('📢 Marketing')
            user_markup.row('💸 Descuentos')
            user_markup.row('⚙️ Otros')
            bot.send_message(chat_id, '¡Has ingresado al panel de administración del bot!\nPara salir, presiona /start', reply_markup=user_markup)

        elif message_text == '💬 Respuestas':
            if dop.check_message('start') is True: 
                start = 'Cambiar'
            else: 
                start = 'Añadir'
            if dop.check_message('after_buy'): 
                after_buy = 'Cambiar'
            else: 
                after_buy = 'Añadir'
            if dop.check_message('help'): 
                help ='Cambiar'
            else: 
                help = 'Añadir'
            if dop.check_message('userfalse'): 
                userfalse = 'Cambiar'
            else: 
                userfalse = 'Añadir'
            user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
            user_markup.row(start + ' bienvenida al usuario')
            user_markup.row(after_buy + ' mensaje después de pagar el producto')
            user_markup.row(help + ' respuesta al comando help', userfalse + ' mensaje si no hay nombre de usuario')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Seleccione qué mensaje desea cambiar.\nDespués de seleccionar, recibirá una breve instrucción', reply_markup=user_markup)

        elif ' bienvenida al usuario' in message_text or ' mensaje después de pagar el producto' in message_text or ' respuesta al comando help' in message_text or ' mensaje si no hay nombre de usuario' in message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            if ' bienvenida al usuario' in message_text: 
                message = 'start'
                bot.send_message(chat_id, '¡Ingrese un nuevo mensaje de bienvenida! En el texto puede usar las palabras `username` y `name`. Se reemplazarán automáticamente por el nombre de usuario', parse_mode='MarkDown', reply_markup=key)
            elif ' mensaje después de pagar el producto' in message_text: 
                message = 'after_buy'
                bot.send_message(chat_id, '¡Ingrese un nuevo mensaje que el bot enviará al usuario después de la compra! En el texto puede usar las palabras `username` y `name`. Se reemplazarán automáticamente por el nombre de usuario', parse_mode='MarkDown', reply_markup=key)
            elif ' respuesta al comando help' in message_text: 
                bot.send_message(chat_id, '¡Ingrese un nuevo mensaje de ayuda! En principio, puede poner cualquier cosa allí. En el texto puede usar las palabras `username` y `name`. Se reemplazarán automáticamente por el nombre de usuario', parse_mode='MarkDown', reply_markup=key)
                message = 'help'
            elif ' mensaje si no hay nombre de usuario' in message_text:
                bot.send_message(chat_id, '¡Ingrese un nuevo mensaje que se enviará si el usuario no tiene `username`! En el texto puede usar `uname`. Se reemplazará automáticamente por el nombre de usuario', parse_mode='MarkDown', reply_markup=key)
                message = 'userfalse'
            with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding ='utf-8') as f: 
                f.write(message)
            with shelve.open(files.sost_bd) as bd : 
                bd[str(chat_id)] = 1

        elif '📦 Surtido' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
            user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
            user_markup.row('📝 Descripción adicional')
            user_markup.row('🎬 Multimedia productos')
            user_markup.row('Volver al menú principal')

            con = db.get_db_connection()
            cursor = con.cursor()
            goodz = 'Productos creados:\n\n'
            a = 0
            cursor.execute("SELECT name, description, format, minimum, price, stored, duration_days FROM goods;")
            for name, description, format, minimum, price, stored, duration in cursor.fetchall():
                a += 1
                amount = dop.amount_of_goods(name)
                dur_line = f"\n*Duración:* {duration} días" if duration not in (None, 0) else ''
                goodz += (
                    '*Nombre:* ' + name + '\n*Descripción:* ' + description +
                    '\n*Formato del producto:* ' + format +
                    '\n*Cantidad mínima para comprar:* ' + str(minimum) +
                    '\n*Precio por unidad:* $' + str(price) + ' USD' +
                    dur_line +
                    '\n*Unidades restantes:* ' + str(amount) + '\n\n'
                )
            if a == 0: 
                goodz = '¡No se han creado posiciones todavía!'
            bot.send_message(chat_id, goodz, reply_markup=user_markup, parse_mode='MarkDown')

        elif 'Añadir nueva posición en el escaparate' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(
                telebot.types.InlineKeyboardButton(
                    text='Omitir', callback_data='SKIP_NEW_MEDIA'
                )
            )
            key.add(
                telebot.types.InlineKeyboardButton(
                    text='Cancelar y volver al menú principal de administración',
                    callback_data='Volver al menú principal de administración'
                )
            )
            bot.send_message(
                chat_id,
                'Envíe una imagen o video para el producto (opcional) o presione "Omitir"',
                reply_markup=key
            )
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 200

        elif 'Eliminar posición' == message_text:
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute("SELECT name FROM goods;")
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            a = 0
            for name in cursor.fetchall():
                a += 1
                user_markup.row(name[0])
            if a == 0: 
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('📝 Descripción adicional')
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!', reply_markup=user_markup)
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿Qué posición desea eliminar?', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 6

        elif 'Cambiar descripción de posición' == message_text:
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute("SELECT name FROM goods;")
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            a = 0
            for name in cursor.fetchall():
                a += 1
                user_markup.row(name[0])
            if a == 0: 
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('📝 Descripción adicional')
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!', reply_markup=user_markup)
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿Para qué posición desea cambiar la descripción?', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 7

        elif 'Cambiar precio' == message_text:
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute("SELECT name FROM goods;")
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            a = 0
            for name in cursor.fetchall():
                a += 1
                user_markup.row(name[0])
            if a == 0: 
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('📝 Descripción adicional')
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!', reply_markup=user_markup)
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿Para qué posición desea cambiar el precio?', parse_mode='Markdown', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 9

        elif '📝 Descripción adicional' == message_text:
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute("SELECT name FROM goods;")
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            a = 0
            for name in cursor.fetchall():
                a += 1
                user_markup.row(name[0])
            if a == 0: 
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('📝 Descripción adicional')
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!', reply_markup=user_markup)
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿Para qué producto desea editar la descripción adicional?', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 28

        elif '🎬 Multimedia productos' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('📤 Agregar o cambiar multimedia', '🗑️ Eliminar multimedia')
            user_markup.row('📋 Ver productos con multimedia')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, '🎬 **Gestión de Multimedia**\n\nSelecciona una opción:', reply_markup=user_markup, parse_mode='Markdown')

        elif '📤 Agregar o cambiar multimedia' == message_text:
            products = dop.get_goods()
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            if not products:
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!', reply_markup=user_markup)
            else:
                products_with_media = {name: mtype for name, mtype in dop.get_products_with_media()}
                emoji_map = {'photo': '📸', 'video': '🎥', 'document': '📄', 'audio': '🎵'}
                for product in products:
                    if product in products_with_media:
                        emoji = emoji_map.get(products_with_media[product], '📎')
                        user_markup.row(f"{emoji} {product}")
                    else:
                        user_markup.row(product)
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '📤 **Agregar o cambiar Multimedia**\n\n¿A qué producto deseas agregar o cambiar multimedia?', reply_markup=user_markup, parse_mode='Markdown')
                with shelve.open(files.sost_bd) as bd:
                    bd[str(chat_id)] = 30

        elif '🗑️ Eliminar multimedia' == message_text:
            products_with_media = dop.get_products_with_media()
            if not products_with_media:
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, 'ℹ️ No hay productos con multimedia asignada', reply_markup=user_markup)
            else:
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                for product, media_type in products_with_media:
                    media_emoji = {'photo': '📸', 'video': '🎥', 'document': '📄', 'audio': '🎵'}.get(media_type, '📎')
                    user_markup.row(f"{media_emoji} {product}")
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '🗑️ **Eliminar Multimedia**\n\n¿De qué producto deseas eliminar multimedia?', reply_markup=user_markup, parse_mode='Markdown')
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 31

        elif '📋 Ver productos con multimedia' == message_text:
            products_with_media = dop.get_products_with_media()
            menu_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            menu_markup.row('🎬 Multimedia productos')
            menu_markup.row('Volver al menú principal')

            if not products_with_media:
                bot.send_message(
                    chat_id,
                    'ℹ️ No hay productos con multimedia asignada',
                    reply_markup=menu_markup,
                )
            else:
                for product_name, media_type in products_with_media:
                    media_info = dop.get_product_media(product_name)
                    caption = dop.format_product_with_media(product_name)
                    if media_info:
                        mtype = media_info['type']
                        file_id = media_info['file_id']
                        if mtype == 'photo':
                            bot.send_photo(chat_id, file_id, caption=caption, parse_mode='Markdown')
                        elif mtype == 'video':
                            bot.send_video(chat_id, file_id, caption=caption, parse_mode='Markdown')
                        elif mtype == 'document':
                            bot.send_document(chat_id, file_id, caption=caption, parse_mode='Markdown')
                        elif mtype == 'audio':
                            bot.send_audio(chat_id, file_id, caption=caption, parse_mode='Markdown')
                        elif mtype == 'animation':
                            bot.send_animation(chat_id, file_id, caption=caption, parse_mode='Markdown')
                        else:
                            bot.send_message(chat_id, caption, parse_mode='Markdown')
                    else:
                        bot.send_message(chat_id, caption or product_name, parse_mode='Markdown')

                bot.send_message(
                    chat_id,
                    '📋 Fin de la lista de productos con multimedia',
                    reply_markup=menu_markup,
                )


        elif '➕ Producto' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(
                telebot.types.InlineKeyboardButton(
                    text='Cancelar y volver al menú principal de administración',
                    callback_data='Volver al menú principal de administración'))
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute("SELECT name, price FROM goods;")
            a = 0
            user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
            for name, price in cursor.fetchall():
                a += 1
                user_markup.row(name)
            user_markup.row('Volver al menú principal')
            if a == 0:
                bot.send_message(
                    chat_id,
                    '¡No se ha creado ninguna posición todavía!',
                    reply_markup=user_markup)
            else:
                bot.send_message(
                    chat_id,
                    '¿De qué posición desea cargar productos?',
                    reply_markup=user_markup,
                    parse_mode='MarkDown')
                with shelve.open(files.sost_bd) as bd:
                    bd[str(chat_id)] = 10

        elif '💰 Pagos' == message_text:
            with shelve.open(files.payments_bd) as bd:
                paypal = bd.get('paypal', '❌')
                binance = bd.get('binance', '❌')
            
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row(f'PayPal {paypal}', f'Binance {binance}')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Configuración de métodos de pago:', reply_markup=user_markup)

        elif 'PayPal' in message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese el Client ID de PayPal:', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 18

        elif 'Binance' in message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese la API Key de Binance:', reply_markup=key)
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 19

        elif '📊 Stats' == message_text:
            result = dop.get_daily_sales()
            bot.send_message(chat_id, result, parse_mode='Markdown')

        elif '📣 Difusión' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('A todos los usuarios', 'Solo a compradores')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Seleccione a qué grupo de usuarios desea enviar el boletín', reply_markup=user_markup)

        elif '📢 Marketing' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('🎯 Nueva campaña', '📋 Ver campañas')
            user_markup.row('⏰ Programar envíos', '🎯 Gestionar grupos')
            user_markup.row('📊 Estadísticas hoy', '⚙️ Configuración')
            user_markup.row('▶️ Envío manual', 'Volver al menú principal')

            today_stats = advertising.get_today_stats()
            stats_text = f"""📢 **Sistema de Marketing**\n\n📊 **Estadísticas de hoy:**\n- Mensajes enviados: {today_stats['sent']}\n- Tasa de éxito: {today_stats['success_rate']}%\n- Grupos alcanzados: {today_stats['groups']}\n\nSelecciona una opción:"""

            bot.send_message(chat_id, stats_text, reply_markup=user_markup, parse_mode='Markdown')

        elif '🎯 Nueva campaña' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '📝 *Nombre de la campaña*\n\nEnvía el nombre para la nueva campaña:', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 160

        elif '📋 Ver campañas' == message_text:
            campaigns = advertising.get_all_campaigns()
            if campaigns:
                response = '📋 *Campañas registradas:*\n'
                for c in campaigns:
                    response += f"- {c['id']}. {c['name']} ({c['status']})\n"
            else:
                response = 'ℹ️ No hay campañas registradas.'
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('📢 Marketing')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, response, parse_mode='Markdown', reply_markup=user_markup)

        elif message_text.startswith('⏰ Programar envíos'):
            params = message_text.replace('⏰ Programar envíos', '').strip()
            if not params:
                bot.send_message(chat_id, 'Uso: ⏰ Programar envíos <ID> <HH:MM>')
            else:
                parts = params.split()
                if len(parts) < 2:
                    bot.send_message(chat_id, 'Uso: ⏰ Programar envíos <ID> <HH:MM>')
                else:
                    try:
                        camp_id = int(parts[0])
                        time_str = parts[1]
                        ok, msg = advertising.schedule_campaign(camp_id, time_str)
                        bot.send_message(chat_id, ('✅ ' if ok else '❌ ') + msg)
                    except ValueError:
                        bot.send_message(chat_id, '❌ ID de campaña inválido')

        elif '🎯 Gestionar grupos' == message_text:
            msg = (
                '🎯 *Gestionar grupos*\n\n'
                'Selecciona una acción o envía /cancel para regresar.'
            )
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('➕ Agregar grupo', '➖ Eliminar grupo')
            user_markup.row('📋 Listar grupos')
            user_markup.row('📢 Marketing')
            bot.send_message(chat_id, msg, reply_markup=user_markup, parse_mode='Markdown')

        elif message_text == '➕ Agregar grupo':
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('telegram', 'whatsapp')
            user_markup.row('Cancelar')
            bot.send_message(chat_id, '¿Para qué plataforma es el grupo?', reply_markup=user_markup)
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 170

        elif message_text == '➖ Eliminar grupo':
            bot.send_message(chat_id, 'Envía el ID del grupo a eliminar:')
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 172

        elif message_text == '📋 Listar grupos':
            conn = db.get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT platform, group_id, group_name FROM target_groups")
            rows = cur.fetchall()
            if rows:
                txt = '🎯 *Grupos registrados:*\n'
                for r in rows:
                    name = r[2] or ''
                    txt += f"- {r[0]} {r[1]} {name}\n"
            else:
                txt = 'No hay grupos registrados.'
            bot.send_message(chat_id, txt, parse_mode='Markdown')


        elif '📊 Estadísticas hoy' == message_text:
            stats = advertising.get_today_stats()
            msg = (
                f"📊 *Estadísticas de hoy*\n\n"
                f"Mensajes enviados: {stats['sent']}\n"
                f"Tasa de éxito: {stats['success_rate']}%\n"
                f"Grupos alcanzados: {stats['groups']}"
            )
            bot.send_message(chat_id, msg, parse_mode='Markdown')

        elif '⚙️ Configuración' == message_text:
            configs = {c['platform']: c for c in advertising.get_platform_configs()}
            tel_status = 'Activo ✅' if configs.get('telegram', {}).get('is_active', True) else 'Inactivo ❌'
            wa_status = 'Activo ✅' if configs.get('whatsapp', {}).get('is_active', True) else 'Inactivo ❌'
            msg_cfg = (
                '⚙️ *Configuración de plataformas*\n\n'
                f'Telegram: {tel_status}\n'
                f'WhatsApp: {wa_status}'
            )
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Toggle telegram', 'Toggle whatsapp')
            user_markup.row('Editar telegram', 'Editar whatsapp')
            user_markup.row('📢 Marketing')
            bot.send_message(chat_id, msg_cfg, reply_markup=user_markup, parse_mode='Markdown')

        elif message_text == 'Toggle telegram':
            cfg = {c['platform']: c for c in advertising.get_platform_configs()}
            current = cfg.get('telegram', {}).get('is_active', True)
            advertising.update_platform_config('telegram', is_active=not current)
            bot.send_message(chat_id, '✅ Estado de Telegram actualizado')
            in_adminka(chat_id, '⚙️ Configuración', username, name_user)

        elif message_text == 'Toggle whatsapp':
            cfg = {c['platform']: c for c in advertising.get_platform_configs()}
            current = cfg.get('whatsapp', {}).get('is_active', True)
            advertising.update_platform_config('whatsapp', is_active=not current)
            bot.send_message(chat_id, '✅ Estado de WhatsApp actualizado')
            in_adminka(chat_id, '⚙️ Configuración', username, name_user)

        elif message_text == 'Editar telegram':
            bot.send_message(chat_id, 'Envíe la nueva configuración (texto o JSON) para Telegram:')
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 175

        elif message_text == 'Editar whatsapp':
            bot.send_message(chat_id, 'Envíe la nueva configuración (texto o JSON) para WhatsApp:')
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 176

        elif message_text.startswith('▶️ Envío manual'):
            params = message_text.replace('▶️ Envío manual', '').strip()
            if not params:
                bot.send_message(chat_id, 'Uso: ▶️ Envío manual <ID>')
            else:
                try:
                    camp_id = int(params.split()[0])
                    ok, msg = advertising.send_campaign_now(camp_id)
                    bot.send_message(chat_id, ('✅ ' if ok else '❌ ') + msg)
                except ValueError:
                    bot.send_message(chat_id, '❌ ID de campaña inválido')


        elif 'Vista previa' == message_text:
            preview = f"🛍️ **CATÁLOGO PREVIEW**\n{'-'*30}\n\n{dop.get_productcatalog()}"
            bot.send_message(chat_id, preview, parse_mode='Markdown')

        elif normalized in ('a todos los usuarios', 'solo a los compradores', 'solo a compradores'):
            if normalized == 'a todos los usuarios':
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:
                    f.write('all\n')
                amount = dop.user_loger()
            elif normalized in ('solo a los compradores', 'solo a compradores'):
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:
                    f.write('buyers\n')
                amount = dop.get_amountsbayers()
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '¿A cuántos usuarios desea enviar el boletín? Ingrese un número. Máximo posible ' + str(amount))
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 40

        elif '⚙️ Otros' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            user_markup.row('Añadir nuevo admin', 'Eliminar admin')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Seleccione qué desea hacer', reply_markup=user_markup)

        elif 'Añadir nuevo admin' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text = 'Cancelar y volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese la ID del nuevo admin')
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 21

        elif 'Eliminar admin' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            a = 0
            for admin_id in dop.get_adminlist(): 
                a += 1
                if int(admin_id) != config.admin_id: 
                    user_markup.row(str(admin_id))
            if a == 1: 
                bot.send_message(chat_id, '¡Todavía no ha añadido admins!')
            else: 
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, 'Seleccione qué admin desea eliminar', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 22

def text_analytics(message_text, chat_id):
    normalized = message_text.strip().lower()
    if normalized in ('volver al men\u00fa principal', 'volver al menu principal', '/adm'):
        with shelve.open(files.sost_bd) as bd:
            if str(chat_id) in bd:
                del bd[str(chat_id)]
        in_adminka(chat_id, 'Volver al men\u00fa principal', None, None)
        return

    if dop.get_sost(chat_id) is True:
        with shelve.open(files.sost_bd) as bd: 
            sost_num = bd[str(chat_id)]
        
        if sost_num == 1:
            try:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f:
                    message = f.read()
            except FileNotFoundError:
                bot.send_message(chat_id, '❌ La sesión anterior se perdió.')
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
                in_adminka(chat_id, 'Volver al menú principal', None, None)
                return
            try:
                with shelve.open(files.bot_message_bd) as bd:
                    bd[message] = message_text
                success = True
            except:
                success = False
            if success:
                user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
                user_markup.row('💬 Respuestas')
                user_markup.row('📦 Surtido', '➕ Producto')
                user_markup.row('💰 Pagos')
                user_markup.row('📊 Stats', '📣 Difusión')
                user_markup.row('💸 Descuentos')
                user_markup.row('⚙️ Otros')
                bot.send_message(chat_id, 'Mensaje guardado exitosamente!', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    del bd[str(chat_id)]
            else:
                bot.send_message(chat_id, 'Error guardando mensaje')

        elif sost_num == 2:
            with open('data/Temp/' + str(chat_id) + 'good_name.txt', 'w', encoding='utf-8') as f: 
                f.write(message_text)
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ahora ingrese la descripción', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 3

        elif sost_num == 3:
            with open('data/Temp/' + str(chat_id) + 'good_description.txt', 'w', encoding='utf-8') as f: 
                f.write(message_text)
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('En formato de texto', 'En formato de archivo')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Ahora seleccione el formato del producto', reply_markup=user_markup)
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 4

        elif sost_num == 4:
            format_map = {
                'En formato de texto': 'text',
                'En formato de archivo': 'file'
            }
            format_value = format_map.get(message_text, message_text)
            with open('data/Temp/' + str(chat_id) + 'good_format.txt', 'w', encoding='utf-8') as f:
                f.write(format_value)
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ahora ingrese la cantidad mínima para comprar', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 5

        elif sost_num == 5:
            with open('data/Temp/' + str(chat_id) + 'good_minimum.txt', 'w', encoding='utf-8') as f: 
                f.write(message_text)
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ahora ingrese el precio por unidad en USD', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 15

        elif sost_num == 15:
            with open('data/Temp/' + str(chat_id) + 'good_price.txt', 'w', encoding='utf-8') as f:
                f.write(message_text)

            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(
                text='Cancelar y volver al menú principal de administración',
                callback_data='Volver al menú principal de administración'
            ))

            bot.send_message(
                chat_id,
                'Ingrese la duración en días del producto (0 para indefinido):',
                reply_markup=key
            )
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 16

        elif sost_num == 16:
            with open('data/Temp/' + str(chat_id) + 'good_duration.txt', 'w', encoding='utf-8') as f:
                f.write(message_text)

            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Añadir producto a la tienda', callback_data='Añadir producto a la tienda'))
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))

            with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f:
                name = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_description.txt', encoding='utf-8') as f:
                description = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_format.txt', encoding='utf-8') as f:
                format_type = f.read()
            format_display = 'Texto' if format_type == 'text' else 'Archivo'
            with open('data/Temp/' + str(chat_id) + 'good_minimum.txt', encoding='utf-8') as f:
                minimum = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_price.txt', encoding='utf-8') as f:
                price = f.read()
            duration_display = ''
            try:
                duration_int = int(message_text)
                if duration_int > 0:
                    duration_display = f'\n*Duración:* {duration_int} días'
            except ValueError:
                pass

            summary = (
                f'*Resumen del producto:*\n\n*Nombre:* {name}\n*Descripción:* {description}'
                f'\n*Formato:* {format_display}\n*Cantidad mínima:* {minimum}\n*Precio:* ${price} USD{duration_display}'
            )

            media_temp = 'data/Temp/' + str(chat_id) + 'new_media.txt'
            if os.path.exists(media_temp):
                with open(media_temp, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                    if len(lines) >= 2:
                        file_id = lines[0]
                        mtype = lines[1]
                        caption = summary
                        if mtype == 'photo':
                            bot.send_photo(chat_id, file_id, caption=caption, reply_markup=key, parse_mode='Markdown')
                        elif mtype == 'video':
                            bot.send_video(chat_id, file_id, caption=caption, reply_markup=key, parse_mode='Markdown')
                        else:
                            bot.send_message(chat_id, summary, parse_mode='MarkDown', reply_markup=key)
                    else:
                        bot.send_message(chat_id, summary, parse_mode='MarkDown', reply_markup=key)
            else:
                bot.send_message(chat_id, summary, parse_mode='MarkDown', reply_markup=key)
            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]

        elif sost_num == 6:
            con = db.get_db_connection()
            cursor = con.cursor()
            a = 0
            cursor.execute("SELECT description FROM goods WHERE name = ?", (message_text,))
            for i in cursor.fetchall():
                a += 1
            if a == 0:
                bot.send_message(chat_id, '¡La posición seleccionada no se encontró! Selecciónela haciendo clic en el botón correspondiente.')
            else:
                cursor.execute("DELETE FROM goods WHERE name = ?", (message_text,))
                con.commit()
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('📝 Descripción adicional')
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡Posición eliminada con éxito!', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    del bd[str(chat_id)]

        elif sost_num == 7:
            con = db.get_db_connection()
            cursor = con.cursor()
            a = 0
            cursor.execute("SELECT description FROM goods WHERE name = ?", (message_text,))
            for i in cursor.fetchall(): 
                a += 1

            if a == 0: 
                bot.send_message(chat_id, '¡No hay una posición con ese nombre!\n¡Seleccione de nuevo!')
            else:
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: 
                    f.write(message_text)
                bot.send_message(chat_id, 'Ahora escriba la nueva descripción', reply_markup=key)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 8

        elif sost_num == 8:
            try:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f:
                    name_good = f.read()
            except FileNotFoundError:
                bot.send_message(chat_id, '❌ La sesión anterior se perdió.')
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
                in_adminka(chat_id, 'Volver al menú principal', None, None)
                return
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute("UPDATE goods SET description = ? WHERE name = ?", (message_text, name_good))
            con.commit()
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
            user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
            user_markup.row('📝 Descripción adicional')
            user_markup.row('🎬 Multimedia productos')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, '¡Descripción cambiada con éxito!', reply_markup=user_markup)
            with shelve.open(files.sost_bd) as bd: 
                del bd[str(chat_id)]

        elif sost_num == 9:
            try:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f:
                    name_good = f.read()
            except FileNotFoundError:
                bot.send_message(chat_id, '❌ La sesión anterior se perdió.')
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
                in_adminka(chat_id, 'Volver al menú principal', None, None)
                return
            try:
                price = int(message_text)
                con = db.get_db_connection()
                cursor = con.cursor()
                cursor.execute("UPDATE goods SET price = ? WHERE name = ?", (price, name_good))
                con.commit()
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('📝 Descripción adicional')
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡Precio cambiado con éxito!', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    del bd[str(chat_id)]
            except:
                bot.send_message(chat_id, 'Error: ingrese un número válido')

        elif sost_num == 10:
            file_path = 'data/goods/' + message_text + '.txt'
            if not os.path.exists(file_path):
                open(file_path, 'w', encoding='utf-8').close()

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                if lines:
                    enumerated = "\n".join(
                        f"{idx+1}. {line}" for idx, line in enumerate(lines)
                    )
                else:
                    enumerated = 'Sin unidades cargadas'

            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(
                text='Cancelar y volver al menú principal de administración',
                callback_data='Volver al menú principal de administración'))
            bot.send_message(
                chat_id,
                f'Unidades actuales de {message_text}:\n\n{enumerated}\n\nEnvíe el nuevo contenido (cada línea será un producto):')

            with open(
                'data/Temp/' + str(chat_id) + 'upload_file.txt',
                'w',
                encoding='utf-8') as f:
                f.write(message_text)

            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 11

        elif sost_num == 11:
            with open('data/Temp/' + str(chat_id) + 'upload_file.txt', encoding='utf-8') as f: 
                file_name = f.read()
            file_path = 'data/goods/' + file_name + '.txt'
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(message_text)
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('📝 Descripción adicional')
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡Productos cargados con éxito!', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    del bd[str(chat_id)]
            except Exception as e:
                bot.send_message(chat_id, f'Error cargando productos: {e}')

        elif sost_num == 18:
            # PayPal Client ID
            with open('data/Temp/' + str(chat_id) + 'paypal_client.txt', 'w', encoding='utf-8') as f: 
                f.write(message_text)
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ahora ingrese el Client Secret de PayPal:', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 25

        elif sost_num == 25:
            # PayPal Client Secret
            try:
                with open('data/Temp/' + str(chat_id) + 'paypal_client.txt', encoding='utf-8') as f: 
                    client_id = f.read()
                
                con = db.get_db_connection()
                cursor = con.cursor()
                cursor.execute("INSERT OR REPLACE INTO paypal_data VALUES(?, ?, ?)", (client_id, message_text, 1))
                con.commit()
                
                with shelve.open(files.payments_bd) as bd:
                    bd['paypal'] = '✅'
                
                bot.send_message(chat_id, '¡Credenciales PayPal guardadas exitosamente!')
                with shelve.open(files.sost_bd) as bd: 
                    del bd[str(chat_id)]
            except Exception as e:
                bot.send_message(chat_id, f'Error guardando credenciales: {e}')

        elif sost_num == 19:
            # Binance API Key
            with open('data/Temp/' + str(chat_id) + 'binance_api.txt', 'w', encoding='utf-8') as f: 
                f.write(message_text)
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ahora ingrese el API Secret de Binance:', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 26

        elif sost_num == 26:
            # Binance API Secret
            with open('data/Temp/' + str(chat_id) + 'binance_api.txt', encoding='utf-8') as f: 
                api_key = f.read()
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Finalmente, ingrese el Merchant ID de Binance:', reply_markup=key)
            with open('data/Temp/' + str(chat_id) + 'binance_secret.txt', 'w', encoding='utf-8') as f: 
                f.write(message_text)
            with open('data/Temp/' + str(chat_id) + 'binance_api_temp.txt', 'w', encoding='utf-8') as f: 
                f.write(api_key)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 27

        elif sost_num == 27:
            # Binance Merchant ID
            try:
                with open('data/Temp/' + str(chat_id) + 'binance_api_temp.txt', encoding='utf-8') as f: 
                    api_key = f.read()
                with open('data/Temp/' + str(chat_id) + 'binance_secret.txt', encoding='utf-8') as f: 
                    api_secret = f.read()
                
                con = db.get_db_connection()
                cursor = con.cursor()
                cursor.execute("INSERT OR REPLACE INTO binance_data VALUES(?, ?, ?)", (api_key, api_secret, message_text))
                con.commit()
                
                with shelve.open(files.payments_bd) as bd:
                    bd['binance'] = '✅'
                
                bot.send_message(chat_id, '¡Credenciales Binance guardadas exitosamente!')
                with shelve.open(files.sost_bd) as bd: 
                    del bd[str(chat_id)]
            except Exception as e:
                bot.send_message(chat_id, f'Error guardando credenciales: {e}')

        elif sost_num == 21:
            dop.new_admin(message_text)
            user_markup = telebot.types.ReplyKeyboardMarkup(True, True) 
            user_markup.row('Añadir nuevo admin', 'Eliminar admin')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Nuevo admin añadido con éxito', reply_markup=user_markup)
            with shelve.open(files.sost_bd) as bd: 
                del bd[str(chat_id)]

        elif sost_num == 22:
            with open(files.admins_list, encoding='utf-8') as f:
                if str(message_text) in f.read():
                    dop.del_id(files.admins_list, message_text)
                    bot.send_message(chat_id, 'Admin eliminado con éxito de la lista')
                    with shelve.open(files.sost_bd) as bd: 
                        del bd[str(chat_id)]
                else: 
                    bot.send_message(chat_id, '¡La ID no se encontró en la lista de administradores! Seleccione la ID correcta.')
                    with shelve.open(files.sost_bd) as bd : 
                        bd[str(chat_id)] = 22

        elif sost_num == 28:  # Seleccionar producto para editar descripción adicional
            con = db.get_db_connection()
            cursor = con.cursor()
            a = 0
            cursor.execute("SELECT name FROM goods WHERE name = ?", (message_text,))
            for i in cursor.fetchall():
                a += 1
            if a == 0:
                bot.send_message(chat_id, '¡La posición seleccionada no se encontró! Selecciónela haciendo clic en el botón correspondiente.')
            else:
                # Mostrar descripción adicional actual
                cursor.execute("SELECT additional_description FROM goods WHERE name = ?", (message_text,))
                current_desc = cursor.fetchone()
                current_additional = current_desc[0] if current_desc and current_desc[0] else "Sin descripción adicional"

                with open('data/Temp/' + str(chat_id) + 'edit_additional_desc.txt', 'w', encoding='utf-8') as f:
                    f.write(message_text)

                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))

                bot.send_message(chat_id,
                                 f'📝 **Editar descripción adicional para:** {message_text}\n\n'
                                 f'**Descripción adicional actual:**\n{current_additional}\n\n'
                                 f'**Ingrese la nueva descripción adicional** (o escriba "ELIMINAR" para quitar la descripción adicional):',
                                 reply_markup=key, parse_mode='Markdown')

                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 29

        elif sost_num == 29:  # Recibir nueva descripción adicional
            try:
                with open('data/Temp/' + str(chat_id) + 'edit_additional_desc.txt', encoding='utf-8') as f:
                    product_name = f.read()

                if message_text.upper() == "ELIMINAR":
                    new_additional_desc = ""
                    success_message = "La descripción adicional ha sido eliminada."
                else:
                    new_additional_desc = message_text
                    success_message = "La descripción adicional ha sido actualizada."

                if dop.set_additional_description(product_name, new_additional_desc):
                    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                    user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                    user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                    user_markup.row('📝 Descripción adicional')
                    user_markup.row('🎬 Multimedia productos')
                    user_markup.row('Volver al menú principal')

                    bot.send_message(chat_id, f'✅ {success_message}\n\nProducto: {product_name}', reply_markup=user_markup)
                    with shelve.open(files.sost_bd) as bd: 
                        del bd[str(chat_id)]
                else:
                    bot.send_message(chat_id, '❌ Error al actualizar la descripción adicional. Inténtelo de nuevo.')
            except Exception as e:
                print(f"Error en estado 29: {e}")
                bot.send_message(chat_id, '❌ Error procesando la descripción adicional. Inténtelo de nuevo.')

        elif sost_num == 30:  # Seleccionar producto para agregar multimedia
            clean_name = message_text
            for emoji in ['📸 ', '🎥 ', '📄 ', '🎵 ', '📎 ']:
                clean_name = clean_name.replace(emoji, '')

            if clean_name in dop.get_goods():
                with open('data/Temp/' + str(chat_id) + 'media_product.txt', 'w', encoding='utf-8') as f:
                    f.write(clean_name)
                
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
                
                bot.send_message(chat_id,
                                f'📤 **Agregar o cambiar multimedia a:** {clean_name}\n\n'
                                f'Envía el archivo multimedia (foto, video, documento, audio, GIF)\n'
                                f'💡 Tip: Puedes añadir un texto descriptivo junto al archivo',
                                reply_markup=key, parse_mode='Markdown')
                
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 32
            else:
                bot.send_message(chat_id, '❌ Producto no válido')

        elif sost_num == 31:  # Seleccionar producto para eliminar multimedia
            clean_name = message_text
            for emoji in ['📸 ', '🎥 ', '📄 ', '🎵 ', '📎 ']:
                clean_name = clean_name.replace(emoji, '')
            
            if dop.has_product_media(clean_name):
                if dop.remove_product_media(clean_name):
                    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                    user_markup.row('🎬 Multimedia productos')
                    user_markup.row('Volver al menú principal')
                    bot.send_message(chat_id, f'✅ Multimedia eliminada del producto: {clean_name}', reply_markup=user_markup)
                else:
                    bot.send_message(chat_id, '❌ Error eliminando multimedia')
            else:
                bot.send_message(chat_id, '❌ El producto no tiene multimedia asignada')
            
            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]

        elif sost_num == 33:  # Recibir nuevo texto de descuento
            if dop.update_discount_config(text=message_text):
                bot.send_message(chat_id, '✅ Texto de descuento actualizado')
            else:
                bot.send_message(chat_id, '❌ Error actualizando texto')

            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]
            show_discount_menu(chat_id)

        elif sost_num == 40:  # Cantidad de destinatarios
            try:
                amount = int(message_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                bot.send_message(chat_id, '❌ Por favor ingrese un número válido.')
                return

            with open('data/Temp/' + str(chat_id) + '.txt', 'a', encoding='utf-8') as f:
                f.write(str(amount) + '\n')

            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese el texto del anuncio', reply_markup=key)
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 41

        elif sost_num == 41:  # Texto del anuncio
            with open('data/Temp/' + str(chat_id) + '.txt', 'a', encoding='utf-8') as f:
                f.write(message_text + '\n')

            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Si desea añadir un archivo multimedia envíelo ahora o escriba "no"', reply_markup=key)
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 42

        elif sost_num == 42:  # Archivo multimedia opcional
            try:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                group = lines[0]
                amount = int(lines[1])
                text = lines[2]
            except Exception:
                bot.send_message(chat_id, '❌ La sesión anterior se perdió.')
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
                in_adminka(chat_id, 'Volver al menú principal', None, None)
                return

            media = None
            if message_text.lower() in ('no', 'skip', 'sin archivo'):
                pass
            else:
                media = None
            result = dop.broadcast_message(group, amount, text, media)
            bot.send_message(chat_id, result)
            try:
                os.remove('data/Temp/' + str(chat_id) + '.txt')
            except Exception:
                pass
            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]










        elif sost_num == 34:  # Recibir nuevo multiplicador
            try:
                multiplier = float(message_text)
                if dop.update_discount_config(multiplier=multiplier):
                    bot.send_message(chat_id, f'✅ Multiplicador actualizado a {multiplier}')
                else:
                    bot.send_message(chat_id, '❌ Error actualizando multiplicador')
            except ValueError:
                bot.send_message(chat_id, '❌ Valor inválido, use punto decimal. Ej: 1.5')

            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]
            show_discount_menu(chat_id)


        elif sost_num == 160:  # Nombre de campaña
            with open('data/Temp/' + str(chat_id) + 'campaign_name.txt', 'w', encoding='utf-8') as f:
                f.write(message_text)
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '📝 **Mensaje de la campaña**\n\nEscribe el texto que se enviará (máximo 500 caracteres):', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 161

        elif sost_num == 161:  # Mensaje de campaña
            if len(message_text) > 500:
                bot.send_message(chat_id, '❌ El mensaje es muy largo. Máximo 500 caracteres.')
                return

            with open('data/Temp/' + str(chat_id) + 'campaign_message.txt', 'w', encoding='utf-8') as f:
                f.write(message_text)

            bot.send_message(chat_id, 'Si deseas agregar un botón escribe:\n<texto> <url>\nEscribe "no" para continuar sin botones:')
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 162

        elif sost_num == 162:  # Crear campaña
            button1_text = None
            button1_url = None
            if message_text.lower() not in ('no', 'sin botones'):
                parts = message_text.split()
                if len(parts) >= 2:
                    button1_text = parts[0]
                    button1_url = parts[1]

            with open('data/Temp/' + str(chat_id) + 'campaign_name.txt', encoding='utf-8') as f:
                name = f.read()
            with open('data/Temp/' + str(chat_id) + 'campaign_message.txt', encoding='utf-8') as f:
                text = f.read()

            data = {
                'name': name,
                'message_text': text,
                'button1_text': button1_text,
                'button1_url': button1_url,
                'created_by': chat_id,
            }
            camp_id = advertising.create_campaign(data)
            bot.send_message(chat_id, f'✅ Campaña creada con ID {camp_id}')
            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]

        elif sost_num == 170:  # Plataforma para nuevo grupo
            platform = message_text.lower()
            if platform in ('telegram', 'whatsapp'):
                with open('data/Temp/' + str(chat_id) + 'group_platform.txt', 'w', encoding='utf-8') as f:
                    f.write(platform)
                bot.send_message(chat_id, 'Envíe el ID del grupo:')
                with shelve.open(files.sost_bd) as bd:
                    bd[str(chat_id)] = 171
            else:
                bot.send_message(chat_id, 'Plataforma inválida. Use telegram o whatsapp.')

        elif sost_num == 171:  # ID del grupo
            with open('data/Temp/' + str(chat_id) + 'group_platform.txt', encoding='utf-8') as f:
                platform = f.read()
            with open('data/Temp/' + str(chat_id) + 'group_id.txt', 'w', encoding='utf-8') as f:
                f.write(message_text.strip())
            bot.send_message(chat_id, 'Envíe un nombre opcional para el grupo o escriba "no":')
            with shelve.open(files.sost_bd) as bd:
                bd[str(chat_id)] = 173

        elif sost_num == 173:  # Nombre opcional del grupo y creación
            with open('data/Temp/' + str(chat_id) + 'group_platform.txt', encoding='utf-8') as f:
                platform = f.read()
            with open('data/Temp/' + str(chat_id) + 'group_id.txt', encoding='utf-8') as f:
                gid = f.read()
            name = None if message_text.lower() == 'no' else message_text
            ok, msg = advertising.add_target_group(platform, gid, name)
            bot.send_message(chat_id, ('✅ ' if ok else '❌ ') + msg)
            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]

        elif sost_num == 172:  # Eliminar grupo
            gid = message_text.strip()
            ok, msg = advertising.remove_target_group(gid)
            bot.send_message(chat_id, ('✅ ' if ok else '❌ ') + msg)
            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]

        elif sost_num == 175:  # Editar config telegram
            advertising.update_platform_config('telegram', config_data=message_text)
            bot.send_message(chat_id, '✅ Configuración de Telegram actualizada')
            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]

        elif sost_num == 176:  # Editar config whatsapp
            advertising.update_platform_config('whatsapp', config_data=message_text)
            bot.send_message(chat_id, '✅ Configuración de WhatsApp actualizada')
            with shelve.open(files.sost_bd) as bd:
                del bd[str(chat_id)]

def ad_inline(callback_data, chat_id, message_id):
    if 'Volver al menú principal de administración' == callback_data:
        if dop.get_sost(chat_id) is True:
            with shelve.open(files.sost_bd) as bd: 
                del bd[str(chat_id)]
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('💬 Respuestas')
        user_markup.row('📦 Surtido', '➕ Producto')
        user_markup.row('💰 Pagos')
        user_markup.row('📊 Stats', '📣 Difusión')
        user_markup.row('💸 Descuentos')
        user_markup.row('⚙️ Otros')
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, '¡Has ingresado al panel de administración del bot!\nPara salir, presiona /start', reply_markup=user_markup)

    elif callback_data == 'SKIP_NEW_MEDIA':
        key = telebot.types.InlineKeyboardMarkup()
        key.add(
            telebot.types.InlineKeyboardButton(
                text='Cancelar y volver al menú principal de administración',
                callback_data='Volver al menú principal de administración'
            )
        )
        bot.edit_message_reply_markup(chat_id, message_id)
        bot.send_message(chat_id, 'Ingrese el nombre del nuevo producto', reply_markup=key)
        with shelve.open(files.sost_bd) as bd:
            bd[str(chat_id)] = 2

    elif callback_data == 'CONFIRM_BROADCAST':
        try:
            with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f:
                lines = f.read().splitlines()
            group = lines[0]
            amount = int(lines[1])
            text = lines[2]
        except Exception:
            bot.send_message(chat_id, '❌ La sesión anterior se perdió.')
            return

        media = None
        media_path = f'data/Temp/{chat_id}_broadcast_media.txt'
        if os.path.exists(media_path):
            with open(media_path, 'r', encoding='utf-8') as f:
                mlines = f.read().splitlines()
                if len(mlines) >= 2:
                    fid = mlines[0]
                    mtype = mlines[1]
                    cap = mlines[2] if len(mlines) > 2 else None
                    media = {'file_id': fid, 'type': mtype, 'caption': cap}

        result = dop.broadcast_message(group, amount, text, media)
        bot.edit_message_reply_markup(chat_id, message_id)
        bot.send_message(chat_id, result)
        try:
            os.remove('data/Temp/' + str(chat_id) + '.txt')
            if os.path.exists(media_path):
                os.remove(media_path)
        except Exception:
            pass

    elif callback_data == 'Añadir producto a la tienda':
        try:
            with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f:
                name = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_description.txt', encoding='utf-8') as f:
                description = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_format.txt', encoding='utf-8') as f:
                format_type = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_minimum.txt', encoding='utf-8') as f:
                minimum = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_price.txt', encoding='utf-8') as f:
                price = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_duration.txt', encoding='utf-8') as f:
                duration_days = f.read()
        except FileNotFoundError:
            bot.send_message(chat_id, '❌ La sesión expiró. Vuelva a intentarlo.')
            with shelve.open(files.sost_bd) as bd:
                if str(chat_id) in bd:
                    del bd[str(chat_id)]

            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('💬 Respuestas')
            user_markup.row('📦 Surtido', '➕ Producto')
            user_markup.row('💰 Pagos')
            user_markup.row('📊 Stats', '📣 Difusión')
            user_markup.row('💸 Descuentos')
            user_markup.row('⚙️ Otros')
            bot.delete_message(chat_id, message_id)
            bot.send_message(
                chat_id,
                '¡Has ingresado al panel de administración del bot!\nPara salir, presiona /start',
                reply_markup=user_markup,
            )
            return

        con = db.get_db_connection()
        cursor = con.cursor()
        media_temp = 'data/Temp/' + str(chat_id) + 'new_media.txt'
        media_id = None
        media_type = None
        media_caption = None
        if os.path.exists(media_temp):
            with open(media_temp, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                if len(lines) >= 2:
                    media_id = lines[0]
                    media_type = lines[1]
                    media_caption = lines[2] if len(lines) > 2 else None

        cursor.execute(
            """
            INSERT INTO goods (name, description, format, minimum, price, stored, additional_description, media_file_id, media_type, media_caption, duration_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                format_type,
                minimum,
                price,
                'data/goods/' + name + '.txt',
                '',
                media_id,
                media_type,
                media_caption,
                duration_days,
            ),
        )
        con.commit()
        goods_file = f"data/goods/{name}.txt"
        open(goods_file, "a", encoding="utf-8").close()
        # Mostrar información del producto con la multimedia que se haya adjuntado
        media_info = dop.get_product_media(name)
        caption = dop.format_product_with_media(name)
        if media_info:
            mtype = media_info['type']
            file_id = media_info['file_id']
            if mtype == 'photo':
                bot.send_photo(chat_id, file_id, caption=caption, parse_mode='Markdown')
            elif mtype == 'video':
                bot.send_video(chat_id, file_id, caption=caption, parse_mode='Markdown')
            elif mtype == 'document':
                bot.send_document(chat_id, file_id, caption=caption, parse_mode='Markdown')
            elif mtype == 'audio':
                bot.send_audio(chat_id, file_id, caption=caption, parse_mode='Markdown')
            elif mtype == 'animation':
                bot.send_animation(chat_id, file_id, caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, caption, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, caption or name, parse_mode='Markdown')

        if os.path.exists(media_temp):
            os.remove(media_temp)
        
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
        user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
        user_markup.row('📝 Descripción adicional')
        user_markup.row('🎬 Multimedia productos')
        user_markup.row('Volver al menú principal')
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, '¡Producto añadido con éxito!', reply_markup=user_markup)

def handle_multimedia(message):
    """Manejar archivos multimedia enviados por admin"""
    chat_id = message.chat.id
    
    try:
        with shelve.open(files.sost_bd) as bd:
            state = bd.get(str(chat_id))

        if state not in (32, 200, 42):
            return

        if state == 32:
            temp_path = 'data/Temp/' + str(chat_id) + 'media_product.txt'
        elif state == 42:
            temp_path = 'data/Temp/' + str(chat_id) + '.txt'
        else:
            temp_path = 'data/Temp/' + str(chat_id) + 'new_media.txt'

        product_name = None
        if state == 32:
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
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
            media_type = 'photo'
        elif message.video:
            file_id = message.video.file_id
            media_type = 'video'
        elif message.document:
            file_id = message.document.file_id
            media_type = 'document'
        elif message.audio:
            file_id = message.audio.file_id
            media_type = 'audio'
        elif message.animation:
            file_id = message.animation.file_id
            media_type = 'animation'
                
        if file_id and media_type:
            if state == 32:
                saved = dop.save_product_media(product_name, file_id, media_type, caption)
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
            elif state == 42:
                try:
                    with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f:
                        lines = f.read().splitlines()
                    group = lines[0]
                    amount = int(lines[1])
                    text = lines[2]
                except Exception:
                    bot.send_message(chat_id, '❌ La sesión anterior se perdió.')
                    with shelve.open(files.sost_bd) as bd:
                        if str(chat_id) in bd:
                            del bd[str(chat_id)]
                    in_adminka(chat_id, 'Volver al menú principal', None, None)
                    return

                media_path = f"data/Temp/{chat_id}_broadcast_media.txt"
                with open(media_path, 'w', encoding='utf-8') as f:
                    f.write(file_id + '\n')
                    f.write(media_type + '\n')
                    if caption:
                        f.write(caption)

                key = telebot.types.InlineKeyboardMarkup()
                key.add(
                    telebot.types.InlineKeyboardButton(text='✅ Enviar boletín', callback_data='CONFIRM_BROADCAST')
                )
                key.add(
                    telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración',
                                                       callback_data='Volver al menú principal de administración')
                )
                bot.send_message(chat_id, 'Archivo recibido. ¿Desea enviar el mensaje ahora?', reply_markup=key)
                with shelve.open(files.sost_bd) as bd:
                    del bd[str(chat_id)]
                return
            else:
                with open('data/Temp/' + str(chat_id) + 'new_media.txt', 'w', encoding='utf-8') as f:
                    f.write(file_id + '\n')
                    f.write(media_type + '\n')
                    if caption:
                        f.write(caption)
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                bot.send_message(chat_id, 'Ingrese el nombre del nuevo producto', reply_markup=key)
                with shelve.open(files.sost_bd) as bd:
                    bd[str(chat_id)] = 2
                return

            media_names = {
                'photo': '📸 Imagen',
                'video': '🎥 Video',
                'document': '📄 Documento',
                'audio': '🎵 Audio',
                'animation': '🎬 GIF'
            }

            if saved:
                bot.send_message(
                    chat_id,
                    f'✅ {media_names.get(media_type, "Archivo")} agregado al producto: {product_name}',
                    reply_markup=user_markup,
                )
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
            else:
                bot.send_message(chat_id, '❌ Error guardando multimedia')
        else:
            bot.send_message(chat_id, '❌ Tipo de archivo no soportado. Envía: foto, video, documento, audio o GIF')
    except:
        pass
