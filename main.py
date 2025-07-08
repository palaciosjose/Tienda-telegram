import telebot, shelve, sqlite3, os
import config, dop, payments, adminka, files, subscriptions
import db
from bot_instance import bot
import atexit
import glob

# Limpieza automática de archivos temporales al cerrar
def cleanup_temp_files():
    """Limpiar archivos temporales al cerrar"""
    try:
        temp_files = glob.glob('data/Temp/*')
        for f in temp_files:
            if os.path.isfile(f) and os.path.getsize(f) == 0:  # Solo archivos vacíos
                os.remove(f)
    except:
        pass

# Registrar limpieza al cerrar
atexit.register(cleanup_temp_files)

# Solo log crítico
print("🚀 Bot iniciado.")

# Verificar que existe la base de datos
if not os.path.exists('data/db/main_data.db'):
    print("❌ ERROR: Base de datos no encontrada. Ejecuta init_db.py primero.")
    exit(1)


in_admin = []

@bot.message_handler(content_types=["text"])
def message_send(message):
    # Permitir que adminka.py procese archivos multimedia cuando corresponde
    adminka.handle_multimedia(message)
    
    if '/start' == message.text:
        if message.chat.username:
            # Limpiar estado si existe
            if dop.get_sost(message.chat.id) is True: 
                with shelve.open(files.sost_bd) as bd: 
                    if str(message.chat.id) in bd:
                        del bd[str(message.chat.id)]
            
            if message.chat.id in in_admin:
                in_admin.remove(message.chat.id)
            
            # Verificar si es primera vez
            is_first_user = dop.it_first(message.chat.id)
            is_admin_user = (message.chat.id == config.admin_id)
            admin_list = dop.get_adminlist()
            is_in_admin_list = (message.chat.id in admin_list)
            
            if is_admin_user and is_first_user:
                in_admin.append(message.chat.id)
                dop.main(message.chat.id)
            elif is_first_user and not is_in_admin_list:
                bot.send_message(message.chat.id, '🚧 **¡El bot aún no está listo para funcionar!**\n\n🔧 Si eres el administrador, entra con la cuenta cuyo ID especificaste al iniciar el bot y prepáralo para funcionar!', parse_mode='Markdown')
            elif dop.check_message('start') is True:
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='🛍️ Catálogo', callback_data='Ir al catálogo de productos'))
                key.add(telebot.types.InlineKeyboardButton(text='🌀 Suscripciones', callback_data='Ir al catálogo de suscripciones'))
                with shelve.open(files.bot_message_bd) as bd: 
                    start_message = bd['start']
                start_message = start_message.replace('username', message.chat.username)
                start_message = start_message.replace('name', message.from_user.first_name)
                bot.send_message(message.chat.id, start_message, reply_markup=key)	
            elif dop.check_message('start') is False and is_in_admin_list:
                bot.send_message(message.chat.id, '👋 **¡El saludo aún no ha sido agregado!**\n\nPara agregarlo, ve al panel de administración con el comando `/adm` y **configura las respuestas del bot**', parse_mode='Markdown')

            dop.user_loger(chat_id=message.chat.id)

        elif not message.chat.username:
            if dop.check_message('userfalse'):
                with shelve.open(files.bot_message_bd) as bd: 
                    start_message = bd['userfalse']
                start_message = start_message.replace('uname', message.from_user.first_name)
                bot.send_message(message.chat.id, start_message, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, '⚠️ **Para usar el bot necesitas establecer un nombre de usuario en la configuración de Telegram.**\n\n📱 Ve a Configuración → Editar perfil → Nombre de usuario', parse_mode='Markdown')
            dop.user_loger(chat_id=message.chat.id)
			
    elif '/adm' == message.text:
        if message.chat.id not in in_admin:
            in_admin.append(message.chat.id)
        adminka.in_adminka(message.chat.id, message.text, message.chat.username, message.from_user.first_name)

    elif dop.get_sost(message.chat.id) is True:
        if message.chat.id in in_admin:
            adminka.text_analytics(message.text, message.chat.id)
        else:
            with shelve.open(files.sost_bd) as bd:
                sost_num = bd[str(message.chat.id)]
            if sost_num == 22:
                key = telebot.types.InlineKeyboardMarkup()
                try:
                    amount = int(message.text)
                    with open('data/Temp/' + str(message.chat.id) + 'good_name.txt', encoding='utf-8') as f:
                        name_good = f.read()
                    if dop.get_minimum(name_good) <= amount <= dop.amount_of_goods(name_good):
                        sum_price = dop.order_sum(name_good, amount)
                        # Optimización: verificar pagos una sola vez
                        paypal_active = dop.check_vklpayments('paypal') == '✅'
                        binance_active = dop.check_vklpayments('binance') == '✅'
                        
                        if paypal_active and binance_active:
                            b1 = telebot.types.InlineKeyboardButton(text='💳 PayPal', callback_data='PayPal')
                            b2 = telebot.types.InlineKeyboardButton(text='🟡 Binance Pay', callback_data='Binance')
                            key.add(b1, b2)
                        elif paypal_active:
                            key.add(telebot.types.InlineKeyboardButton(text='💳 PayPal', callback_data='PayPal'))
                        elif binance_active:
                            key.add(telebot.types.InlineKeyboardButton(text='🟡 Binance Pay', callback_data='Binance'))
                        key.add(telebot.types.InlineKeyboardButton(text='🔙 Inicio', callback_data='Volver al inicio'))

                        bot.send_message(message.chat.id,
                                         f'✅ **Has elegido:** {name_good}\n🔢 **Cantidad:** {str(amount)}\n💰 **Total del pedido:** ${str(sum_price)} USD\n\n💳 **Elige tu método de pago:**',
                                         parse_mode='Markdown', reply_markup=key)

                        with open('data/Temp/' + str(message.chat.id) + '.txt', 'w', encoding='utf-8') as f:
                            f.write(str(amount) + '\n')
                            f.write(str(sum_price) + '\n')
                    elif dop.get_minimum(name_good) > amount:
                        key.add(telebot.types.InlineKeyboardButton(text='🔙 Inicio', callback_data='Volver al inicio'))
                        bot.send_message(message.chat.id,
                                         f'⚠️ **¡Elige una cantidad mayor!**\n\n📊 **Cantidad mínima:** {str(dop.get_minimum(name_good))} unidades',
                                         parse_mode='Markdown', reply_markup=key)
                    elif amount > dop.amount_of_goods(name_good):
                        key.add(telebot.types.InlineKeyboardButton(text='🔙 Inicio', callback_data='Volver al inicio'))
                        bot.send_message(message.chat.id,
                                         f'⚠️ **¡Elige una cantidad menor!**\n\n📦 **Stock disponible:** {str(dop.amount_of_goods(name_good))} unidades',
                                         parse_mode='Markdown', reply_markup=key)
                except Exception as e:
                    key.add(telebot.types.InlineKeyboardButton(text='🔙 Inicio', callback_data='Volver al inicio'))
                    bot.send_message(message.chat.id,
                                     '❌ **¡La cantidad debe ser un número válido!**\n\n🔢 Envía solo números (ej: 5)',
                                     parse_mode='Markdown', reply_markup=key)

    elif message.chat.id in in_admin:
        adminka.in_adminka(message.chat.id, message.text, message.chat.username, message.from_user.first_name)

    elif '/help' == message.text:
        if dop.check_message('help') is True:
            with shelve.open(files.bot_message_bd) as bd:
                help_message = bd['help']
            bot.send_message(message.chat.id, help_message)
        elif dop.check_message('help') is False and message.chat.id in dop.get_adminlist():
            bot.send_message(message.chat.id, '❓ **¡El mensaje de ayuda aún no ha sido agregado!**\n\nPara agregarlo, ve al panel de administración con el comando `/adm` y **configura las respuestas del bot**', parse_mode='Markdown')


@bot.callback_query_handler(func=lambda c:True)
def inline(callback):
    try:
        # Solo obtener goods cuando sea necesario - optimización aplicada
        the_goods = None
        if callback.data == 'Ir al catálogo de productos' or (callback.data not in ['APROBAR_PAGO_', 'RECHAZAR_PAGO_', 'Enviar comprobante Binance', 'Volver al inicio', 'Comprar'] and not callback.data.startswith(('SUBINFO_', 'SUBP_', 'BUY_SUB_', 'MAS_INFO_'))):
            the_goods = dop.get_goods()
        
        # Manejar callbacks de aprobación/rechazo de pagos
        if callback.data.startswith('APROBAR_PAGO_') or callback.data.startswith('RECHAZAR_PAGO_'):
            if callback.message.chat.id in dop.get_adminlist():
                payments.handle_admin_payment_decision(
                    callback.data, 
                    callback.message.chat.id, 
                    callback.id, 
                    callback.message.message_id
                )
            else:
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='❌ No tienes permisos de administrador')
            return
        
        # Manejar envío de comprobantes
        elif callback.data == 'Enviar comprobante Binance':
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, 
                                     text='📱 Envía una captura de pantalla del comprobante de pago como imagen al chat')
            return
        
        if callback.message.chat.id in in_admin:
            adminka.ad_inline(callback.data, callback.message.chat.id, callback.message.message_id)

        elif callback.data == 'Ir al catálogo de productos':
            # Optimización: usar conexión eficiente
            con = dop.get_db_connection() if hasattr(dop, 'get_db_connection') else db.get_db_connection()
            cursor = con.cursor()
            cursor.execute("SELECT name, price FROM goods;")
            key = telebot.types.InlineKeyboardMarkup()
            
            # Agregar productos con emojis
            for name, price in cursor.fetchall():
                key.add(telebot.types.InlineKeyboardButton(text=f'📦 {name}', callback_data=name))
            
            key.add(telebot.types.InlineKeyboardButton(text='🏠 Inicio', callback_data='Volver al inicio'))

            if dop.get_productcatalog() == None:
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='📭 No hay productos disponibles en este momento')
            else:
                catalog_text = f"🛍️ **CATÁLOGO DE PRODUCTOS**\n{'-'*30}\n\n{dop.get_productcatalog()}"
                dop.safe_edit_message(bot, callback.message, catalog_text, reply_markup=key, parse_mode='Markdown')

        elif callback.data == 'Ir al catálogo de suscripciones':
            plans = subscriptions.get_all_subscription_products()
            key = telebot.types.InlineKeyboardMarkup()
            for plan in plans:
                key.add(telebot.types.InlineKeyboardButton(text=f'🌀 {plan[1]}', callback_data=f'SUBP_{plan[0]}'))
            key.add(telebot.types.InlineKeyboardButton(text='🏠 Inicio', callback_data='Volver al inicio'))

            if not plans:
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='No hay planes disponibles')
            else:
                catalog_text = '🌀 *PLANES DISPONIBLES*\n\nSeleccione un plan para ver detalles.'
                dop.safe_edit_message(bot, callback.message, catalog_text, reply_markup=key, parse_mode='Markdown')

        # Mostrar información del producto
        elif the_goods and callback.data in the_goods:
            with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', 'w', encoding='utf-8') as f: 
                f.write(callback.data)
            
            # Crear teclado con botón "Más información" si existe descripción adicional
            key = telebot.types.InlineKeyboardMarkup()
            
            # Verificar si el producto tiene información adicional
            if dop.has_additional_description(callback.data):
                key.add(telebot.types.InlineKeyboardButton(text='ℹ️ Más información', callback_data=f'MAS_INFO_{callback.data}'))
            
            key.add(telebot.types.InlineKeyboardButton(text='💰 Comprar ahora', callback_data='Comprar'))
            key.add(telebot.types.InlineKeyboardButton(text='🔙 Catálogo', callback_data='Ir al catálogo de productos'))
            key.add(telebot.types.InlineKeyboardButton(text='🏠 Inicio', callback_data='Volver al inicio'))
            
            # Optimización: manejo de multimedia más eficiente
            media_info = dop.get_product_media(callback.data)
            formatted_info = dop.format_product_with_media(callback.data)

            if media_info:
                try:
                    if media_info['type'] == 'photo':
                        bot.edit_message_media(
                            chat_id=callback.message.chat.id,
                            message_id=callback.message.message_id,
                            media=telebot.types.InputMediaPhoto(
                                media=media_info['file_id'],
                                caption=formatted_info,
                                parse_mode='Markdown'
                            ),
                            reply_markup=key
                        )
                    elif media_info['type'] == 'video':
                        bot.edit_message_media(
                            chat_id=callback.message.chat.id,
                            message_id=callback.message.message_id,
                            media=telebot.types.InputMediaVideo(
                                media=media_info['file_id'],
                                caption=formatted_info,
                                parse_mode='Markdown'
                            ),
                            reply_markup=key
                        )
                    else:
                        bot.delete_message(callback.message.chat.id, callback.message.message_id)
                        if media_info['type'] == 'document':
                            bot.send_document(
                                chat_id=callback.message.chat.id,
                                document=media_info['file_id'],
                                caption=formatted_info,
                                reply_markup=key,
                                parse_mode='Markdown'
                            )
                        elif media_info['type'] == 'audio':
                            bot.send_audio(
                                chat_id=callback.message.chat.id,
                                audio=media_info['file_id'],
                                caption=formatted_info,
                                reply_markup=key,
                                parse_mode='Markdown'
                            )
                except:
                    # Fallback a mensaje de texto
                    dop.safe_edit_message(bot, callback.message, formatted_info, reply_markup=key, parse_mode='Markdown')
            else:
                dop.safe_edit_message(bot, callback.message, formatted_info, reply_markup=key, parse_mode='Markdown')
        
        # Mostrar información adicional del producto
        elif callback.data.startswith('MAS_INFO_'):
            product_name = callback.data.replace('MAS_INFO_', '')
            
            # Crear teclado para volver a la vista del producto
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='🔙 Volver al producto', callback_data=product_name))
            key.add(telebot.types.InlineKeyboardButton(text='💰 Comprar ahora', callback_data='Comprar'))
            key.add(telebot.types.InlineKeyboardButton(text='🛍️ Catálogo', callback_data='Ir al catálogo de productos'))
            key.add(telebot.types.InlineKeyboardButton(text='🏠 Inicio', callback_data='Volver al inicio'))
            
            # Mostrar información adicional
            additional_info = dop.format_product_additional_info(product_name)
            enhanced_additional = f"📋 **INFORMACIÓN ADICIONAL**\n{'-'*30}\n\n{additional_info}"
            
            dop.safe_edit_message(bot, callback.message, enhanced_additional, reply_markup=key, parse_mode='Markdown')
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='ℹ️ Información adicional mostrada')

        elif callback.data.startswith('SUBINFO_'):
            sub_id = int(callback.data.split('_')[1])
            plan = subscriptions.get_subscription_product(sub_id)
            if not plan:
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Plan no encontrado')
            else:
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='🔙 Volver al plan', callback_data=f'SUBP_{sub_id}'))
                key.add(telebot.types.InlineKeyboardButton(text='🏠 Inicio', callback_data='Volver al inicio'))
                info = subscriptions.format_plan_additional_info(sub_id)
                enhanced = f"📋 **INFORMACIÓN ADICIONAL**\n{'-'*30}\n\n{info}"
                dop.safe_edit_message(bot, callback.message, enhanced, reply_markup=key, parse_mode='Markdown')

        elif callback.data.startswith('SUBP_'):
            sub_id = int(callback.data.split('_')[1])
            plan = subscriptions.get_subscription_product(sub_id)
            if not plan:
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Plan no encontrado')
            else:
                key = telebot.types.InlineKeyboardMarkup()
                if subscriptions.has_additional_description(plan[1]):
                    key.add(telebot.types.InlineKeyboardButton(text="ℹ️ Más información", callback_data=f"SUBINFO_{sub_id}"))
                key.add(telebot.types.InlineKeyboardButton(text="💳 Suscribirme", callback_data=f"BUY_SUB_{sub_id}"))
                key.add(telebot.types.InlineKeyboardButton(text="🔙 Suscripciones", callback_data="Ir al catálogo de suscripciones"))
                key.add(telebot.types.InlineKeyboardButton(text="🏠 Inicio", callback_data="Volver al inicio"))
                media = subscriptions.get_plan_media(plan[1])
                formatted = subscriptions.format_plan_with_media(sub_id)
                if media and media["type"] in ("photo", "video"):
                    try:
                        input_media = telebot.types.InputMediaPhoto if media["type"] == "photo" else telebot.types.InputMediaVideo
                        bot.edit_message_media(chat_id=callback.message.chat.id, message_id=callback.message.message_id, media=input_media(media=media["file_id"], caption=formatted, parse_mode="Markdown"), reply_markup=key)
                    except Exception:
                        dop.safe_edit_message(bot, callback.message, formatted, reply_markup=key, parse_mode="Markdown")
                elif media and media["type"] in ("document", "audio", "animation"):
                    bot.delete_message(callback.message.chat.id, callback.message.message_id)
                    if media["type"] == "document":
                        bot.send_document(callback.message.chat.id, media["file_id"], caption=formatted, reply_markup=key, parse_mode="Markdown")
                    elif media["type"] == "audio":
                        bot.send_audio(callback.message.chat.id, media["file_id"], caption=formatted, reply_markup=key, parse_mode="Markdown")
                    else:
                        bot.send_animation(callback.message.chat.id, media["file_id"], caption=formatted, reply_markup=key, parse_mode="Markdown")
                else:
                    dop.safe_edit_message(bot, callback.message, formatted, reply_markup=key, parse_mode="Markdown")

        elif callback.data.startswith('BUY_SUB_'):
            sub_id = int(callback.data.split('_')[2])
            plan = subscriptions.get_subscription_product(sub_id)
            if not plan:
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Plan no disponible')
            else:
                _, name, desc, price, currency, duration, unit, *_ = plan
                key = telebot.types.InlineKeyboardMarkup()
                if dop.check_vklpayments('paypal') == '✅':
                    key.add(telebot.types.InlineKeyboardButton(text='💳 PayPal', callback_data='PayPal'))
                if dop.check_vklpayments('binance') == '✅':
                    key.add(telebot.types.InlineKeyboardButton(text='🟡 Binance Pay', callback_data='Binance'))
                key.add(telebot.types.InlineKeyboardButton(text='🔙 Plan', callback_data=f'SUBP_{sub_id}'))
                key.add(telebot.types.InlineKeyboardButton(text='🏠 Inicio', callback_data='Volver al inicio'))
                dop.safe_edit_message(bot, callback.message, f'🌀 *{name}*\nPrecio: {price} {currency}\nDuración: {duration} {unit}\n\nSelecciona método de pago:', reply_markup=key, parse_mode='Markdown')
                with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', 'w', encoding='utf-8') as f:
                    f.write(f'SUB:{sub_id}')
                with open('data/Temp/' + str(callback.message.chat.id) + '.txt', 'w', encoding='utf-8') as f:
                    f.write('1\n')
                    f.write(str(price) + '\n')

        elif callback.data == 'Volver al inicio':
            if callback.message.chat.username:
                if dop.get_sost(callback.message.chat.id) is True: 
                    with shelve.open(files.sost_bd) as bd: 
                        if str(callback.message.chat.id) in bd:
                            del bd[str(callback.message.chat.id)]
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='🛍️ Catálogo', callback_data='Ir al catálogo de productos'))
                key.add(telebot.types.InlineKeyboardButton(text='🌀 Suscripciones', callback_data='Ir al catálogo de suscripciones'))
                if dop.check_message('start'):
                    with shelve.open(files.bot_message_bd) as bd: 
                        start_message = bd['start']
                    start_message = start_message.replace('username', callback.message.chat.username)
                    start_message = start_message.replace('name', callback.message.from_user.first_name)
                    dop.safe_edit_message(bot, callback.message, start_message, reply_markup=key)

        elif callback.data == 'Comprar':
            with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', encoding='utf-8') as f: 
                name_good = f.read()
            if not name_good.startswith('SUB:') and dop.amount_of_goods(name_good) == 0:
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='❌ Producto agotado - No disponible para compra')
            elif dop.payments_checkvkl() == None:
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='💳 Los pagos están temporalmente desactivados')
            else:
                key = telebot.types.InlineKeyboardMarkup()
                back_cb = name_good if not name_good.startswith('SUB:') else f'SUBP_{name_good.split(":")[1]}'
                key.add(telebot.types.InlineKeyboardButton(text='🔙 Volver al producto', callback_data=back_cb))
                key.add(telebot.types.InlineKeyboardButton(text='🏠 Inicio', callback_data='Volver al inicio'))
                
                if name_good.startswith('SUB:'):
                    sub_id = int(name_good.split(':')[1])
                    plan = subscriptions.get_subscription_product(sub_id)
                    if plan:
                        _, name, desc, price, currency, duration, unit, *_ = plan
                        purchase_text = f"🌀 *{name}*\nPrecio: {price} {currency}\nDuración: {duration} {unit}"
                        dop.safe_edit_message(bot, callback.message, purchase_text, reply_markup=key, parse_mode='Markdown')
                        with open('data/Temp/' + str(callback.message.chat.id) + '.txt', 'w', encoding='utf-8') as f:
                            f.write('1\n')
                            f.write(str(price) + '\n')
                    else:
                        bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Plan no disponible')
                        return
                else:
                    purchase_text = f"""🛒 **REALIZAR COMPRA**\n{'-'*25}\n\n📦 **Producto:** {name_good}\n\n🔢 **Ingresa la cantidad** que deseas comprar:\n\n📊 **Cantidad mínima:** {str(dop.get_minimum(name_good))} unidades\n📦 **Stock disponible:** {str(dop.amount_of_goods(name_good))} unidades\n\n💡 **Tip:** Envía solo el número (ej: 5)"""
                    dop.safe_edit_message(bot, callback.message, purchase_text, reply_markup=key, parse_mode='Markdown')
                    with shelve.open(files.sost_bd) as bd:
                        bd[str(callback.message.chat.id)] = 22

        # Callbacks de pagos
        elif callback.data == 'PayPal' or callback.data == 'Binance':
            if callback.data == 'PayPal':
                with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', encoding='utf-8') as f: 
                    name_good = f.read()
                amount = dop.normal_read_line('data/Temp/' + str(callback.message.chat.id) + '.txt', 0)
                sum_price = dop.normal_read_line('data/Temp/' + str(callback.message.chat.id) + '.txt', 1)
                payments.creat_bill_paypal(callback.message.chat.id, callback.id, callback.message.message_id, sum_price, name_good, amount)
            elif callback.data == 'Binance':
                sum_price = dop.normal_read_line('data/Temp/' + str(callback.message.chat.id) + '.txt', 1)
                with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', encoding='utf-8') as f: 
                    name_good = f.read()
                amount = dop.normal_read_line('data/Temp/' + str(callback.message.chat.id) + '.txt', 0)
                if int(sum_price) < 5:
                    bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='⚠️ Binance Pay requiere un mínimo de $5 USD')
                else: 
                    payments.creat_bill_binance(callback.message.chat.id, callback.id, callback.message.message_id, sum_price, name_good, amount)
        
        elif callback.data == 'Verificar pago PayPal':
            payments.check_oplata_paypal(callback.message.chat.id, callback.from_user.username, callback.id, callback.from_user.first_name, callback.message.message_id)
        
        elif callback.data == 'Verificar pago Binance':
            payments.check_oplata_binance(callback.message.chat.id, callback.from_user.username, callback.id, callback.from_user.first_name, callback.message.message_id)

    except Exception as e:
        # Manejo de errores optimizado - no hacer print de todos los errores
        if "bad request" not in str(e).lower():
            print(f"Error en callback: {e}")

@bot.message_handler(content_types=['document'])
def handle_docs_log(message):
    """Manejar documentos enviados al bot"""
    adminka.handle_multimedia(message)

    if message.chat.id in in_admin:
        if dop.get_sost(message.chat.id) and shelve.open(files.sost_bd)[str(message.chat.id)] == 12:
            adminka.new_files(message.document.file_id, message.chat.id)

@bot.message_handler(content_types=['photo', 'video', 'audio', 'animation'])
def handle_media_files(message):
    """Manejar archivos multimedia (fotos, videos, audio, GIF)"""
    adminka.handle_multimedia(message)

if __name__ == '__main__':
    print("✅ Bot iniciando polling optimizado...")
    # Polling optimizado configurable mediante variables de entorno
    bot.polling(
        none_stop=True,
        interval=config.POLL_INTERVAL,
        timeout=config.POLL_TIMEOUT,
        long_polling_timeout=config.LONG_POLLING_TIMEOUT
    )
