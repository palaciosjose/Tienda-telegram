import telebot, sqlite3, shelve
import config, dop, files
import purchase_validator

bot = telebot.TeleBot(config.token)

def in_adminka(chat_id, message_text, username, name_user):
    if chat_id in dop.get_adminlist():
        if message_text == 'Volver al menú principal' or message_text == '/adm':
            if dop.get_sost(chat_id) is True: 
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Personalizar las respuestas del bot')
            user_markup.row('Configuración de surtido', 'Cargar nuevo producto')
            user_markup.row('Configuración de pago')
            user_markup.row('Configurar descuentos')
            user_markup.row('Estadísticas', 'Boletín informativo')
            user_markup.row('Validar Compras', 'Otras configuraciones')
            bot.send_message(chat_id, '¡Has ingresado al panel de administración del bot!\nPara salir, presiona /start', reply_markup=user_markup)

        elif message_text == 'Personalizar las respuestas del bot':
            if dop.check_message('start') is True: start = 'Cambiar'
            else: start = 'Añadir'
            if dop.check_message('after_buy'): after_buy = 'Cambiar'
            else: after_buy = 'Añadir'
            if dop.check_message('help'): help ='Cambiar'
            else: help = 'Añadir'
            if dop.check_message('userfalse'): userfalse = 'Cambiar'
            else: userfalse = 'Añadir'
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
            with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding ='utf-8') as f: f.write(message)
            with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 1

        elif 'Configuración de surtido' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
            user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
            user_markup.row('📝 Descripción adicional')
            user_markup.row('🎬 Multimedia productos')
            user_markup.row('Volver al menú principal')

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            goodz = 'Productos creados:\n\n'
            a = 0
            cursor.execute("SELECT name, description, format, minimum, price, stored FROM goods;") 
            for name, description, format, minimum, price, stored in cursor.fetchall():
                a += 1
                amount = dop.amount_of_goods(name)
                goodz += '*Nombre:* ' + name + '\n*Descripción:* ' + description + '\n*Formato del producto:* ' + format + '\n*Cantidad mínima para comprar:* ' + str(minimum) + '\n*Precio por unidad:* $' + str(price) + ' USD' + '\n*Unidades restantes:* ' + str(amount) + '\n\n'
            con.close()
            if a == 0: goodz = '¡No se han creado posiciones todavía!'	
            else: pass
            bot.send_message(chat_id, goodz, reply_markup=user_markup, parse_mode='Markdown')

        elif 'Añadir nueva posición en el escaparate' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese el nombre del nuevo producto', reply_markup=key)
            with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 2

        elif 'En formato de archivo' == message_text or 'En formato de texto' == message_text:
            if 'En formato de archivo' == message_text: 
                with open('data/Temp/' + str(chat_id) + 'good_format.txt', 'w', encoding='utf-8') as f: f.write('file')
                bot.send_message(chat_id, 'Ha seleccionado un producto en formato de archivo.\nAhora ingrese la cantidad mínima de producto que se puede comprar (es decir, no se puede comprar menos de este número)')
            elif 'En formato de texto' == message_text: 
                with open('data/Temp/' + str(chat_id) + 'good_format.txt', 'w', encoding='utf-8') as f: f.write('text')
                bot.send_message(chat_id, '¡Ha seleccionado un producto en formato de texto!\nAhora ingrese la cantidad mínima de producto que se puede comprar (es decir, no se puede comprar menos de este número)')
            with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 4

        elif 'Eliminar posición' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT name, price FROM goods;")
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            a = 0
            for name, price in cursor.fetchall():
                a += 1
                user_markup.row(name)
            if a == 0: 
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!', reply_markup=user_markup)
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿Qué posición desea eliminar? ¡Tenga cuidado, al eliminarla, todo el producto cargado se eliminará!', parse_mode='Markdown', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 6
            con.close()

        elif 'Cambiar descripción de posición' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT name, price FROM goods;")
            a = 0
            user_markup = telebot.types.ReplyKeyboardMarkup(True, True) 
            for name, price in cursor.fetchall():
                a += 1
                user_markup.row(name)
            if a == 0: bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!')
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿Para qué posición desea cambiar la descripción?', parse_mode='Markdown', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 7
            con.close()

        elif 'Cambiar precio' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT name, price FROM goods;")
            a = 0
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            for name, price in cursor.fetchall():
                a += 1
                user_markup.row(name)
            if a == 0:
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!', reply_markup=user_markup)
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿Para qué posición desea cambiar el precio?', parse_mode='Markdown', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 9
            con.close()

        
        elif 'Descripción adicional' == message_text:
            con = sqlite3.connect(files.main_db)
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
                with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 8
            con.close()

elif 'Cargar nuevo producto' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT name, price FROM goods;")
            a = 0
            user_markup = telebot.types.ReplyKeyboardMarkup(True, True) 
            for name, price in cursor.fetchall():
                a += 1
                user_markup.row(name)
            if a == 0: bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!')
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿De qué posición desea cargar productos?', parse_mode='Markdown', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 11
            con.close()

        elif 'Configuración de pago' == message_text:
            with shelve.open(files.payments_bd) as bd:
                da_paypal = bd.get('paypal', '❌')
                da_binance = bd.get('binance', '❌')
            
            if da_paypal == '❌' and da_binance == '❌': 
                da_all = ''
            elif da_paypal == '✅' and da_binance == '✅':
                da_paypal = '' 
                da_binance = ''
                da_all = '✅'
            else: 
                da_all = ''

            key = telebot.types.InlineKeyboardMarkup()
            b1 = telebot.types.InlineKeyboardButton(text='Pago a través de PayPal ' + da_paypal, callback_data='Pago a través de PayPal')
            b2 = telebot.types.InlineKeyboardButton(text='Pago a través de Binance ' + da_binance, callback_data='Pago a través de Binance')
            b3 = telebot.types.InlineKeyboardButton(text='Pago con PayPal y Binance ' + da_all, callback_data='Pago con PayPal y Binance')
            key.add(b1, b2)
            key.add(b3)
            bot.send_message(chat_id, 'Configuración de aceptación de pagos', reply_markup=key)

            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Añadir credenciales PayPal', 'Eliminar credenciales PayPal', 'Mostrar credenciales PayPal')
            user_markup.row('Añadir credenciales Binance', 'Eliminar credenciales Binance', 'Mostrar credenciales Binance')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, """*Puedes configurar PayPal y Binance para recibir pagos*.

**PayPal**: Necesitas Client ID y Client Secret de tu aplicación PayPal.
**Binance**: Necesitas API Key y API Secret de tu cuenta Binance.

Hay guías de configuración para ambos sistemas de pago disponibles al configurar cada método.""", reply_markup=user_markup, parse_mode='Markdown')

        # SECCIÓN DE CONFIGURACIÓN DE DESCUENTOS - CORREGIDA
        elif 'Configurar descuentos' == message_text:
            discount_config = dop.get_discount_config()
            
            status = "✅ Activados" if discount_config['enabled'] else "❌ Desactivados"
            fake_price_status = "✅ Sí" if discount_config['show_fake_price'] else "❌ No"
            
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Activar/Desactivar descuentos')
            user_markup.row('Cambiar texto descuento')
            user_markup.row('Cambiar multiplicador precio')
            user_markup.row('Mostrar/Ocultar precios tachados')
            user_markup.row('Vista previa catálogo')
            user_markup.row('Volver al menú principal')
            
            bot.send_message(chat_id, f"""🎯 **Configuración de Descuentos**

📊 **Estado actual:**
• Descuentos: {status}
• Texto: "{discount_config['text']}"
• Multiplicador: {discount_config['multiplier']}x
• Precios tachados: {fake_price_status}

**Cómo funciona:**
• El catálogo solo muestra el texto de descuento
• Los precios con descuento se ven al seleccionar cada producto
• El multiplicador controla qué tan alto es el precio "anterior"

Selecciona qué deseas cambiar:""", reply_markup=user_markup, parse_mode='Markdown')

        elif 'Activar/Desactivar descuentos' == message_text:
            discount_config = dop.get_discount_config()
            new_status = not discount_config['enabled']
            
            if dop.update_discount_config(enabled=new_status):
                status_text = "✅ activados" if new_status else "❌ desactivados"
                bot.send_message(chat_id, f'Descuentos {status_text} exitosamente')
            else:
                bot.send_message(chat_id, '❌ Error actualizando configuración')

        elif 'Cambiar texto descuento' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, """✏️ **Cambiar Texto de Descuento**

Este texto aparecerá en el catálogo principal.

**Ejemplos:**
• 🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥
• 💥 MEGA OFERTA 50% OFF 💥
• ⚡ PRECIOS ESPECIALES HOY ⚡
• 🎉 PROMOCIÓN LIMITADA 🎉

Envía el nuevo texto:""", reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 60

        elif 'Cambiar multiplicador precio' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, """🔢 **Cambiar Multiplicador de Precio**

Controla qué tan alto será el precio "anterior" tachado.

**Ejemplos:**
• 1.5 = precio anterior 50% más alto
• 2.0 = precio anterior 100% más alto (doble)
• 1.3 = precio anterior 30% más alto
• 2.5 = precio anterior 150% más alto

**Recomendado:** 1.5 a 2.0

Envía el nuevo multiplicador:""", reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 61

        elif 'Mostrar/Ocultar precios tachados' == message_text:
            discount_config = dop.get_discount_config()
            new_status = not discount_config['show_fake_price']
            
            if dop.update_discount_config(show_fake_price=new_status):
                if new_status:
                    bot.send_message(chat_id, '✅ Los precios tachados se mostrarán en los productos')
                else:
                    bot.send_message(chat_id, '❌ Los precios tachados se ocultarán (solo precio real)')
            else:
                bot.send_message(chat_id, '❌ Error actualizando configuración')

        elif 'Vista previa catálogo' == message_text:
            # Mostrar cómo se ve el catálogo actual
            catalog_preview = dop.get_productcatalog()
            if catalog_preview:
                bot.send_message(chat_id, f"👀 **Vista previa del catálogo:**\n\n{catalog_preview}", parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ No hay productos en el catálogo")

        elif 'Añadir credenciales PayPal' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Envíe el *Client ID* de PayPal.\n\nGuía para obtenerlo: https://developer.paypal.com/', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 14

        elif 'Eliminar credenciales PayPal' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT client_id FROM paypal_data;")
            a = 0
            for i in cursor.fetchall(): a += 1
            if a == 0: bot.send_message(chat_id, '¡No se han añadido credenciales de PayPal! No hay nada que eliminar')
            elif a > 0:
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Eliminar', callback_data = 'Eliminar credenciales PayPal'))
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
                bot.send_message(chat_id, 'Confirme o cancele la eliminación', reply_markup=key)
            con.close()

        elif 'Mostrar credenciales PayPal' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT client_id, client_secret, sandbox FROM paypal_data;")
            msg = ''
            for client_id, client_secret, sandbox in cursor.fetchall():
                mode = "Sandbox (Pruebas)" if sandbox else "Live (Producción)"
                msg += '*Client ID:* ' + str(client_id) + '\n*Client Secret:* ' + str(client_secret[:10]) + '...\n*Modo:* ' + mode + '\n\n'
            con.close()
            if msg: bot.send_message(chat_id, 'Credenciales PayPal:\n' + msg, parse_mode='Markdown')
            else: bot.send_message(chat_id, 'No hay credenciales PayPal configuradas')

        elif 'Añadir credenciales Binance' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese *API Key* de Binance\n\nGuía para obtenerlo: https://www.binance.com/en/support/faq/360002502072', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 17

        elif 'Eliminar credenciales Binance' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT api_key FROM binance_data;")
            a = 0
            for i in cursor.fetchall(): a += 1
            if a == 0: bot.send_message(chat_id, '¡No se han añadido credenciales de Binance! No hay nada que eliminar')
            elif a > 0:
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Eliminar', callback_data = 'Eliminar credenciales Binance'))
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
                bot.send_message(chat_id, 'Confirme o cancele la eliminación', reply_markup=key)
            con.close()

        elif 'Mostrar credenciales Binance' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT api_key, api_secret, merchant_id FROM binance_data;")
            msg = ''
            for api_key, api_secret, merchant_id in cursor.fetchall():
                msg += '*API Key:* ' + str(api_key[:10]) + '...\n*Secret Key:* ' + str(api_secret[:10]) + '...\n*Merchant ID:* ' + str(merchant_id) + '\n\n'
            con.close()
            if msg: bot.send_message(chat_id, 'Credenciales Binance:\n' + msg, parse_mode='Markdown')
            else: bot.send_message(chat_id, 'No hay credenciales Binance configuradas')

        elif 'Estadísticas' == message_text:
            amount_users = dop.user_loger()
            profit = dop.get_profit()
            buyers = dop.get_amountsbayers()
            lock = dop.get_amountblock()
            bot.send_message(chat_id, '*Estadísticas*\n\n*Número de usuarios que ingresaron al bot:* ' + str(amount_users) + '\n*Usuarios que bloquearon el bot:* ' + str(lock) + '\n*Ingresos por ventas:* $' + str(profit) + ' USD\n*Número de compradores:* ' + str(buyers), parse_mode='MarkDown')
            
        elif 'Boletín informativo' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('A todos los usuarios', 'Solo a los compradores')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Seleccione a qué grupo de usuarios desea enviar el boletín', reply_markup=user_markup)

        elif 'A todos los usuarios' == message_text or 'Solo a los compradores' == message_text:
            if 'A todos los usuarios' == message_text: 
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:  f.write('all\n')
                amount = dop.user_loger()
            elif 'Solo a los compradores' == message_text: 
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:  f.write('buyers\n')
                amount = dop.get_amountsbayers()
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '¿A cuántos usuarios desea enviar el boletín? Ingrese un número. Máximo posible ' + str(amount))
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 19

        elif 'Validar Compras' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Buscar compras')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, '**Panel de Validación**\n\nPara buscar compras de un usuario, selecciona la opción:', reply_markup=user_markup, parse_mode='Markdown')

        elif 'Buscar compras' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '**Buscar Compras**\n\nEnvía el ID de Telegram o username del usuario:', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 50
        
        elif 'Otras configuraciones' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            user_markup.row('Añadir nuevo admin', 'Eliminar admin')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Seleccione qué desea hacer', reply_markup=user_markup)

        elif 'Añadir nuevo admin' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text = 'Cancelar y volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese la ID del nuevo admin')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 21

        elif 'Eliminar admin' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False) 
            a = 0
            for admin_id in dop.get_adminlist(): 
                a += 1
                if int(admin_id) != config.admin_id: user_markup.row(str(admin_id))
            if a == 1: bot.send_message(chat_id, '¡Todavía no ha añadido admins!')
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, 'Seleccione la ID del admin que desea eliminar', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 22

        elif dop.get_sost(chat_id) is True:
            with shelve.open(files.sost_bd) as bd: sost_num = bd[str(chat_id)]
            
            if sost_num == 1:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f:  what_message = f.read()
                if what_message == 'start':
                    bot.send_message(chat_id, 'Nuevo mensaje de bienvenida añadido')
                    with shelve.open(files.bot_message_bd) as bd: bd['start'] = message_text
                elif what_message == 'after_buy':
                    bot.send_message(chat_id, 'Nuevo mensaje después de la compra añadido')
                    with shelve.open(files.bot_message_bd) as bd: bd['after_buy'] = message_text
                elif what_message == 'help':
                    bot.send_message(chat_id, 'Nuevo mensaje de ayuda añadido')
                    with shelve.open(files.bot_message_bd) as bd: bd['help'] = message_text
                elif what_message == 'userfalse':
                    bot.send_message(chat_id, '¡Nuevo mensaje si no hay nombre de usuario añadido!')
                    with shelve.open(files.bot_message_bd) as bd: bd['userfalse'] = message_text

                if 'start' in shelve.open(files.bot_message_bd): start = 'Cambiar'
                else: start = 'Añadir'
                if 'after_buy' in shelve.open(files.bot_message_bd): after_buy = 'Cambiar'
                else: after_buy = 'Añadir'
                if 'help' in shelve.open(files.bot_message_bd): help = 'Cambiar'
                else: help = 'Añadir'
                if 'userfalse' in shelve.open(files.bot_message_bd): userfalse = 'Cambiar'
                else: userfalse = 'Añadir'
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row(start + ' bienvenida al usuario')
                user_markup.row(after_buy + ' mensaje después de pagar el producto')
                user_markup.row(help + ' respuesta al comando help')
                user_markup.row(userfalse + ' mensaje si no hay nombre de usuario')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, message_text, reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

            elif sost_num == 2:
                with open('data/Temp/' + str(chat_id) + 'good_name.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                bot.send_message(chat_id, 'Ingrese la descripción para ' + message_text, reply_markup=key)
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 3

            elif sost_num == 3:
                with open('data/Temp/' + str(chat_id) + 'good_description.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
                user_markup.row('En formato de archivo', 'En formato de texto')
                bot.send_message(chat_id, '¿En qué formato se entregará el producto?\n¿*En formato de archivo*? *Por ejemplo*: archivos zip (logs), documentos txt (bases de datos)\n\n¿O *en formato de texto*? *Por ejemplo:* cuentas, etc.', reply_markup=user_markup, parse_mode='Markdown')
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

            elif sost_num == 4:
                try:
                    message = int(message_text)
                    if message >= 0:
                        with open('data/Temp/' + str(chat_id) + 'good_minimum.txt', 'w', encoding='utf-8') as f: f.write(str(message_text))
                        key = telebot.types.InlineKeyboardMarkup()
                        key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                        bot.send_message(chat_id, 'Cantidad mínima para comprar - ' + str(message_text) + '\nAhora ingrese el precio por unidad del producto en dólares USD.', reply_markup=key)
                        with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 5
                    else: bot.send_message(chat_id, '¡No se puede elegir un número negativo! Ingrese de nuevo.')
                except: bot.send_message(chat_id, '¡La cantidad mínima debe ingresarse estrictamente en números! Ingrese de nuevo.')

            elif sost_num == 5:
                try:
                    price = int(message_text)
                    with open('data/Temp/' + str(chat_id) + 'good_price.txt', 'w', encoding='utf-8') as f: f.write(str(message_text))
                    key = telebot.types.InlineKeyboardMarkup()
                    key.add(telebot.types.InlineKeyboardButton(text='Añadir producto a la tienda', callback_data='Añadir producto a la tienda'))
                    key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                    
                    with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f: name = f.read()
                    with open('data/Temp/' + str(chat_id) + 'good_description.txt', encoding='utf-8') as f: description = f.read()
                    with open('data/Temp/' + str(chat_id) + 'good_format.txt', encoding='utf-8') as f: format = f.read()
                    with open('data/Temp/' + str(chat_id) + 'good_minimum.txt', encoding='utf-8') as f: minimum = f.read()
                    with open('data/Temp/' + str(chat_id) + 'good_price.txt', encoding='utf-8') as f: price = f.read()
        
                    bot.send_message(chat_id, 'Ha decidido añadir el siguiente producto:\n*Nombre:* ' + name + '\n*Descripción:* ' + description + '\n*Formato del producto:* ' + format + '\n*Cantidad mínima para comprar:* ' + minimum + '\n*Precio por unidad:* $' + price + ' USD', reply_markup=key, parse_mode='MarkDown')
                    with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
                except: bot.send_message(chat_id, '¡El precio por unidad debe ingresarse estrictamente en números! Ingrese de nuevo.')

            elif sost_num == 6:
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute("SELECT description FROM goods WHERE name = " + "'" + message_text + "'")
                for i in cursor.fetchall():a += 1
                if a == 0:
                    bot.send_message(chat_id, '¡La posición seleccionada no se encontró! Selecciónela haciendo clic en el botón correspondiente.')
                else:
                    cursor.execute("DELETE FROM goods WHERE name = " + "'" + message_text + "';")
                    con.commit()
                    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                    user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                    user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                    user_markup.row('Volver al menú principal')
                    bot.send_message(chat_id, '¡Posición eliminada con éxito!', reply_markup=user_markup)
                    with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
                con.close()

            elif sost_num == 7:
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute("SELECT description FROM goods WHERE name = " + "'" + message_text + "';")
                for i in cursor.fetchall(): a += 1
            
                if a == 0: bot.send_message(chat_id, '¡No hay una posición con ese nombre!\n¡Seleccione de nuevo!')
                else: 
                    key = telebot.types.InlineKeyboardMarkup()
                    key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                    with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                    bot.send_message(chat_id, 'Ahora escriba la nueva descripción', reply_markup=key)
                    with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 8
                con.close()

            elif sost_num == 8:	
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: name = f.read()
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute("UPDATE goods SET description = '" + message_text + "' WHERE name = '" + name + "';")
                con.commit()
                con.close()
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¡Descripción cambiada con éxito!', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

            elif sost_num == 9:
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute("SELECT description FROM goods WHERE name = " + "'" + message_text + "';")
                for i in cursor.fetchall(): a += 1
                if a >= 1:
                    with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                    key = telebot.types.InlineKeyboardMarkup()
                    key.add(telebot.types.InlineKeyboardButton(text = 'Cancelar y volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
                    bot.send_message(chat_id, 'Ahora escriba el nuevo precio', reply_markup=key)
                    with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 10
                else: bot.send_message(chat_id, '¡No hay una posición con ese nombre!\n¡Seleccione de nuevo!')
                con.close()

            elif sost_num == 10:
                try:
                    message_text = int(message_text)
                    with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: name = f.read()
                    con = sqlite3.connect(files.main_db)
                    cursor = con.cursor()
                    cursor.execute("UPDATE goods SET price = '" + str(message_text) + "' WHERE name = '" + name + "';")
                    con.commit()
                    con.close()
                    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                    user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
                    user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
                    user_markup.row('Volver al menú principal')
                    bot.send_message(chat_id, '¡Precio cambiado con éxito!')
                    with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
                except: bot.send_message(chat_id, '¡El precio debe ser un número!\n¡Escriba el precio de nuevo!')

            elif sost_num == 11:
                if message_text in dop.get_goods():
                    with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                    key = telebot.types.InlineKeyboardMarkup()
                    key.add(telebot.types.InlineKeyboardButton(text = 'Detener carga', callback_data = 'Detener carga'))
                    key.add(telebot.types.InlineKeyboardButton(text = 'Cancelar y volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
                    type = dop.get_goodformat(message_text)
                    if type == 'file': 
                        bot.send_message(chat_id, '¡Cargue los archivos al bot!\n¡Cuando todos los archivos estén cargados, haga clic en detener carga!', reply_markup=key)
                        with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 12
                    elif type == 'text': 
                        bot.send_message(chat_id, '¡Cargue los datos necesarios en formato de texto!\nCada línea = un producto.\nDespués de enviar todo el texto al bot, haga clic en detener carga',reply_markup=key)
                        with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 13
                else: bot.send_message(chat_id, '¡Esa posición no está creada en el bot!')

            elif sost_num == 13:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: good_name = f.read()
                stored = dop.get_stored(good_name)
                with open(stored, 'a', encoding ='utf-8') as f: f.write(message_text + '\n')

            elif sost_num == 14:
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                bot.send_message(chat_id, 'Ahora ingrese el *Client Secret* de PayPal\n\nGuía para obtenerlo: https://developer.paypal.com/', parse_mode='Markdown')
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 15

            elif sost_num == 15:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: client_id = f.read()
                bot.send_message(chat_id, '¿Desea usar modo Sandbox (pruebas) o Live (producción)?\nEnvíe: "sandbox" para pruebas o "live" para producción')
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: 
                    f.write(client_id + '\n' + message_text)
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 16

            elif sost_num == 16:
                if message_text.lower() in ['sandbox', 'live']:
                    lines = []
                    with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: 
                        lines = f.readlines()
                    client_id = lines[0].strip()
                    client_secret = lines[1].strip()
                    sandbox = 1 if message_text.lower() == 'sandbox' else 0
                    
                    con = sqlite3.connect(files.main_db)
                    cursor = con.cursor()
                    cursor.execute("DELETE FROM paypal_data")
                    con.commit()
                    cursor.execute("INSERT INTO paypal_data VALUES(?, ?, ?)", (client_id, client_secret, sandbox))
                    con.commit()
                    con.close()
                    bot.send_message(chat_id, '¡Credenciales PayPal añadidas exitosamente!')
                    with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
                else:
                    bot.send_message(chat_id, 'Envíe "sandbox" o "live"')

            elif sost_num == 17:
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                bot.send_message(chat_id, 'Ingrese *API Secret* de Binance\n\nGuía para obtenerlo: https://www.binance.com/en/support/faq/360002502072', parse_mode='Markdown')
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 18

            elif sost_num == 18:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: api_key = f.read()
                bot.send_message(chat_id, 'Ingrese su *Merchant ID* de Binance (opcional, puede escribir "ninguno")')
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: 
                    f.write(api_key + '\n' + message_text)
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 19

            elif sost_num == 19:
                lines = []
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: 
                    lines = f.readlines()
                api_key = lines[0].strip()
                api_secret = lines[1].strip()
                merchant_id = message_text if message_text.lower() != 'ninguno' else ''
                
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute("DELETE FROM binance_data")
                con.commit()
                cursor.execute("INSERT INTO binance_data VALUES(?, ?, ?)", (api_key, api_secret, merchant_id))
                con.commit()
                con.close()
                bot.send_message(chat_id, '¡Credenciales Binance añadidas exitosamente!')
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

            elif sost_num == 21:
                dop.new_admin(message_text)
                user_markup = telebot.types.ReplyKeyboardMarkup(True, True) 
                user_markup.row('Añadir nuevo admin', 'Eliminar admin')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, 'Nuevo admin añadido con éxito', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

            elif sost_num == 22:
                with open(files.admins_list, encoding='utf-8') as f:
                    if str(message_text) in f.read():
                        dop.del_id(files.admins_list, message_text)
                        bot.send_message(chat_id, 'Admin eliminado con éxito de la lista')
                        with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
                    else: 
                        bot.send_message(chat_id, '¡La ID no se encontró en la lista de administradores! Seleccione la ID correcta.')
                        with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 22
                        
            elif sost_num == 50:  # Buscar compras
                # Intentar buscar por ID primero, luego por username
                try:
                    if message_text.isdigit():
                        result = purchase_validator.validate_purchase_by_user(user_id=int(message_text))
                    else:
                        result = purchase_validator.validate_purchase_by_user(username=message_text)
        
                    bot.send_message(chat_id, result, parse_mode='Markdown')
                except Exception as e:
                    bot.send_message(chat_id, f'❌ Error en la búsqueda: {e}')
    
                # Volver al menú
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('Buscar compras')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿Buscar más compras?', reply_markup=user_markup)
    
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

            # ESTADOS DE DESCUENTOS - CORREGIDOS
            elif sost_num == 60:  # Cambiar texto descuento
                if dop.update_discount_config(text=message_text):
                    bot.send_message(chat_id, f'✅ Texto de descuento cambiado a:\n"{message_text}"')
                else:
                    bot.send_message(chat_id, '❌ Error actualizando texto')
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

            elif sost_num == 61:  # Cambiar multiplicador
                try:
                    multiplier = float(message_text)
                    if 1.0 <= multiplier <= 5.0:
                        if dop.update_discount_config(multiplier=multiplier):
                            bot.send_message(chat_id, f'✅ Multiplicador cambiado a: {multiplier}x\n\nAhora el precio "anterior" será {int((multiplier-1)*100)}% más alto que el precio real.')
                        else:
                            bot.send_message(chat_id, '❌ Error actualizando multiplicador')
                    else:
                        bot.send_message(chat_id, '❌ El multiplicador debe estar entre 1.0 y 5.0')
                except:
                    bot.send_message(chat_id, '❌ El multiplicador debe ser un número válido')
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]



            elif sost_num == 30:  # Seleccionar producto para agregar multimedia
                if message_text in dop.get_products_without_media():
                    with open('data/Temp/' + str(chat_id) + 'media_product.txt', 'w', encoding='utf-8') as f:
                        f.write(message_text)
                    
                    key = telebot.types.InlineKeyboardMarkup()
                    key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
                    
                    bot.send_message(chat_id, 
                                    f'📤 **Agregar multimedia a:** {message_text}\n\n'
                                    f'Envía el archivo multimedia (foto, video, documento, audio, GIF)\n'
                                    f'💡 Tip: También puedes agregar un texto descriptivo junto al archivo',
                                    reply_markup=key, parse_mode='Markdown')
                    
                    with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 32
                else:
                    bot.send_message(chat_id, '❌ Producto no válido o ya tiene multimedia asignada')

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
                
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

def ad_inline(callback_data, chat_id, message_id):
    if 'Volver al menú principal de administración' == callback_data:
        if dop.get_sost(chat_id) is True:
            with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('Personalizar las respuestas del bot')
        user_markup.row('Configuración de surtido', 'Cargar nuevo producto')
        user_markup.row('Configuración de pago')
        user_markup.row('Configurar descuentos')
        user_markup.row('Estadísticas', 'Boletín informativo')
        user_markup.row('Validar Compras', 'Otras configuraciones')
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, '¡Has ingresado al panel de administración del bot!\nPara salir, presiona /start', reply_markup=user_markup)

    elif callback_data == 'Añadir producto a la tienda':
        with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f: name = f.read()
        with open('data/Temp/' + str(chat_id) + 'good_description.txt', encoding='utf-8') as f: description = f.read()
        with open('data/Temp/' + str(chat_id) + 'good_format.txt', encoding='utf-8') as f: format = f.read()
        with open('data/Temp/' + str(chat_id) + 'good_minimum.txt', encoding='utf-8') as f: minimum = f.read()
        with open('data/Temp/' + str(chat_id) + 'good_price.txt', encoding='utf-8') as f: price = f.read()

        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("INSERT INTO goods VALUES(?, ?, ?, ? , ?, ?, ?)", (name, description, format, minimum, price, 'data/goods/' + name + '.txt', ''))
        con.commit()
        con.close()
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
        user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
        user_markup.row('Volver al menú principal')
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, '¡Producto añadido con éxito!', reply_markup=user_markup)
        
        with open('data/goods/' + name + '.txt', 'w', encoding ='utf-8') as f: pass

    elif callback_data == 'Detener carga':
        good_name = open('data/Temp/' + str(chat_id) + '.txt', encoding ='utf-8').read()
        bot.delete_message(chat_id, message_id)
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT name, price FROM goods;")
        user_markup = telebot.types.ReplyKeyboardMarkup(True, True) 
        for name, price in cursor.fetchall(): user_markup.row(name)
        user_markup.row('Volver al menú principal')
        bot.send_message(chat_id, '¡Productos cargados con éxito! Ahora la cantidad de ' + good_name + ' es ' + str(dop.amount_of_goods(good_name)) + '\nPara volver al menú principal de administración presiona /adm', reply_markup=user_markup)
        
    elif callback_data == 'Pago a través de PayPal' or callback_data == 'Pago a través de Binance' or callback_data == 'Pago con PayPal y Binance':
        with shelve.open(files.payments_bd) as bd:
            if callback_data == 'Pago con PayPal y Binance':
                bd['paypal'] = '✅'
                bd['binance'] = '✅'
            elif callback_data == 'Pago a través de PayPal':
                bd['paypal'] = '✅'
                bd['binance'] = '❌'
            elif callback_data == 'Pago a través de Binance':
                bd['paypal'] = '❌'
                bd['binance'] = '✅'
            
            da_paypal = bd['paypal']
            da_binance = bd['binance']
            
            if da_paypal == '❌' and da_binance == '❌':
                da_paypal = '❌' 
                da_binance = '❌'
                da_all = ''
            elif da_paypal == '✅' and da_binance == '✅':
                da_paypal = '' 
                da_binance = ''
                da_all = '✅'
            else: da_all = ''

        key = telebot.types.InlineKeyboardMarkup()
        b1 = telebot.types.InlineKeyboardButton(text='Pago a través de PayPal ' + da_paypal, callback_data = 'Pago a través de PayPal')
        b2 = telebot.types.InlineKeyboardButton(text='Pago a través de Binance ' + da_binance, callback_data = 'Pago a través de Binance')
        b3 = telebot.types.InlineKeyboardButton(text='Pago con PayPal y Binance ' + da_all, callback_data = 'Pago con PayPal y Binance')
        key.add(b1, b2)
        key.add(b3)
        try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='Configuración de pagos actualizada', reply_markup=key)
        except: pass

    elif callback_data == 'Eliminar credenciales PayPal':
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("DELETE FROM paypal_data")
        con.commit()
        con.close()
        try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='¡Credenciales PayPal eliminadas con éxito!')
        except: pass

    elif callback_data == 'Eliminar credenciales Binance':
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("DELETE FROM binance_data")
        con.commit()
        con.close()
        try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='¡Credenciales Binance eliminadas con éxito!')
        except: pass


def new_files(document_id, chat_id):
    with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: good_name = f.read()
    stored = dop.get_stored(good_name)
    with open(stored, 'a', encoding='utf-8') as f: f.write(document_id + '\n')

def handle_multimedia(message):
    """Manejar archivos multimedia enviados por admin"""
    chat_id = message.chat.id
    
    try:
        with shelve.open(files.sost_bd) as bd:
            if str(chat_id) in bd and bd[str(chat_id)] == 32:
                with open('data/Temp/' + str(chat_id) + 'media_product.txt', 'r', encoding='utf-8') as f:
                    product_name = f.read()
                
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
                    if dop.save_product_media(product_name, file_id, media_type, caption):
                        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                        user_markup.row('🎬 Multimedia productos')
                        user_markup.row('Volver al menú principal')
                        
                        media_names = {
                            'photo': '📸 Imagen',
                            'video': '🎥 Video',
                            'document': '📄 Documento', 
                            'audio': '🎵 Audio',
                            'animation': '🎬 GIF'
                        }
                        
                        bot.send_message(chat_id, 
                                       f'✅ {media_names.get(media_type, "Archivo")} agregado al producto: {product_name}',
                                       reply_markup=user_markup)
                        
                        del bd[str(chat_id)]
                    else:
                        bot.send_message(chat_id, '❌ Error guardando multimedia')
                else:
                    bot.send_message(chat_id, '❌ Tipo de archivo no soportado. Envía: foto, video, documento, audio o GIF')
    except:
        pass
