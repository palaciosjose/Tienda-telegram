import telebot, shelve, sqlite3
import config, dop, payments, adminka, files

print("DEBUG: main.py - Script iniciado.") # Línea de depuración 1

bot = telebot.TeleBot(config.token)
in_admin = []

print("DEBUG: main.py - Bot inicializado.") # Línea de depuración 2

@bot.message_handler(content_types=["text"])
def message_send(message):
    print(f"DEBUG: message_send - Mensaje recibido: {message.text} de {message.chat.id}")
    if '/start' == message.text:
        print(f"DEBUG: /start handler - Procesando comando /start.")
        print(f"DEBUG: /start handler - Chat ID: {message.chat.id}, Admin ID: {config.admin_id}")
        print(f"DEBUG: /start handler - User has username: {message.chat.username}")

        if message.chat.username:
            print(f"DEBUG: /start handler - Path: User with username.")
            # Llama a it_first antes de las comprobaciones condicionales para debug
            is_first_user = dop.it_first(message.chat.id)
            is_admin_user = (message.chat.id == config.admin_id)
            admin_list = dop.get_adminlist()
            is_in_admin_list = (message.chat.id in admin_list)
            
            print(f"DEBUG: /start handler - is_first_user: {is_first_user}, is_admin_user: {is_admin_user}, is_in_admin_list: {is_in_admin_list}")

            if dop.get_sost(message.chat.id) is True: 
                print(f"DEBUG: /start handler - get_sost is True for {message.chat.id}, deleting state.")
                with shelve.open(files.sost_bd) as bd: del bd[str(message.chat.id)]
            if message.chat.id in in_admin:
                print(f"DEBUG: /start handler - User {message.chat.id} in in_admin list, removing.")
                in_admin.remove(message.chat.id)
            
            if is_admin_user and is_first_user:
                print(f"DEBUG: /start handler - Admin first launch branch triggered for {message.chat.id}. Adding to in_admin.")
                in_admin.append(message.chat.id)
            elif is_first_user and not is_in_admin_list:
                print(f"DEBUG: /start handler - First time non-admin user branch triggered for {message.chat.id}. Sending 'Bot no listo'.")
                bot.send_message(message.chat.id, 'Бот ещё не готов к работе!\nЕсли вы являетесь его администратором, то войдите из под аккаунту, id которого указали при запуске бота y подготовьте его к работе!')
            elif dop.check_message('start') is True:
                print(f"DEBUG: /start handler - Welcome message exists. Sending start message.")
                key = telebot.types.InlineKeyboardMarkup()
                key.add(telebot.types.InlineKeyboardButton(text='Перейти к каталогу товаров', callback_data='Перейти к катаálogo товаров'))
                with shelve.open(files.bot_message_bd) as bd: start_message = bd['start']
                start_message = start_message.replace('username', message.chat.username)
                start_message = start_message.replace('name', message.from_user.first_name)
                bot.send_message(message.chat.id, start_message, reply_markup=key)	
            elif dop.check_message('start') is False and is_in_admin_list:
                print(f"DEBUG: /start handler - Admin, no welcome message set. Sending setup message.")
                bot.send_message(message.chat.id, 'Приветствие ещё не добавлено!\nЧтобы его добавить, перейдите в админку по команde /adm y *настройте ответы бота*', parse_mode='Markdown')
            else:
                print(f"DEBUG: /start handler - Fallback path for user: {message.chat.id}. No specific condition met.")


            dop.user_loger(chat_id=message.chat.id) #логгирование юзеровs
            print(f"DEBUG: /start handler - User logged: {message.chat.id}")

        elif not message.chat.username:
            print(f"DEBUG: /start handler - Path: User WITHOUT username. Sending userfalse message.")
            with shelve.open(files.bot_message_bd) as bd: start_message = bd['userfalse']
            start_message = start_message.replace('uname', message.from_user.first_name)
            bot.send_message(message.chat.id, start_message, parse_mode='Markdown')
            print(f"DEBUG: /start handler - User logged: {message.chat.id}") # Duplicado por si acaso
            dop.user_loger(chat_id=message.chat.id)
			
    elif '/adm' == message.text:
        print(f"DEBUG: /adm handler - Command /adm received from {message.chat.id}")
        if not message.chat.id in in_admin:  in_admin.append(message.chat.id)
        adminka.in_adminka(message.chat.id, message.text, message.chat.username, message.from_user.first_name)

    elif  message.chat.id in in_admin:
        print(f"DEBUG: Admin handler - Message from in_admin user {message.chat.id}: {message.text}")
        adminka.in_adminka(message.chat.id, message.text, message.chat.username, message.from_user.first_name)

    elif '/help' == message.text:
        print(f"DEBUG: /help handler - Command /help received from {message.chat.id}")
        if dop.check_message('help') is True:
            print(f"DEBUG: /help handler - Help message exists. Sending help message.")
            with shelve.open(files.bot_message_bd) as bd: help_message = bd['help']
            bot.send_message(message.chat.id, help_message)
        elif dop.check_message('help') is False and message.chat.id in dop.get_adminlist():
            print(f"DEBUG: /help handler - Admin, no help message set. Sending setup message.")
            bot.send_message(message.chat.id, 'Сообщение с помощью ещё не добавлено!\nЧтобы его добавить, перейдите в админку по команде /adm y *настройте ответы бота*', parse_mode='Markdown')

    elif dop.get_sost(message.chat.id) is True:
        print(f"DEBUG: get_sost is True handler - User state {message.chat.id} is active.")
        with shelve.open(files.sost_bd) as bd: sost_num = bd[str(message.chat.id)]
        if sost_num == 22:
            print(f"DEBUG: get_sost = 22 handler - Processing quantity input.")
            key = telebot.types.InlineKeyboardMarkup()
            try:
                amount = int(message.text) #проверяется, числительно ли это
                with open('data/Temp/' + str(message.chat.id) + 'good_name.txt', encoding='utf-8') as f: name_good = f.read()
                if dop.get_minimum(name_good) <= amount <= dop.amount_of_goods(name_good):
                    print(f"DEBUG: Quantity valid. Processing order sum.")
                    sum = dop.order_sum(name_good, amount)
                    if dop.check_vklpayments('qiwi') == '✅' and dop.check_vklpayments('btc') == '✅':
                        b1 = telebot.types.InlineKeyboardButton(text='🥝Qiwi🥝', callback_data='Qiwi')
                        b2 = telebot.types.InlineKeyboardButton(text='💰btc', callback_data='btc')
                        key.add(b1, b2)
                    elif dop.check_vklpayments('qiwi') == '✅': key.add(telebot.types.InlineKeyboardButton(text='🥝Qiwi🥝', callback_data='Qiwi'))
                    elif dop.check_vklpayments('btc') ==  '✅': key.add(telebot.types.InlineKeyboardButton(text='💰btc', callback_data='btc'))
                    key.add(telebot.types.InlineKeyboardButton(text='Вернуться в начало', callback_data = 'Вернуться в начало'))
                    bot.send_message(message.chat.id,'Вы *выбрали*: ' + name_good + '\n*Количеством*: ' + str(amount) + '\n*Сумма* заказа: ' + str(sum) + ' р\nВыбирите, куда желаете оплатить', parse_mode='Markdown', reply_markup=key)
                    print(f"DEBUG: Order sum message sent. Saving order details.")
                    with open('data/Temp/' + str(message.chat.id) + '.txt', 'w', encoding='utf-8') as f:
                        f.write(str(amount) + '\n') #записывается количество выбраных товаров
                        f.write(str(sum) + '\n') #записывается стоимость выбранных товаров
                elif dop.get_minimum(name_good) >= amount: 
                    print(f"DEBUG: Quantity too low. Sending warning.")
                    key.add(telebot.types.InlineKeyboardButton(text = 'Вернуться в начало', callback_data = 'Вернуться в начало'))
                    bot.send_message(message.chat.id, 'Выберите y отправьте большее количество!\nМинимальное количество к покупке *' + str(dop.get_minimum(name_good)) + '*', parse_mode='Markdown', reply_markup=key)
                elif amount >= dop.amount_of_goods(name_good): 
                    print(f"DEBUG: Quantity too high. Sending warning.")
                    bot.send_message(message.chat.id, 'Выберите y отправьте меньшее количество!\nМаксимальное количество к покупке *' + str(dop.amount_of_goods(name_good)) + '*', parse_mode='Markdown', reply_markup=key)
            except Exception as e: 
                print(f"DEBUG: Error in quantity processing: {e}")
                key.add(telebot.types.InlineKeyboardButton(text='Вернуться в начало', callback_data='Вернуться в начало'))
                bot.send_message(message.chat.id, 'Нужное количество выбирать строго в цифрах!', reply_markup=key)


@bot.callback_query_handler(func=lambda c:True)
def inline(callback):
    print(f"DEBUG: inline - Callback recibido: {callback.data} de {callback.message.chat.id}")
    the_goods = dop.get_goods()
    if callback.message.chat.id in in_admin:
        adminka.ad_inline(callback.data, callback.message.chat.id, callback.message.message_id)

    elif callback.data == 'Перейти к каталогу товаров':
        print(f"DEBUG: Callback - 'Ir al catalogo de productos' from {callback.message.chat.id}")
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT name, price FROM goods;")
        key = telebot.types.InlineKeyboardMarkup()
        for name, price in cursor.fetchall():
            key.add(telebot.types.InlineKeyboardButton(text = name, callback_data = name))
        key.add(telebot.types.InlineKeyboardButton(text = 'Вернуться в начало', callback_data = 'Вернуться в начало'))
        con.close()

        if dop.get_productcatalog() == None:
            print(f"DEBUG: Callback - Product catalog is empty for {callback.message.chat.id}")
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='На данный момент в боте не было создано ни одной позиции')
        else:
            try:
                print(f"DEBUG: Callback - Sending product catalog for {callback.message.chat.id}")
                bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dop.get_productcatalog(), reply_markup=key, parse_mode='Markdown')
            except Exception as e:
                print(f"DEBUG: Callback - Error editing message for product catalog: {e}")
                pass

    elif callback.data in the_goods:
        print(f"DEBUG: Callback - Product selected: {callback.data} by {callback.message.chat.id}")
        with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', 'w', encoding='utf-8') as f: f.write(callback.data)
        key = telebot.types.InlineKeyboardMarkup()
        key.add(telebot.types.InlineKeyboardButton(text = 'Купить', callback_data = 'Купить'))
        key.add(telebot.types.InlineKeyboardButton(text = 'Вернуться в начало', callback_data = 'Вернуться в начало'))
        try: bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=dop.get_description(callback.data), reply_markup=key)
        except Exception as e:
            print(f"DEBUG: Callback - Error editing message for product description: {e}")
            pass

    elif callback.data == 'Вернуться в начало':
        print(f"DEBUG: Callback - 'Volver al inicio' from {callback.message.chat.id}")
        if callback.message.chat.username:
            if dop.get_sost(callback.message.chat.id) is True: 
                with shelve.open(files.sost_bd) as bd: del bd[str(callback.message.chat.id)]
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text = 'Перейти к каталогу товаров', callback_data = 'Перейти к каталогу товаров'))
            with shelve.open(files.bot_message_bd) as bd: start_message = bd['start']
            start_message = start_message.replace('username', callback.message.chat.username)
            start_message = start_message.replace('name', callback.message.from_user.first_name)
            try: bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=start_message, reply_markup=key)
            except Exception as e:
                print(f"DEBUG: Callback - Error editing message for start: {e}")
                pass
        elif not callback.message.chat.username:
            with shelve.open(files.bot_message_bd) as bd: start_message = bd['userfalse']
            start_message = start_message.replace('uname', callback.message.from_user.first_name)
            bot.send_message(callback.message.chat.id, start_message, parse_mode='Markdown')

    elif callback.data == 'Купить':
        print(f"DEBUG: Callback - 'Comprar' from {callback.message.chat.id}")
        with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', encoding='utf-8') as f: name_good = f.read()
        if dop.amount_of_goods(name_good) == 0:
            print(f"DEBUG: Callback - Product not available for purchase: {name_good}")
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='В данный момент недоступно к покупке')
        elif dop.payments_checkvkl() == None:
            print(f"DEBUG: Callback - Payments disabled.")
            bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Оплата на данный момент отключена')
        else:
            print(f"DEBUG: Callback - Requesting quantity for {name_good}.")
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text = 'Вернуться в начало', callback_data = 'Вернуться в начало'))
            try: bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='Введите *количество* товаров к покупке\n*Минимальное* количество к покупке: ' + str(dop.get_minimum(name_good)) + '\n*Максимальное* disponible: ' + str(dop.amount_of_goods(name_good)), reply_markup=key, parse_mode='Markdown')
            except Exception as e:
                print(f"DEBUG: Callback - Error editing message for quantity request: {e}")
                pass
            with shelve.open(files.sost_bd) as bd: bd[str(callback.message.chat.id)] = 22

    elif callback.data == 'btc' or callback.data == 'Qiwi':
        print(f"DEBUG: Callback - Payment method selected: {callback.data} by {callback.message.chat.id}")
        if callback.data == 'Qiwi':
            with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', encoding='utf-8') as f: name_good = f.read()
            amount = dop.normal_read_line('data/Temp/' + str(callback.message.chat.id) + '.txt', 0)
            sum = dop.normal_read_line('data/Temp/' + str(callback.message.chat.id) + '.txt', 1)

            payments.creat_bill_qiwi(callback.message.chat.id, callback.id, callback.message.message_id, sum, name_good, amount)
        elif callback.data == 'btc':
            sum = dop.normal_read_line('data/Temp/' + str(callback.message.chat.id) + '.txt', 1)
            with open('data/Temp/' + str(callback.message.chat.id) + 'good_name.txt', encoding='utf-8') as f: name_good = f.read()
            amount = dop.normal_read_line('data/Temp/' + str(callback.message.chat.id) + '.txt', 0)
            if int(sum) < 40:
                print(f"DEBUG: Callback - BTC sum too low: {sum}")
                bot.answer_callback_query(callback_query_id=callback.id, show_alert=True, text='Сумму менее 100 рублей оплатить в btc невозможно!')

            else: payments.creat_bill_btc(callback.message.chat.id, callback.id, callback.message.message_id, sum, name_good, amount)
    elif callback.data == 'Проверить оплату':
        print(f"DEBUG: Callback - Checking Qiwi payment for {callback.message.chat.id}")
        payments.check_oplata_qiwi(callback.message.chat.id, callback.from_user.username, callback.id, callback.message.from_user.first_name)
    
    elif callback.data == 'Проверить оплату btc':
        print(f"DEBUG: Callback - Checking BTC payment for {callback.message.chat.id}")
        payments.check_oplata_btc(callback.message.chat.id, callback.from_user.username, callback.id, callback.message.from_user.first_name)

    elif dop.get_sost(callback.message.chat.id) is True:
        print(f"DEBUG: Callback - User state active, processing sost_num for {callback.message.chat.id}")
        with shelve.open(files.sost_bd) as bd: sost_num = bd[str(callback.message.chat.id)]
        if sost_num == 12:
            print(f"DEBUG: Callback - sost_num is 12 for {callback.message.chat.id}. Passing.")
            pass 


@bot.message_handler(content_types=['document'])
def handle_docs_log(message):
    print(f"DEBUG: Document handler - Document received from {message.chat.id}")
    if message.chat.id in in_admin:
        if shelve.open(files.sost_bd)[str(message.chat.id)] == 12:
            adminka.new_files(message.document.file_id, message.chat.id)
		
if __name__ == '__main__':
    print("DEBUG: main.py - Calling bot.infinity_polling().")
    bot.infinity_polling()
    print("DEBUG: main.py - bot.infinity_polling() exited.") # Esto no se verá a menos que el polling termine