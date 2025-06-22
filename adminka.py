import telebot, sqlite3, shelve, os
import config, dop, files

bot = telebot.TeleBot(config.token)

def in_adminka(chat_id, message_text, username, name_user):
    if chat_id in dop.get_adminlist():
        if message_text == 'Volver al menú principal' or message_text == '/adm':
            if dop.get_sost(chat_id) is True: 
                with shelve.open(files.sost_bd) as bd: 
                    del bd[str(chat_id)]
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('💬 Respuestas')
            user_markup.row('📦 Surtido', '➕ Producto')
            user_markup.row('💰 Pagos')
            user_markup.row('📊 Stats', '📣 Difusión')
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
            if a == 0: 
                goodz = '¡No se han creado posiciones todavía!'
            bot.send_message(chat_id, goodz, reply_markup=user_markup, parse_mode='MarkDown')

        elif 'Añadir nueva posición en el escaparate' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese el nombre del nuevo producto', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 2

        elif 'Eliminar posición' == message_text:
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
                bot.send_message(chat_id, '¿Qué posición desea eliminar?', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 6
            con.close()

        elif 'Cambiar descripción de posición' == message_text:
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
                bot.send_message(chat_id, '¿Para qué posición desea cambiar la descripción?', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 7
            con.close()

        elif 'Cambiar precio' == message_text:
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
                bot.send_message(chat_id, '¿Para qué posición desea cambiar el precio?', parse_mode='Markdown', reply_markup=user_markup)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 9
            con.close()

        elif '📝 Descripción adicional' == message_text:
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
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 28
            con.close()

        elif '🎬 Multimedia productos' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('📤 Agregar multimedia', '🗑️ Eliminar multimedia')
            user_markup.row('📋 Ver productos con multimedia')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, '🎬 **Gestión de Multimedia**\n\nSelecciona una opción:', reply_markup=user_markup, parse_mode='Markdown')

        elif '📤 Agregar multimedia' == message_text:
            products_without_media = dop.get_products_without_media()
            if not products_without_media:
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('🎬 Multimedia productos')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '✅ Todos los productos ya tienen multimedia asignada', reply_markup=user_markup)
            else:
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                for product in products_without_media:
                    user_markup.row(product)
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '📤 **Agregar Multimedia**\n\n¿A qué producto deseas agregar multimedia?', reply_markup=user_markup, parse_mode='Markdown')
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
            if not products_with_media:
                response = 'ℹ️ No hay productos con multimedia asignada'
            else:
                response = '📋 **Productos con Multimedia:**\n\n'
                for product, media_type in products_with_media:
                    media_emoji = {'photo': '📸', 'video': '🎥', 'document': '📄', 'audio': '🎵'}.get(media_type, '📎')
                    response += f"{media_emoji} **{product}** - {media_type}\n"
            
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('🎬 Multimedia productos')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, response, reply_markup=user_markup, parse_mode='Markdown')

        elif '➕ Producto' == message_text:
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
            if a == 0: 
                bot.send_message(chat_id, '¡No se ha creado ninguna posición todavía!')
            else:
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '¿De qué posición desea cargar productos?', reply_markup=user_markup, parse_mode='MarkDown')
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 10
            con.close()

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
            user_markup.row('A todos los usuarios', 'Solo a los compradores')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Seleccione a qué grupo de usuarios desea enviar el boletín', reply_markup=user_markup)

        elif 'A todos los usuarios' == message_text or 'Solo a los compradores' == message_text:
            if 'A todos los usuarios' == message_text: 
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:  
                    f.write('all\n')
                amount = dop.user_loger()
            elif 'Solo a los compradores' == message_text: 
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:  
                    f.write('buyers\n')
                amount = dop.get_amountsbayers()
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '¿A cuántos usuarios desea enviar el boletín? Ingrese un número. Máximo posible ' + str(amount))
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 19

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
    if dop.get_sost(chat_id) is True:
        with shelve.open(files.sost_bd) as bd: 
            sost_num = bd[str(chat_id)]
        
        if sost_num == 1:
            with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: 
                message = f.read()
            if dop.save_message(message, message_text):
                user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
                user_markup.row('💬 Respuestas')
                user_markup.row('📦 Surtido', '➕ Producto')
                user_markup.row('💰 Pagos')
                user_markup.row('📊 Stats', '📣 Difusión')
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
            user_markup.row('En formato de texto')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Ahora seleccione el formato del producto', reply_markup=user_markup)
            with shelve.open(files.sost_bd) as bd: 
                bd[str(chat_id)] = 4

        elif sost_num == 4:
            with open('data/Temp/' + str(chat_id) + 'good_format.txt', 'w', encoding='utf-8') as f: 
                f.write(message_text)
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
            key.add(telebot.types.InlineKeyboardButton(text='Añadir producto a la tienda', callback_data='Añadir producto a la tienda'))
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            
            with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f: 
                name = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_description.txt', encoding='utf-8') as f: 
                description = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_format.txt', encoding='utf-8') as f: 
                format_type = f.read()
            with open('data/Temp/' + str(chat_id) + 'good_minimum.txt', encoding='utf-8') as f: 
                minimum = f.read()
            
            bot.send_message(chat_id, f'*Resumen del producto:*\n\n*Nombre:* {name}\n*Descripción:* {description}\n*Formato:* {format_type}\n*Cantidad mínima:* {minimum}\n*Precio:* ${message_text} USD', parse_mode='MarkDown', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: 
                del bd[str(chat_id)]

        elif sost_num == 6:
            con = sqlite3.connect(files.main_db)
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
            con.close()

        elif sost_num == 7:
            con = sqlite3.connect(files.main_db)
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
            con.close()

        elif sost_num == 8:
            with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: 
                name_good = f.read()
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("UPDATE goods SET description = ? WHERE name = ?", (message_text, name_good))
            con.commit()
            con.close()
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
            with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: 
                name_good = f.read()
            try:
                price = int(message_text)
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute("UPDATE goods SET price = ? WHERE name = ?", (price, name_good))
                con.commit()
                con.close()
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
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                bot.send_message(chat_id, f'Contenido actual del archivo {message_text}:\n\n{content}\n\nEnvíe el nuevo contenido (cada línea será un producto):')
                with open('data/Temp/' + str(chat_id) + 'upload_file.txt', 'w', encoding='utf-8') as f: 
                    f.write(message_text)
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 11
            else:
                bot.send_message(chat_id, 'Error: archivo no encontrado')

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
                
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute("INSERT OR REPLACE INTO paypal_data VALUES(?, ?, ?)", (client_id, message_text, 1))
                con.commit()
                con.close()
                
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
                
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute("INSERT OR REPLACE INTO binance_data VALUES(?, ?, ?)", (api_key, api_secret, message_text))
                con.commit()
                con.close()
                
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
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            a = 0
            cursor.execute("SELECT name FROM goods WHERE name = ? COLLATE NOCASE", (message_text,))
            for i in cursor.fetchall():
                a += 1
            if a == 0:
                bot.send_message(chat_id, '¡La posición seleccionada no se encontró! Selecciónela haciendo clic en el botón correspondiente.')
            else:
                # Mostrar descripción adicional actual
                cursor.execute("SELECT additional_description FROM goods WHERE name = ? COLLATE NOCASE", (message_text,))
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
            con.close()

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
                
                with shelve.open(files.sost_bd) as bd: 
                    bd[str(chat_id)] = 32
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
        user_markup.row('⚙️ Otros')
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, '¡Has ingresado al panel de administración del bot!\nPara salir, presiona /start', reply_markup=user_markup)

    elif callback_data == 'Añadir producto a la tienda':
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

        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            INSERT INTO goods (name, description, format, minimum, price, stored, additional_description, media_file_id, media_type, media_caption)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, format_type, minimum, price, 'data/goods/' + name + '.txt', '', None, None, None))
        con.commit()
        con.close()
        
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
