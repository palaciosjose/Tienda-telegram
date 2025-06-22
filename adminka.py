import telebot, sqlite3, shelve
import config, dop, files

bot = telebot.TeleBot(config.token)

def in_adminka(chat_id, message_text, username, name_user):
    if chat_id in dop.get_adminlist():
        if message_text == 'Volver al menú principal' or message_text == '/adm':
            if dop.get_sost(chat_id) is True: 
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Personalizar las respuestas del bot')
            user_markup.row('Configuración de surtido', 'Subir un nuevo producto')
            user_markup.row('Configuración de pago')
            user_markup.row('Estadísticas', 'Boletín informativo')
            user_markup.row('Otras configuraciones')
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
            user_markup.row('Volver al menú principal')

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            goodz = 'Productos creados:\n\n'
            a = 0
            cursor.execute("SELECT name, description, format, minimum, price, stored FROM goods;") 
            for name, description, format, minimum, price, stored in cursor.fetchall():
                a += 1
                amount = dop.amount_of_goods(name)
                goodz += '*Nombre:* ' + name + '\n*Descripción:* ' + description + '\n*Formato del producto:* ' + format + '\n*Cantidad mínima para comprar:* ' + str(minimum) + '\n*Precio por unidad:* ' + str(price) + ' rub' + '\n*Unidades restantes:* ' + str(amount) + '\n\n'
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
                da_qiwi = bd['qiwi']
                da_btc = bd['btc']
            if da_qiwi == '❌' and da_btc == '❌': 
                da_all = ''
            elif da_qiwi == '✅' and da_btc == '✅':
                da_qiwi = '' 
                da_btc = ''
                da_all = '✅'
            else: da_all = ''

            key = telebot.types.InlineKeyboardMarkup()
            b1 = telebot.types.InlineKeyboardButton(text='Pago a través de Qiwi ' + da_qiwi, callback_data='Pago a través de qiwi')
            b2 = telebot.types.InlineKeyboardButton(text='Pago a través de Coinbase ' + da_btc, callback_data='Pago a través de coinbase')
            b3 = telebot.types.InlineKeyboardButton(text='Pago con rublos y bitcoins ' + da_all, callback_data='Pago con rublos y bitcoins')
            key.add(b1, b2)
            key.add(b3)
            bot.send_message(chat_id, 'Configuración de aceptación de pagos', reply_markup=key)

            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Añadir nueva billetera Qiwi', 'Eliminar billetera Qiwi', 'Mostrar billeteras Qiwi añadidas')
            user_markup.row('Añadir/Reemplazar datos de intercambio', 'Eliminar datos de intercambio', 'Mostrar claves de intercambio añadidas')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, """*Puedes añadir un número ilimitado de billeteras QIWI*.
Si la billetera utilizada es bloqueada de repente, recibirás una notificación al respecto y el dinero se aceptará en otra billetera.

Los bitcoins se pueden aceptar en el intercambio solo en una cuenta.

Hay guías de configuración para ambos sistemas de pago, puedes obtenerlas al añadir el sistema de pago correspondiente""", reply_markup=user_markup, parse_mode='Markdown')

        elif 'Añadir nueva billetera Qiwi' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Envíe el *número* de la billetera Qiwi. Ingrese *sin el signo más*. Por ejemplo, 7946 o 3756\n\nNo es posible verificar la validez del número, ¡así que ingréselo sin errores! De lo contrario, el dinero no se acreditará en su billetera', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 14

        elif 'Eliminar billetera Qiwi' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Envíe el número de la billetera Qiwi que desea eliminar de la base de datos', reply_markup=key)
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 16

        elif 'Mostrar billeteras Qiwi añadidas' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT number, token FROM qiwi_data;")
            msg = ''
            for number, token in cursor.fetchall():
                msg += '*Número:* ' + str(number) + '\n*Token:* ' + str(token) + '\n\n'
            bot.send_message(chat_id, 'Lista de billeteras en la base:\n' + msg, parse_mode='MarkDown')
            con.close()

        elif 'Añadir/Reemplazar datos de intercambio' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, 'Ingrese *API Key* del intercambio *coinbase*\n\nGuía para obtenerlo: https://telegra.ph/Token-coinbase-08-31', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 17

        elif 'Eliminar datos de intercambio' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT api_key, private_key FROM coinbase_data;")
            a = 0
            for i in cursor.fetchall(): a += 1
            if a == 0: bot.send_message(chat_id, '¡No se han añadido claves de intercambio! No hay nada que eliminar')
            elif a > 0:
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Eliminar', callback_data = 'Eliminar claves de la base de datos'))
                key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
                bot.send_message(chat_id, 'Confirme o cancele la eliminación', reply_markup=key)
            con.close()

        elif 'Mostrar claves de intercambio añadidas' == message_text:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT api_key, private_key FROM coinbase_data;")
            msg = ''
            for api_key, private_key in cursor.fetchall():
                msg += '*API Key:* ' + str(api_key) + '\n*Secret Key:* ' + str(private_key)
            con.close()
            bot.send_message(chat_id, 'Lista de claves:\n' + msg, parse_mode='Markdown')

        elif 'Estadísticas' == message_text:
            amount_users = dop.user_loger() #obtener el número de usuarios
            profit = dop.get_profit() #obtener los ingresos
            buyers = dop.get_amountsbayers() #obtener el número de compradores
            lock = dop.get_amountblock() #obtener el número de usuarios que bloquearon el bot
            bot.send_message(chat_id, '*Estadísticas*\n\n*Número de usuarios que ingresaron al bot:* ' + str(amount_users) + '\n*Usuarios que bloquearon el bot:* ' + str(lock) + '\n*Ingresos por ventas:* ' + str(profit) + ' ₽\n*Número de compradores:* ' + str(buyers), parse_mode='MarkDown')
            
        elif 'Boletín informativo' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('A todos los usuarios', 'Solo a los compradores')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Seleccione a qué grupo de usuarios desea enviar el boletín', reply_markup=user_markup)

        elif 'A todos los usuarios' == message_text or 'Solo a los compradores' == message_text:
            if 'A todos los usuarios' == message_text: 
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:  f.write('all\n')
                amount = dop.user_loger() #obtener el número de usuarios
            elif 'Solo a los compradores' == message_text: 
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:  f.write('buyers\n')
                amount = dop.get_amountsbayers() #obtener el número de compradores
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '¿A cuántos usuarios desea enviar el boletín? Ingrese un número. Máximo posible ' + str(amount))
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 19

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
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f:  what_message = f.read()#se obtiene el mensaje cuya respuesta debe ser cambiada
                if what_message == 'start':
                    bot.send_message(chat_id, 'Nuevo mensaje de bienvenida añadido')
                    shelve.open(files.bot_message_bd)['start'] = message_text
                elif what_message == 'after_buy':
                    bot.send_message(chat_id, 'Nuevo mensaje después de la compra añadido')
                    shelve.open(files.bot_message_bd)['after_buy'] = message_text
                elif what_message == 'help':
                    bot.send_message(chat_id, 'Nuevo mensaje de ayuda añadido')
                    shelve.open(files.bot_message_bd)['help'] = message_text
                elif what_message == 'userfalse':
                    bot.send_message(chat_id, '¡Nuevo mensaje si no hay nombre de usuario añadido!')
                    shelve.open(files.bot_message_bd)['userfalse'] = message_text

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
                        bot.send_message(chat_id, 'Cantidad mínima para comprar - ' + str(message_text) + '\nAhora ingrese el precio por unidad del producto en rublos.\nSi decide aceptar pagos en BTC, la cantidad se convertirá automáticamente a satoshis', reply_markup=key)
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
        
                    bot.send_message(chat_id, 'Ha decidido añadir el siguiente producto:\n*Nombre:* ' + name + '\n*Descripción:* ' + description + '\n*Formato del producto:* ' + format + '\n*Cantidad mínima para comprar:* ' + minimum + '\n*Precio por unidad:* ' + price + ' rub', reply_markup=key, parse_mode='MarkDown')
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
                else: bot.send_message(chat_id, '¡No hay una posición con ese nombre!\n¡Seleccione de nuevo!', reply_markup=user_markup)
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
                try:
                    message = int(message_text)
                    con = sqlite3.connect(files.main_db)
                    cursor = con.cursor()
                    cursor.execute("SELECT number, token FROM qiwi_data WHERE number = " + str(message_text) + ";")
                    if len(cursor.fetchall()) > 0: bot.send_message(chat_id,'¡Ese número ya existe en la base de datos!')
                    elif 15 >= len(message_text) >= 10:
                        with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                        bot.send_message(chat_id, 'Ahora ingrese el token\n\n*Guía para obtener el token - *https://telegra.ph/Kak-poluchit-token-ot-kivi-koshelka-08-31', parse_mode='Markdown')
                        with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 15
                    else: bot.send_message(chat_id, '¡Ha ingresado un número incorrecto!')
                    con.close()
                except:
                    bot.send_message(chat_id, '¡El número no debe contener letras!\n\nEnvíe el *número* de la billetera Qiwi. Ingrese *sin el signo más*. Por ejemplo, 7904 o 3757', parse_mode='Markdown')

            elif sost_num == 15:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: phone = f.read()
                if dop.check_qiwi_valid(phone, message_text) is False:
                    key = telebot.types.InlineKeyboardMarkup()
                    key.add(telebot.types.InlineKeyboardButton(text = 'Volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
                    bot.send_message(chat_id, '¡Los datos ingresados no son válidos! O no ha otorgado los privilegios necesarios.\n\nIngrese el número de Qiwi de nuevo, o regrese al menú principal', reply_markup=key)
                    with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 14

                elif dop.check_qiwi_valid(phone, message_text) is True:
                    con = sqlite3.connect(files.main_db)
                    cursor = con.cursor()
                    cursor.execute("INSERT INTO qiwi_data VALUES(?, ?)", (phone, message_text))
                    con.commit()
                    cursor.close()
                    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                    user_markup.row('Añadir nueva billetera Qiwi', 'Eliminar billetera Qiwi', 'Mostrar billeteras Qiwi añadidas')
                    user_markup.row('Añadir/Reemplazar datos de intercambio', 'Eliminar datos de intercambio', 'Mostrar claves de intercambio añadidas')
                    user_markup.row('Volver al menú principal')
                    bot.send_message(chat_id, '*Token* válido\n¡Los datos se han añadido a la base de datos! El dinero se acreditará a la cuenta de esta billetera', parse_mode='Markdown', reply_markup=user_markup)
                    with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]

            elif sost_num == 16:
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute("SELECT number, token FROM qiwi_data WHERE number = " + str(message_text) + ";")
                a = 0
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    key = telebot.types.InlineKeyboardMarkup()
                    key.add(telebot.types.InlineKeyboardButton(text='Volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                    bot.send_message(chat_id, '¡Número `' + message_text + '` no encontrado en la base de datos!', reply_markup=key, parse_mode='Markdown')
                elif a > 0:
                    cursor.execute("DELETE FROM qiwi_data WHERE number = '" + str(message_text) + "';")
                    con.commit()
                    bot.send_message(chat_id, '¡Billetera Qiwi eliminada con éxito de la base de datos!')
                con.close()

            elif sost_num == 17:
                with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f: f.write(message_text)
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text = 'Volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
                bot.send_message(chat_id, 'Ingrese *API Secret*\n\nGuía para obtenerlo: https://telegra.ph/Token-coinbase-08-31', reply_markup=key, parse_mode='Markdown')
                with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 18

            elif sost_num == 18:
                with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: api_key = f.read()
                if dop.check_coinbase_valid(api_key, message_text) is True:
                    con = sqlite3.connect(files.main_db)
                    cursor = con.cursor()
                    cursor.execute("DELETE FROM coinbase_data")
                    con.commit()
                    cursor.execute("INSERT INTO coinbase_data VALUES(?, ?)", (api_key, message_text))
                    con.commit()
                    con.close()
                    bot.send_message(chat_id, '¡Datos *válidos* y añadidos a la base de datos!', parse_mode='Markdown')
                    with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
                elif dop.check_coinbase_valid(api_key, message_text) is False:
                    key = telebot.types.InlineKeyboardMarkup()
                    key.add(telebot.types.InlineKeyboardButton(text = 'Volver al menú principal de administración', callback_data = 'Volver al menú principal de administración'))
                    bot.send_message(chat_id, '¡Datos no válidos!\n\nIngrese *API key* del intercambio *coinbase* o regrese al menú principal\n\nGuía para obtenerlo: https://telegra.ph/Token-coinbase-08-31', reply_markup=key, parse_mode='MarkDown')
                    with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 17

            elif sost_num == 19:
                try:
                    if int(message_text) > 0:
                        with open('data/Temp/' + str(chat_id) + '.txt', 'a', encoding='utf-8') as f: f.write(message_text)
                        key = telebot.types.InlineKeyboardMarkup()
                        key.add(telebot.types.InlineKeyboardButton(text='Cancelar y volver al menú principal de administración', callback_data='Volver al menú principal de administración'))
                        group = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 0)
                        if group == 'all': group = 'a todos'
                        elif group == 'buyers': group = 'solo a compradores'
                        bot.send_message(chat_id, 'Ha seleccionado el boletín ' + group + '\nA ' + message_text + ' usuarios\nAhora ingrese el texto del boletín. Se enviará exactamente como lo envíe.')
                        with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 20
                    elif int(message_text) < 1:
                        bot.send_message(chat_id, '¡Para el boletín, seleccione solo un número positivo! Ingrese de nuevo.')
                        with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 19
                except: bot.send_message(chat_id, '¡La cantidad de usuarios para el boletín debe ingresarse como un número! Ingrese de nuevo.')

            elif sost_num == 20:
                group = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 0)
                amount_users = dop.read_my_line('data/Temp/' + str(chat_id) + '.txt', 1)
                message_text = dop.rasl(group, amount_users, message_text) #se obtienen los resultados del boletín

                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('A todos los usuarios', 'Solo a los compradores')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, message_text, reply_markup=user_markup)
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
                        dop. del_id(files.admins_list, message_text)
                        bot.send_message(chat_id, 'Admin eliminado con éxito de la lista')
                        with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
                    else: 
                        bot.send_message(chat_id, '¡La ID no se encontró en la lista de administradores! Seleccione la ID correcta.')
                        with shelve.open(files.sost_bd) as bd : bd[str(chat_id)] = 22

def ad_inline(callback_data, chat_id, message_id):
    if 'Volver al menú principal de administración' == callback_data:
        if dop.get_sost(chat_id) is True:
            with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('Personalizar las respuestas del bot')
        user_markup.row('Configuración de surtido', 'Subir un nuevo producto')
        user_markup.row('Configuración de pago')
        user_markup.row('Estadísticas', 'Boletín informativo')
        user_markup.row('Otras configuraciones')
        bot.delete_message(chat_id, message_id) #el mensaje antiguo es eliminado
        bot.send_message(chat_id, '¡Has ingresado al panel de administración del bot!\nPara salir, presiona /start', reply_markup=user_markup)

    elif callback_data == 'Añadir producto a la tienda':
        with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f: name = f.read()
        with open('data/Temp/' + str(chat_id) + 'good_description.txt', encoding='utf-8') as f: description = f.read()
        with open('data/Temp/' + str(chat_id) + 'good_format.txt', encoding='utf-8') as f: format = f.read()
        with open('data/Temp/' + str(chat_id) + 'good_minimum.txt', encoding='utf-8') as f: minimum = f.read()
        with open('data/Temp/' + str(chat_id) + 'good_price.txt', encoding='utf-8') as f: price = f.read()

        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("INSERT INTO goods VALUES(?, ?, ?, ? , ?, ?)", (name, description, format, minimum, price, 'data/goods/' + name + '.txt'))
        con.commit()
        con.close()
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('Añadir nueva posición en el escaparate', 'Eliminar posición')
        user_markup.row('Cambiar descripción de posición', 'Cambiar precio')
        user_markup.row('Volver al menú principal')
        bot.delete_message(chat_id, message_id) #el mensaje antiguo es eliminado
        bot.send_message(chat_id, '¡Producto añadido con éxito!', reply_markup=user_markup)
        
        with open('data/goods/' + name + '.txt', 'w', encoding ='utf-8') as f: pass #se crea el archivo para el producto

    elif callback_data == 'Detener carga':
        good_name = open('data/Temp/' + str(chat_id) + '.txt', encoding ='utf-8').read()
        bot.delete_message(chat_id, message_id) #el mensaje antiguo es eliminado
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT name, price FROM goods;")
        user_markup = telebot.types.ReplyKeyboardMarkup(True, True) 
        for name, price in cursor.fetchall(): user_markup.row(name)
        user_markup.row('Volver al menú principal')
        bot.send_message(chat_id, '¡Productos cargados con éxito! Ahora la cantidad de ' + good_name + ' es ' + str(dop.amount_of_goods(good_name)) + '\nPara volver al menú principal de administración presiona /adm', reply_markup=user_markup)
        
    elif callback_data == 'Pago a través de qiwi' or callback_data == 'Pago a través de coinbase' or callback_data == 'Pago con rublos y bitcoins':
        with shelve.open(files.payments_bd) as bd:
            if callback_data =='Pago con rublos y bitcoins':
                bd['qiwi'] = '✅'
                bd['btc'] = '✅'
            elif callback_data == 'Pago a través de qiwi':
                bd['qiwi'] = '✅'
                bd['btc'] = '❌'
            elif callback_data == 'Pago a través de coinbase':
                bd['qiwi'] = '❌'
                bd['btc'] = '✅'
            da_qiwi = bd['qiwi']
            da_btc = bd['btc']
            
            if da_qiwi == '❌' and da_btc == '❌':
                da_qiwi = '❌' 
                da_btc = '❌'
                da_all = ''
            elif da_qiwi == '✅' and da_btc == '✅':
                da_qiwi = '' 
                da_btc = ''
                da_all = '✅'
            else: da_all = ''

        key = telebot.types.InlineKeyboardMarkup()
        b1 = telebot.types.InlineKeyboardButton(text='Pago a través de qiwi ' + da_qiwi, callback_data = 'Pago a través de qiwi')
        b2 = telebot.types.InlineKeyboardButton(text='Pago a través de coinbase' + da_btc, callback_data = 'Pago a través de coinbase')
        b3 = telebot.types.InlineKeyboardButton(text='Pago con rublos y bitcoins' + da_all, callback_data = 'Pago con rublos y bitcoins')
        key.add(b1, b2)
        key.add(b3)
        try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='Configurar', reply_markup=key)
        except: pass

    elif callback_data == 'Eliminar claves de la base de datos':
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("DELETE FROM coinbase_data")
        con.commit()
        con.close()
        try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='¡Claves eliminadas con éxito de la base de datos!')
        except: pass

def new_files(document_id, chat_id):
    with open('data/Temp/' + str(chat_id) + '.txt', encoding='utf-8') as f: good_name = f.read()
    stored = dop.get_stored(good_name)
    with open(stored, 'a', encoding='utf-8') as f: f.write(document_id + '\n')