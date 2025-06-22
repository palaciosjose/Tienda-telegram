import telebot, time, shelve, requests, json
import dop, config, files

bot = telebot.TeleBot(config.token)

he_client = []

try:
    import paypalrestsdk
    PAYPAL_AVAILABLE = True
except ImportError:
    PAYPAL_AVAILABLE = False
    print("Advertencia: paypalrestsdk no instalado. Los pagos PayPal no funcionarán.")

try:
    from binance.client import Client as BinanceClient
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("Advertencia: python-binance no instalado. Los pagos Binance no funcionarán.")

def creat_bill_paypal(chat_id, callback_id, message_id, sum_amount, name_good, amount):
    if not PAYPAL_AVAILABLE:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='PayPal no está disponible!')
        return
        
    if dop.get_paypaldata() == None: 
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='PayPal no está configurado en este momento!')
        return
        
    client_id, client_secret, sandbox = dop.get_paypaldata()
    
    # Configurar PayPal
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
    
    # Crear pago
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": "https://example.com/return",
            "cancel_url": "https://example.com/cancel"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": name_good,
                    "sku": "001",
                    "price": str(sum_amount),
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(sum_amount),
                "currency": "USD"
            },
            "description": f"Compra de {name_good} x{amount}"
        }]
    })
    
    if payment.create():
        payment_id = payment.id
        approval_url = None
        
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = link.href
                break
        
        # Guardar datos temporales
        with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:
            f.write(str(amount) + '\n')
            f.write(str(sum_amount) + '\n')
            f.write(payment_id)
        
        key = telebot.types.InlineKeyboardMarkup()
        if approval_url:
            url_button = telebot.types.InlineKeyboardButton("Pagar con PayPal", url=approval_url)
            key.add(url_button)
        b1 = telebot.types.InlineKeyboardButton(text='Verificar pago PayPal', callback_data='Verificar pago PayPal')
        key.add(b1)
        key.add(telebot.types.InlineKeyboardButton(text='Volver al inicio', callback_data='Volver al inicio'))
        
        try: 
            bot.edit_message_text(
                chat_id=chat_id, 
                message_id=message_id, 
                text=f'Para comprar {name_good} cantidad {amount}\nTotal: ${sum_amount} USD\nHaz clic en "Pagar con PayPal" y completa el pago.\nLuego presiona "Verificar pago".', 
                reply_markup=key
            )
        except: 
            pass
        
        he_client.append(chat_id)
    else:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Error creando pago PayPal!')

def check_oplata_paypal(chat_id, username, callback_id, first_name, message_id):
    if not PAYPAL_AVAILABLE:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='PayPal no está disponible!')
        return
        
    if chat_id in he_client:
        with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f: 
            name_good = f.read()
        amount = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 0)
        sum_amount = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 1)
        payment_id = dop.read_my_line('data/Temp/' + str(chat_id) + '.txt', 2)
        
        # Verificar el pago
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment.state == 'approved':
                he_client.remove(chat_id)
                try: 
                    bot.edit_message_text(
                        chat_id=chat_id, 
                        message_id=message_id, 
                        text='¡Pago de PayPal confirmado!\nAhora recibirás tu producto'
                    )
                except: 
                    pass
                
                # Entregar producto
                text = ''
                for i in range(int(amount)):
                    if dop.get_goodformat(name_good) == 'file':
                        bot.send_document(chat_id, dop.get_tovar(name_good))
                    elif dop.get_goodformat(name_good) == 'text':
                        text += dop.get_tovar(name_good) + '\n'
                
                if dop.get_goodformat(name_good) == 'text': 
                    bot.send_message(chat_id, text)
                
                if dop.check_message('after_buy') is True:
                    with shelve.open(files.bot_message_bd) as bd: 
                        after_buy = bd['after_buy']
                    after_buy = after_buy.replace('username', username)
                    after_buy = after_buy.replace('name', first_name)
                    bot.send_message(chat_id, after_buy)
                
                # Notificar a admins
                for admin_id in dop.get_adminlist(): 
                    bot.send_message(admin_id, f'*Usuario*\nID: `{chat_id}`\nUsername: @{username}\nCompró *{name_good}*\nPor ${sum_amount} USD (PayPal)', parse_mode='Markdown')
                
                dop.new_buy(chat_id, username, name_good, amount, sum_amount)
                dop.new_buyer(chat_id, username, sum_amount)
            else:
                bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='El pago aún no ha sido confirmado!')
        except Exception as e:
            print(f"Error verificando pago PayPal: {e}")
            bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Error verificando el pago!')

def creat_bill_binance(chat_id, callback_id, message_id, sum_amount, name_good, amount):
    if dop.get_binancedata() == None: 
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Binance Pay no está configurado en este momento!')
        return
    
    # Guardar datos temporales
    with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:
        f.write(str(amount) + '\n')
        f.write(str(sum_amount) + '\n')
        f.write('binance_order_' + str(chat_id) + '_' + str(int(time.time())))
    
    key = telebot.types.InlineKeyboardMarkup()
    # Para Binance, por ahora usaremos método manual
    b1 = telebot.types.InlineKeyboardButton(text='Verificar pago Binance', callback_data='Verificar pago Binance')
    key.add(b1)
    key.add(telebot.types.InlineKeyboardButton(text='Volver al inicio', callback_data='Volver al inicio'))
    
    try: 
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=f'Para comprar {name_good} cantidad {amount}\nTotal: ${sum_amount} USD\n\n📱 **Instrucciones para pagar con Binance Pay:**\n1. Abre Binance App\n2. Ve a "Pay"\n3. Envía ${sum_amount} USD a:\n`[WALLET_ADDRESS_AQUI]`\n\n⚠️ **Importante:** Guarda el ID de transacción\nLuego presiona "Verificar pago"', 
            parse_mode='Markdown',
            reply_markup=key
        )
    except: 
        pass
    
    he_client.append(chat_id)

def check_oplata_binance(chat_id, username, callback_id, first_name, message_id):
    if chat_id in he_client:
        with open('data/Temp/' + str(chat_id) + 'good_name.txt', encoding='utf-8') as f: 
            name_good = f.read()
        amount = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 0)
        sum_amount = dop.normal_read_line('data/Temp/' + str(chat_id) + '.txt', 1)
        
        # Por ahora, verificación manual (puedes mejorar esto con Binance API)
        # En una implementación real, aquí verificarías con la API de Binance
        
        # Simulación de verificación exitosa (cambiar por lógica real)
        payment_confirmed = True  # Aquí iría la verificación real
        
        if payment_confirmed:
            he_client.remove(chat_id)
            try: 
                bot.edit_message_text(
                    chat_id=chat_id, 
                    message_id=message_id, 
                    text='¡Pago de Binance confirmado!\nAhora recibirás tu producto'
                )
            except: 
                pass
            
            # Entregar producto
            text = ''
            for i in range(int(amount)):
                if dop.get_goodformat(name_good) == 'file':
                    bot.send_document(chat_id, dop.get_tovar(name_good))
                elif dop.get_goodformat(name_good) == 'text':
                    text += dop.get_tovar(name_good) + '\n'
            
            if dop.get_goodformat(name_good) == 'text': 
                bot.send_message(chat_id, text)
            
            if dop.check_message('after_buy') is True:
                with shelve.open(files.bot_message_bd) as bd: 
                    after_buy = bd['after_buy']
                after_buy = after_buy.replace('username', username)
                after_buy = after_buy.replace('name', first_name)
                bot.send_message(chat_id, after_buy)
            
            # Notificar a admins
            for admin_id in dop.get_adminlist(): 
                bot.send_message(admin_id, f'*Usuario*\nID: `{chat_id}`\nUsername: @{username}\nCompró *{name_good}*\nPor ${sum_amount} USD (Binance)', parse_mode='Markdown')
            
            dop.new_buy(chat_id, username, name_good, amount, sum_amount)
            dop.new_buyer(chat_id, username, sum_amount)
        else:
            bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='El pago aún no ha sido confirmado!')