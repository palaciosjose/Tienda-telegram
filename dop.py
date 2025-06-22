import telebot, shelve, datetime, sqlite3, random, os
import files, config

bot = telebot.TeleBot(config.token)

def it_first(chat_id):
    try:
        with open(files.working_log, encoding='utf-8') as f: 
            return False
    except:
        return True

def main(chat_id):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    user_markup.row('Configurar respuestas del bot')
    user_markup.row('Configuración de productos', 'Cargar nuevo producto')
    user_markup.row('Configuración de pagos')
    user_markup.row('Estadísticas', 'Difusión')
    user_markup.row('Otras configuraciones')
    
    bot.send_message(chat_id, """*¡Hola!*
Este es el primer arranque y ahora estás en el *panel de administración.*
Para que el bot esté listo *para trabajar* con clientes en poco tiempo, necesitas agregar métodos de pago.
Puedes elegir entre pagos con *PayPal* y *Binance*.

En este *momento* estás en el panel de administración del bot. La próxima vez, para acceder escribe /adm
Para salir, presiona /start
*Guía completa de configuración del bot*(recomiendo leer) - https://telegra.ph/Polnaya-nastrojka-08-31
""", parse_mode='MarkDown', reply_markup=user_markup)

    # Inicializar shelve para pagos si no existe
    try:
        with shelve.open(files.payments_bd) as bd:
            bd['paypal'] = '❌'
            bd['binance'] = '❌'
    except:
        pass

    log('Primer arranque del bot')
    new_admin(chat_id)

def log(text):
    time = str(datetime.datetime.utcnow())[:22]
    try: 
        with open(files.working_log, 'a', encoding='utf-8') as f: 
            f.write(time + '    | ' + text + '\n')
    except: 
        with open(files.working_log, 'w', encoding='utf-8') as f: 
            f.write(time + '    | ' + text + '\n')

def check_message(message):
    try:
        with shelve.open(files.bot_message_bd) as bd:
            if message in bd: 
                return True
            else: 
                return False
    except:
        return False

def get_adminlist():
    admins_list = [config.admin_id]  # Siempre incluir el admin principal
    try:
        with open(files.admins_list, encoding='utf-8') as f:
            for admin_id in f.readlines(): 
                try:
                    admin_id = int(admin_id.strip())
                    if admin_id not in admins_list:
                        admins_list.append(admin_id)
                except:
                    continue
    except:
        pass
    return admins_list

def user_loger(chat_id=0):
    if chat_id != 0:
        try:
            with open(files.users_list, encoding='utf-8') as f:
                if not str(chat_id) in f.read():
                    with open(files.users_list, 'a', encoding='utf-8') as f: 
                        f.write(str(chat_id) + '\n')
        except:
            with open(files.users_list, 'w', encoding='utf-8') as f: 
                f.write(str(chat_id) + '\n')
    
    try:
        with open(files.users_list, encoding='utf-8') as f: 
            return len(f.readlines())
    except:
        return 0

def get_productcatalog():
    product_list = '*Catálogo actual de productos:*\n'
    product_list += '*DESCUENTOS 25% EN TODO\n*'
    
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT name, description, price, stored FROM goods;")
        a = 0
        for name, description, price, stored in cursor.fetchall():
            a += 1
            lasstprice = str(int(price*1.5))+' USD'
            array = list(lasstprice)
            lastprice = "̶" + "̶".join(array) + "̶"
            good_amount = amount_of_goods(name)
            product_list += '*' + name + '*' + ' `-`' + '  ' + lastprice + '  ' + ' *$' + str(price) + '*' + ' USD ' + '(Quedan ' + str(good_amount) +')\n'
        con.close()
        if a == 0: 
            return None
        else: 
            return product_list
    except Exception as e:
        print(f"Error obteniendo catálogo de productos: {e}")
        return None

def get_goods():
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT name FROM goods;")
        goods = []
        for row in cursor.fetchall(): 
            goods.append(row[0])
        con.close()
        return goods
    except:
        return []

def get_stored(name_good):
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT stored FROM goods WHERE name = ?;", (name_good,))
        result = cursor.fetchone()
        con.close()
        if result:
            return result[0]
        return None
    except:
        return None

def amount_of_goods(name_good):
    stored = get_stored(name_good)
    if not stored:
        return 0
    try: 
        with open(stored, encoding='utf-8') as f: 
            lines = f.readlines()
            return len([line for line in lines if line.strip()])
    except: 
        return 0

def get_minimum(name_good):
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT minimum FROM goods WHERE name = ?;", (name_good,))
        result = cursor.fetchone()
        con.close()
        if result:
            return result[0]
        return 1
    except:
        return 1

def order_sum(name_good, amount):
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT price FROM goods WHERE name = ?;", (name_good,))
        result = cursor.fetchone()
        con.close()
        if result:
            return int(result[0]) * amount
        return 0
    except:
        return 0

def read_my_line(filename, linenumber):
    try:
        with open(filename, encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == linenumber:
                    return line
        return ""
    except:
        return ""

def normal_read_line(filename, linenumber):
    line = read_my_line(filename, linenumber)
    return line.rstrip('\n')

def get_sost(chat_id):
    try:
        with shelve.open(files.sost_bd) as bd:
            return str(chat_id) in bd
    except:
        return False

def check_vklpayments(name):
    try:
        with shelve.open(files.payments_bd) as bd: 
            return bd.get(name, '❌')
    except:
        return '❌'

def get_goodformat(name_good):
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT format FROM goods WHERE name = ?;", (name_good,))
        result = cursor.fetchone()
        con.close()
        if result:
            return result[0]
        return 'text'
    except:
        return 'text'

def get_profit():
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT price FROM purchases;")
        price_amount = 0
        for row in cursor.fetchall(): 
            price_amount += int(row[0])
        con.close()
        return price_amount
    except:
        return 0

def get_amountsbayers():
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM buyers;")
        result = cursor.fetchone()
        con.close()
        return result[0] if result else 0
    except:
        return 0

def get_amountblock():
    try:
        with open(files.blockusers_list, encoding='utf-8') as f: 
            return len(f.readlines())
    except:
        return 0

def new_blockuser(his_id):
    try:
        with open(files.blockusers_list, 'a', encoding='utf-8') as f: 
            f.write(str(his_id) + '\n')
    except:
        pass

def rasl(group, amount, text):
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
                    bot.send_message(chat_id, text)
                    good_send += 1
                except: 
                    lose_send += 1
                    new_blockuser(chat_id)
                i += 1
        except:
            pass
    
    elif group == 'buyers':
        try:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT id FROM buyers LIMIT ?;", (int(amount),))
            buyers = cursor.fetchall()
            
            for buyer in buyers:
                chat_id = int(buyer[0])
                try:
                    bot.send_message(chat_id, text)
                    good_send += 1
                except: 
                    lose_send += 1
                    new_blockuser(chat_id)
            con.close()
        except:
            pass

    return f'¡{good_send} usuarios recibieron el mensaje exitosamente!\n{lose_send} usuarios bloquearon el bot y fueron agregados a la lista de usuarios bloqueados'

def del_id(file, chat_id):
    try:
        text = ''
        with open(file, encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                if str(chat_id) != line: 
                    text += line + '\n'
        with open(file, 'w', encoding='utf-8') as f: 
            f.write(text)
    except:
        pass

def new_admin(his_id):
    try:
        with open(files.admins_list, encoding='utf-8') as f:
            content = f.read()
        if str(his_id) not in content:
            with open(files.admins_list, 'a', encoding='utf-8') as f: 
                f.write(str(his_id) + '\n')
    except:
        with open(files.admins_list, 'w', encoding='utf-8') as f: 
            f.write(str(his_id) + '\n')

def get_description(name_good):
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT description FROM goods WHERE name = ?;", (name_good,))
        result = cursor.fetchone()
        con.close()
        if result:
            return result[0]
        return "Descripción no encontrada"
    except:
        return "Descripción no encontrada"

def get_paypaldata():
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT client_id, client_secret, sandbox FROM paypal_data;")
        result = cursor.fetchone()
        con.close()
        if result:
            return result[0], result[1], bool(result[2])
        return None
    except:
        return None

def get_binancedata():
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT api_key, api_secret, merchant_id FROM binance_data;")
        result = cursor.fetchone()
        con.close()
        if result:
            return result[0], result[1], result[2]
        return None
    except:
        return None

def check_paypal_valid(client_id, client_secret, sandbox=True):
    try:
        import paypalrestsdk
        if sandbox:
            paypalrestsdk.configure({
                "mode": "sandbox",
                "client_id": client_id,
                "client_secret": client_secret
            })
        else:
            paypalrestsdk.configure({
                "mode": "live", 
                "client_id": client_id,
                "client_secret": client_secret
            })
        
        # Crear un pago de prueba para verificar credenciales
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": "1.00", "currency": "USD"},
                "description": "Test payment"
            }]
        })
        return True
    except:
        return False

def check_binance_valid(api_key, api_secret):
    try:
        from binance.client import Client
        client = Client(api_key, api_secret, testnet=True)
        client.get_account()
        return True
    except:
        return False

def payments_checkvkl():
    active_payment = []
    
    # Verificar PayPal
    if check_vklpayments('paypal') == '✅' and get_paypaldata() != None: 
        active_payment.append('paypal')
    elif check_vklpayments('paypal') == '✅' and get_paypaldata() == None:
        for admin_id in get_adminlist(): 
            try:
                bot.send_message(admin_id, '¡Faltan datos de PayPal en la base de datos! Se desactivó automáticamente para recibir pagos.')
            except:
                pass
        try:
            with shelve.open(files.payments_bd) as bd: 
                bd['paypal'] = '❌'
        except:
            pass

    # Verificar Binance
    if check_vklpayments('binance') == '✅' and get_binancedata() != None: 
        active_payment.append('binance')
    elif check_vklpayments('binance') == '✅' and get_binancedata() == None:
        for admin_id in get_adminlist(): 
            try:
                bot.send_message(admin_id, '¡Faltan datos de Binance en la base de datos! Se desactivó automáticamente para recibir pagos.')
            except:
                pass
        try:
            with shelve.open(files.payments_bd) as bd: 
                bd['binance'] = '❌'
        except:
            pass

    if len(active_payment) > 0: 
        return active_payment
    else: 
        return None

def generator_pw(n):
    passwd = list('1234567890ABCDEFGHIGKLMNOPQRSTUVYXWZ')
    random.shuffle(passwd)
    pas = ''.join([random.choice(passwd) for x in range(n)])
    return pas

def get_tovar(name_good):
    try:
        stored = get_stored(name_good)
        if not stored:
            return "Producto no encontrado"
            
        with open(stored, encoding='utf-8') as f: 
            lines = f.readlines()
        
        if not lines:
            return "Producto agotado"
            
        # Obtener primera línea y eliminarla
        first_line = lines[0].strip()
        remaining_lines = lines[1:]
        
        with open(stored, 'w', encoding='utf-8') as f: 
            f.writelines(remaining_lines)
        
        return first_line
    except:
        return "Error obteniendo producto"

def new_buy(his_id, username, name_good, amount, price):
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("INSERT INTO purchases VALUES(?, ?, ?, ?, ?)", (his_id, username, name_good, amount, price))
        con.commit()
        con.close()
    except:
        pass

def new_buyer(his_id, username, payed):
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        cursor.execute("SELECT payed FROM buyers WHERE id = ?;", (his_id,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute("INSERT INTO buyers VALUES(?, ?, ?)", (his_id, username, payed))
        else:
            total_payed = int(result[0]) + int(payed)
            cursor.execute("UPDATE buyers SET payed = ? WHERE id = ?;", (total_payed, his_id))
        
        con.commit()
        con.close()
    except:
        pass