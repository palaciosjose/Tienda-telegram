import telebot, shelve, sqlite3, os
import config, dop, payments, adminka, files

print("DEBUG: main.py - Script iniciado.")

# Verificar que existe la base de datos
if not os.path.exists('data/db/main_data.db'):
    print("ERROR: Base de datos no encontrada. Ejecuta init_db.py primero.")
    exit(1)

bot = telebot.TeleBot(config.token)
in_admin = []

print("DEBUG: main.py - Bot inicializado.")

@bot.message_handler(content_types=["text"])
def message_send(message):
    print(f"DEBUG: message_send - Mensaje recibido: {message.text} de {message.chat.id}")
    
    if '/start' == message.text:
        print(f"DEBUG: /start handler - Procesando comando /start.")
        
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
                bot.send_message(message.chat.id, '¡El bot aún no está listo para funcionar!\nSi eres el administrador, entra con la cuenta cuyo ID especificaste al iniciar el bot y prepáralo para funcionar!')
            elif dop.check_message('start') is True:
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Ir al catálogo de productos', callback_data='Ir al catálogo de productos'))
                with shelve.open(files.bot_message_bd) as bd: 
                    start_message = bd['start']
                start_message = start_message.replace('username', message.chat.username)
                start_message = start_message.replace('name', message.from_user.first_name)
                bot.send_message(message.chat.id, start_message, reply_markup=key)	
            elif dop.check_message('start') is False and is_in_admin_list:
                bot.send_message(message.chat.id, '¡El saludo aún no ha sido agregado!\nPara agregarlo, ve al panel de administración con el comando /adm y *configura las respuestas del bot*', parse_mode='Markdown')

            dop.user_loger(chat_id=message.chat.id)

        elif not message.chat.username:
            if dop.check_message('userfalse'):
                with shelve.open(files.bot_message_bd) as bd: 
                    start_message = bd['userfalse']
                start_message = start_message.replace('uname', message.from_user.first_name)
                bot.send_message(message.chat.id, start_message, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, 'Para usar el bot necesitas establecer un nombre de usuario en la configuración de Telegram.')
            dop.user_loger(chat_id=message.chat.id)
			
    elif '/adm' == message.text:
        if not message.chat.id in in_admin:  
            in_admin.append(message.chat.id)
        adminka.in_adminka(message.chat.id, message.text, message.chat.username, message.from_user.first_name)

    elif message.chat.id in in_admin:
        adminka.in_adminka(message.chat.id, message.text, message.chat.username, message.from_user.first_name)

    elif '/help' == message.text:
        if dop.check_message('help') is True:
            with shelve.open(files.bot_message_bd) as bd: 
                help_message = bd['help']
            bot.send_message(message.chat.id, help_message)
        elif dop.check_message('help') is False and message.chat.id in dop.get_adminlist():
            bot.send_message(message.chat.id, '¡El mensaje de ayuda aún no ha sido agregado!\nPara agregarlo, ve al panel de administración con el comando /adm y *configura las respuestas del bot*', parse_mode='Markdown')

    elif dop.get_sost(message.chat.id) is True:
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
                    if dop.check_vklpayments('paypal') == '✅' and dop.check_vklpayments('binance') == '✅':
                        b1 = telebot.types.InlineKeyboardButton(text='💳 PayPal', callback_data='PayPal')
                        b2 = telebot.types.InlineKeyboardButton(text='🟡 Binance', callback_data='Binance')
                        key.add(b1, b2)
                    elif dop.check_vklpayments('paypal') == '✅': 
                        key.add(telebot.types.InlineKeyboardButton(text='💳 PayPal', callback_data='PayPal'))
                    elif dop.check_vklpayments('binance') == '✅': 
                        key.add(telebot.types.InlineKeyboardButton(text='🟡 Binance', callback_data='Binance'))
                    key.add(telebot.types.InlineKeyboardButton(text='Volver al inicio', callback_data='Volver al inicio'))
                    bot.send_message(message.chat.id,'Has *elegido*: ' + name_good + '\n*Cantidad*: ' + str(amount) + '\n*Total* del pedido: $' + str(sum_price) + ' USD\nElige donde deseas pagar', parse_mode='Markdown', reply_markup=key)
                    with open('data/Temp/' + str(message.chat.id) + '.txt', 'w', encoding='utf-8') as f:
                        f.write(str(amount) + '\n')
                        f.write(str(sum_price) + '\n')
                elif dop.get_minimum(name_good) > amount: 
                    key.add(telebot.types.InlineKeyboardButton(text='Volver al inicio', callback_data='Volver al inicio'))
                    bot.send_message(message.chat.id, '¡Elige y envía una cantidad mayor!\nCantidad mínima para comprar *' + str(dop.get_minimum(name_good)) + '*', parse_mode='Markdown', reply_markup=key)
                elif amount > dop.amount_of_goods(name_good): 
                    key.add(telebot.types.InlineKeyboardButton(text='Volver al inicio', callback_data='Volver al inicio'))
                    bot.send_message(message.chat.id, '¡Elige y envía una cantidad menor!\nCantidad máxima para comprar *' + str(dop.amount_of_goods(name_good)) + '*', parse_mode='Markdown', reply_markup=key)
            except Exception as e: 
                key.add(telebot.types.InlineKeyboardButton(text='Volver al inicio', callback_data='Volver al inicio'))
                bot.send_message(message.chat.id, '¡La cantidad debe elegirse estrictamente en números!', reply_markup=key)


@bot.callback_query_handler(func=lambda c:True)
def inline(callback):
    print(f"DEBUG: inline - Callback recibido: {callback.data} de {callback.message.chat.id}")
    the_goods = dop.get_goods()
    
    # NUEVO: Manejar callbacks de aprobación/rechazo de pagos
    if callback.data.startswith('APROBAR_PAGO_') or callback.data.startswith('RECHAZAR_PAGO_'):
        # Verificar que quien responde es admin
        if callback.message.chat.id in dop.get_adminlist():
            payments.handle_admin_payment_decision(
                callback.data, 
                callback.message.chat.id, 
                callback.id, 
                callback.message.message_id
            )
        else:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='❌ No tienes permisos')
        return
    
    # NUEVO: Manejar envío de comprobantes
    elif callback.data == 'Enviar comprobante Binance':
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, 
                                 text='📱 Envía una captura de pantalla del comprobante de pago como imagen al chat')
        return
    
    if callback.message.chat.id in in_admin:
        adminka.ad_inline(callback.data, callback.message.chat.id, callback.message.message_id)

    elif callback.data == 'Ir al catálogo de productos':
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT name, price FROM goods;")
        key = telebot.types.InlineKeyboardMarkup()
        for name, price in cursor.fetchall():
            key.add(telebot.types.InlineKeyboardButton(text=name, callback_data=name))
        key.add(telebot.types.InlineKeyboardButton(text='Volver al inicio', callback_data='Volver al inicio'))
        con.close()

        if dop.get_productcatalog() == None:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Actualmente no se ha creado ningún producto en el bot')
        else:
            try:
                bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dop.get_productcatalog(), reply_markup=key, parse_mode='Markdown')
            except Exception as e:
                print(f"DEBUG: Error editando mensaje: {e}")

    # ===== SECCIÓN MODIFICADA =====
    elif callback.data in the_goods:
        with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', 'w', encoding='utf-8') as f: 
            f.write(callback.data)
        
        # Crear teclado con botón "Más información" si existe descripción adicional
        key = telebot.types.InlineKeyboardMarkup()
        
        # Verificar si el producto tiene información adicional
        if dop.has_additional_description(callback.data):
            key.add(telebot.types.InlineKeyboardButton(text='ℹ️ Más información', callback_data=f'MAS_INFO_{callback.data}'))
        
        key.add(telebot.types.InlineKeyboardButton(text='💰 Comprar', callback_data='Comprar'))
        key.add(telebot.types.InlineKeyboardButton(text='🔙 Volver al inicio', callback_data='Volver al inicio'))
        
        try: 
            # Usar la nueva función para mostrar información básica del producto
            product_info = dop.format_product_basic_info(callback.data)
            bot.edit_message_text(
                chat_id=callback.message.chat.id, 
                message_id=callback.message.message_id, 
                text=product_info, 
                reply_markup=key,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"DEBUG: Error editando mensaje: {e}")
    
    # ===== NUEVO CALLBACK =====
    elif callback.data.startswith('MAS_INFO_'):
        product_name = callback.data.replace('MAS_INFO_', '')
        
        # Crear teclado para volver a la vista del producto
        key = telebot.types.InlineKeyboardMarkup()
        key.add(telebot.types.InlineKeyboardButton(text='🔙 Volver al producto', callback_data=product_name))
        key.add(telebot.types.InlineKeyboardButton(text='💰 Comprar', callback_data='Comprar'))
        key.add(telebot.types.InlineKeyboardButton(text='🏠 Ir al inicio', callback_data='Volver al inicio'))
        
        try:
            # Mostrar información adicional
            additional_info = dop.format_product_additional_info(product_name)
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=additional_info,
                reply_markup=key,
                parse_mode='Markdown'
            )
            
            # Confirmar la acción al usuario
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='ℹ️ Información adicional mostrada')
            
        except Exception as e:
            print(f"DEBUG: Error mostrando información adicional: {e}")
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='❌ Error cargando información')

    elif callback.data == 'Volver al inicio':
        if callback.message.chat.username:
            if dop.get_sost(callback.message.chat.id) is True: 
                with shelve.open(files.sost_bd) as bd: 
                    if str(callback.message.chat.id) in bd:
                        del bd[str(callback.message.chat.id)]
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Ir al catálogo de productos', callback_data='Ir al catálogo de productos'))
            if dop.check_message('start'):
                with shelve.open(files.bot_message_bd) as bd: 
                    start_message = bd['start']
                start_message = start_message.replace('username', callback.message.chat.username)
                start_message = start_message.replace('name', callback.message.from_user.first_name)
                try: 
                    bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=start_message, reply_markup=key)
                except Exception as e:
                    print(f"DEBUG: Error editando mensaje: {e}")

    elif callback.data == 'Comprar':
        with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', encoding='utf-8') as f: 
            name_good = f.read()
        if dop.amount_of_goods(name_good) == 0:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Actualmente no disponible para compra')
        elif dop.payments_checkvkl() == None:
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Los pagos están desactivados actualmente')
        else:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Volver al inicio', callback_data='Volver al inicio'))
            try: 
                bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='Ingresa la *cantidad* de productos a comprar\nCantidad *mínima* para comprar: ' + str(dop.get_minimum(name_good)) + '\n*Máximo* disponible: ' + str(dop.amount_of_goods(name_good)), reply_markup=key, parse_mode='Markdown')
            except Exception as e:
                print(f"DEBUG: Error editando mensaje: {e}")
            with shelve.open(files.sost_bd) as bd: 
                bd[str(callback.message.chat.id)] = 22

    # Callbacks de pagos nuevos
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
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='¡No es posible pagar menos de $5 USD con Binance!')
            else: 
                payments.creat_bill_binance(callback.message.chat.id, callback.id, callback.message.message_id, sum_price, name_good, amount)
    
    elif callback.data == 'Verificar pago PayPal':
        payments.check_oplata_paypal(callback.message.chat.id, callback.from_user.username, callback.id, callback.from_user.first_name, callback.message.message_id)
    
    elif callback.data == 'Verificar pago Binance':
        payments.check_oplata_binance(callback.message.chat.id, callback.from_user.username, callback.id, callback.from_user.first_name, callback.message.message_id)

    elif callback.data.startswith('MAS_INFO_'):
        product_name = callback.data.replace('MAS_INFO_', '')
    
    # Crear teclado para volver a la vista del producto
    key = telebot.types.InlineKeyboardMarkup()
    key.add(telebot.types.InlineKeyboardButton(text='🔙 Volver al producto', callback_data=product_name))
    key.add(telebot.types.InlineKeyboardButton(text='💰 Comprar', callback_data='Comprar'))
    key.add(telebot.types.InlineKeyboardButton(text='🏠 Ir al inicio', callback_data='Volver al inicio'))
    
    try:
        # Mostrar información adicional
        additional_info = dop.format_product_additional_info(product_name)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=additional_info,
            reply_markup=key,
            parse_mode='Markdown'
        )
        
        # Confirmar la acción al usuario
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=False, text='ℹ️ Información adicional mostrada')
        
    except Exception as e:
        print(f"DEBUG: Error mostrando información adicional: {e}")
        bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='❌ Error cargando información')

@bot.message_handler(content_types=['document'])
def handle_docs_log(message):
    if message.chat.id in in_admin:
        if dop.get_sost(message.chat.id) and shelve.open(files.sost_bd)[str(message.chat.id)] == 12:
            adminka.new_files(message.document.file_id, message.chat.id)

if __name__ == '__main__':
    print("DEBUG: main.py - Calling bot.infinity_polling().")
    bot.infinity_polling()