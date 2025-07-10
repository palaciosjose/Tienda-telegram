import telebot, time, shelve, requests, json
from datetime import datetime, timedelta
import dop, config, files
from bot_instance import bot

he_client = []
pending_payments = {}  # Para almacenar pagos pendientes

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
    """Crear factura PayPal - función sin cambios"""
    if not PAYPAL_AVAILABLE:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='PayPal no está disponible!')
        return
        
    shop_id = dop.get_user_shop(chat_id)
    if dop.get_paypaldata(shop_id) == None:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='PayPal no está configurado en este momento!')
        return

    client_id, client_secret, sandbox = dop.get_paypaldata(shop_id)
    
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
            dop.safe_edit_message(
                bot,
                type('obj', (object,), {
                    'chat': type('chat', (object,), {'id': chat_id})(),
                    'message_id': message_id,
                    'content_type': 'text'
                })(),
                f'Para comprar {name_good} cantidad {amount}\nTotal: ${sum_amount} USD\nHaz clic en "Pagar con PayPal" y completa el pago.\nLuego presiona "Verificar pago".',
                reply_markup=key
            )
        except Exception as e:
            print(f"Error editando mensaje de pago PayPal: {e}")
        
        he_client.append(chat_id)
    else:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Error creando pago PayPal!')

def check_oplata_paypal(chat_id, username, callback_id, first_name, message_id):
    """Verificar pago PayPal - función sin cambios"""
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
                    dop.safe_edit_message(
                        bot,
                        type('obj', (object,), {
                            'chat': type('chat', (object,), {'id': chat_id})(),
                            'message_id': message_id,
                            'content_type': 'text'
                        })(),
                        '¡Pago de PayPal confirmado!\nAhora recibirás tu producto'
                    )
                except Exception as e:
                    print(f"Error confirmando pago PayPal: {e}")
                
                # Entregar producto
                deliver_product(chat_id, username, first_name, name_good, amount, sum_amount, "PayPal")
                
            else:
                bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='El pago aún no ha sido confirmado!')
        except Exception as e:
            print(f"Error verificando pago PayPal: {e}")
            bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Error verificando el pago!')

def creat_bill_binance(chat_id, callback_id, message_id, sum_amount, name_good, amount):
    """Crear solicitud de pago Binance CORREGIDA - Con ID en instrucciones"""
    if not BINANCE_AVAILABLE:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Binance Pay no está disponible!')
        return

    shop_id = dop.get_user_shop(chat_id)
    if dop.get_binancedata(shop_id) == None:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Binance Pay no está configurado en este momento!')
        return
    
    # Obtener tu Binance Pay ID
    try:
        api_key, api_secret, binance_pay_id = dop.get_binancedata(shop_id)
        # binance_pay_id es tu 294603789
    except Exception as e:
        print(f"Error obteniendo Binance Pay ID: {e}")
        binance_pay_id = "294603789"  # fallback
    
    # Generar ID único para el pago
    payment_id = f'BIN_{chat_id}_{int(time.time())}'
    
    # Guardar datos del pago pendiente
    pending_payments[chat_id] = {
        'payment_id': payment_id,
        'amount': sum_amount,
        'product': name_good,
        'quantity': amount,
        'timestamp': time.time()
    }
    
    # Guardar datos temporales
    with open('data/Temp/' + str(chat_id) + '.txt', 'w', encoding='utf-8') as f:
        f.write(str(amount) + '\n')
        f.write(str(sum_amount) + '\n')
        f.write(payment_id)
    
    key = telebot.types.InlineKeyboardMarkup()
    b1 = telebot.types.InlineKeyboardButton(text='✅ Confirmé el pago', callback_data='Verificar pago Binance')
    key.add(b1)
    key.add(telebot.types.InlineKeyboardButton(text='🏠 Volver al inicio', callback_data='Volver al inicio'))
    
    # MENSAJE CORREGIDO - CON ID EN LAS INSTRUCCIONES
    try:
        dop.safe_edit_message(
            bot,
            type('obj', (object,), {
                'chat': type('chat', (object,), {'id': chat_id})(),
                'message_id': message_id,
                'content_type': 'text'
            })(),
            f"""💳 **Pago con Binance Pay**

📦 **Producto:** {name_good}
🔢 **Cantidad:** {amount}
💰 **Total:** ${sum_amount} USD

🚀 **Instrucciones de pago:**

1️⃣ Abre tu app de **Binance**
2️⃣ Ve a **"Pay"** → **"Enviar"**
3️⃣ Envía **${sum_amount} USD** a:
`{binance_pay_id}`

4️⃣ **🔑 PASO CRÍTICO:**
En el campo **"Concepto"** o **"Nota"** escribe:
`{payment_id}`

5️⃣ Confirma el envío
6️⃣ Presiona "✅ Confirmé el pago"

⚠️ **IMPORTANTE:** 
• El ID `{payment_id}` identifica TU pago
• Sin este ID no podremos verificar tu pago
• Copia y pega exactamente como aparece""", 
            parse_mode='Markdown',
            reply_markup=key
        )
    except Exception as e:
        print(f"Error editando mensaje: {e}")
    
    he_client.append(chat_id)

def check_oplata_binance(chat_id, username, callback_id, first_name, message_id):
    """Verificación MANUAL de pago Binance - SISTEMA CORREGIDO"""
    if not BINANCE_AVAILABLE:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='Binance Pay no está disponible!')
        return
    print(f"DEBUG: check_oplata_binance llamado para chat_id: {chat_id}")
    
    if chat_id not in he_client:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='❌ No hay pago pendiente')
        return
    
    if chat_id not in pending_payments:
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='❌ No se encontró información del pago')
        return
    
    # Obtener información del pago
    payment_info = pending_payments[chat_id]
    payment_id = payment_info['payment_id']
    sum_amount = payment_info['amount']
    name_good = payment_info['product']
    amount = payment_info['quantity']
    
    # Obtener tu Binance Pay ID
    try:
        shop_id = dop.get_user_shop(chat_id)
        api_key, api_secret, binance_pay_id = dop.get_binancedata(shop_id)
    except Exception as e:
        print(f"Error obteniendo Binance Pay ID: {e}")
        binance_pay_id = "294603789"  # fallback
    
    # **SISTEMA DE VERIFICACIÓN MANUAL**
    # Enviar notificación a TODOS los administradores
    admin_list = dop.get_adminlist()
    
    key_admin = telebot.types.InlineKeyboardMarkup()
    key_admin.add(
        telebot.types.InlineKeyboardButton(text='✅ APROBAR', callback_data=f'APROBAR_PAGO_{chat_id}'),
        telebot.types.InlineKeyboardButton(text='❌ RECHAZAR', callback_data=f'RECHAZAR_PAGO_{chat_id}')
    )
    
    admin_message = f"""🔔 **VERIFICACIÓN DE PAGO REQUERIDA**

👤 **Cliente:**
• ID Telegram: `{chat_id}`
• Username: @{username if username else 'Sin username'}
• Nombre: {first_name}

💳 **Detalles del pago:**
• Método: Binance Pay
• Tu Binance ID: `{binance_pay_id}`
• Monto: ${sum_amount} USD
• Producto: {name_good}
• Cantidad: {amount}

🔑 **ID ÚNICO DEL PAGO:**
`{payment_id}`

📋 **INSTRUCCIONES PARA VERIFICAR:**
1. Abre tu Binance
2. Ve a "Pay" → "Historial"
3. Busca pago de ${sum_amount} USD
4. Verifica que en el concepto aparezca: {payment_id}
5. Si coincide → APROBAR
6. Si no coincide o no existe → RECHAZAR

**¿Apruebas este pago?**"""
    
    # Enviar a todos los admins
    for admin_id in admin_list:
        try:
            bot.send_message(admin_id, admin_message, parse_mode='Markdown', reply_markup=key_admin)
            print(f"DEBUG: Notificación enviada a admin {admin_id}")
        except Exception as e:
            print(f"DEBUG: Error enviando a admin {admin_id}: {e}")
    
    # Responder al cliente
    try:
        dop.safe_edit_message(
            bot,
            type('obj', (object,), {
                'chat': type('chat', (object,), {'id': chat_id})(),
                'message_id': message_id,
                'content_type': 'text'
            })(),
            f"""⏳ **Pago en Verificación**

✅ Tu solicitud de pago ha sido enviada al administrador.

📋 **Detalles:**
• Producto: {name_good}
• Cantidad: {amount}
• Monto: ${sum_amount} USD
• ID: `{payment_id}`

⏰ **Tiempo estimado:** 5-30 minutos
📱 Te notificaremos cuando sea aprobado.

💡 **Tip:** Mantén disponible el comprobante de pago por si se solicita.""",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"DEBUG: Error editando mensaje del cliente: {e}")
    
    bot.answer_callback_query(callback_query_id=callback_id, show_alert=False, text='📤 Solicitud enviada al administrador')

def handle_admin_payment_decision(callback_data, admin_chat_id, callback_id, message_id):
    """Manejar decisión del administrador sobre pagos"""
    print(f"DEBUG: handle_admin_payment_decision llamado: {callback_data}")
    
    try:
        parts = callback_data.split('_')
        action = parts[0]  # APROBAR o RECHAZAR
        user_chat_id = int(parts[2])
        
        if user_chat_id not in pending_payments:
            bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='❌ Pago ya procesado o no encontrado')
            return
        
        payment_info = pending_payments[user_chat_id]
        
        if action == 'APROBAR':
            # APROBAR PAGO
            try:
                # Obtener datos del usuario
                with open('data/Temp/' + str(user_chat_id) + 'good_name.txt', encoding='utf-8') as f: 
                    name_good = f.read()
                
                amount = payment_info['quantity']
                sum_amount = payment_info['amount']
                
                # Obtener username del usuario (intentar desde payment_info o usar fallback)
                username = "cliente"  # Fallback
                
                # Entregar producto
                success = deliver_product(user_chat_id, username, "Usuario", name_good, amount, sum_amount, "Binance")
                
                if success:
                    # Notificar al usuario
                    try:
                        bot.send_message(user_chat_id, f"""✅ **¡PAGO APROBADO!**

🎉 Tu pago de ${sum_amount} USD ha sido confirmado.
📦 ¡Ya tienes tu {name_good}!

Gracias por tu compra.""", parse_mode='Markdown')
                    except Exception as e:
                        print(f"DEBUG: Error notificando cliente: {e}")
                    
                    # Confirmar al admin
                    try:
                        dop.safe_edit_message(
                            bot,
                            type('obj', (object,), {
                                'chat': type('chat', (object,), {'id': admin_chat_id})(),
                                'message_id': message_id,
                                'content_type': 'text'
                            })(),
                            f"✅ **PAGO APROBADO por Admin {admin_chat_id}**\n\nUsuario {user_chat_id} recibió su producto: {name_good}",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        print(f"DEBUG: Error editando mensaje admin: {e}")
                    
                    bot.answer_callback_query(callback_query_id=callback_id, show_alert=False, text='✅ Pago aprobado y producto entregado')
                else:
                    bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='❌ Error entregando producto')
                
            except Exception as e:
                print(f"Error procesando aprobación: {e}")
                bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='❌ Error procesando aprobación')
        
        elif action == 'RECHAZAR':
            # RECHAZAR PAGO
            try:
                # Notificar al usuario
                bot.send_message(user_chat_id, f"""❌ **Pago Rechazado**

Tu pago de ${payment_info['amount']} USD no pudo ser verificado.

🔄 **Opciones:**
• Verifica que enviaste el monto correcto
• Verifica que incluiste el ID en el concepto
• Contacta al soporte si ya pagaste correctamente
• Intenta nuevamente

💬 **Soporte:** Contacta al administrador si necesitas ayuda.""", parse_mode='Markdown')
                
                # Confirmar al admin
                try:
                    dop.safe_edit_message(
                        bot,
                        type('obj', (object,), {
                            'chat': type('chat', (object,), {'id': admin_chat_id})(),
                            'message_id': message_id,
                            'content_type': 'text'
                        })(),
                        f"❌ **PAGO RECHAZADO por Admin {admin_chat_id}**\n\nUsuario {user_chat_id} fue notificado del rechazo.",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"DEBUG: Error editando mensaje admin: {e}")
                
                bot.answer_callback_query(callback_query_id=callback_id, show_alert=False, text='❌ Pago rechazado')
                
            except Exception as e:
                print(f"Error procesando rechazo: {e}")
        
        # Limpiar pago pendiente
        if user_chat_id in he_client:
            he_client.remove(user_chat_id)
        if user_chat_id in pending_payments:
            del pending_payments[user_chat_id]
        
    except Exception as e:
        print(f"Error en handle_admin_payment_decision: {e}")
        bot.answer_callback_query(callback_query_id=callback_id, show_alert=True, text='❌ Error procesando decisión')

def deliver_product(chat_id, username, first_name, name_good, amount, sum_amount, payment_method):
    """Función común para entregar productos"""
    try:
        print(f"DEBUG: Entregando producto {name_good} a usuario {chat_id}")

        shop_id = dop.get_user_shop(chat_id)

        if dop.is_manual_delivery(name_good):
            manual_msg = dop.get_manual_delivery_message(username, first_name)
            bot.send_message(chat_id, manual_msg)
        else:
            # Entregar producto físico/digital
            text = ''
            for i in range(int(amount)):
                if dop.get_goodformat(name_good) == 'file':
                    product_data = dop.get_tovar(name_good, shop_id)
                    if product_data != "Error obteniendo producto" and product_data != "Producto agotado":
                        bot.send_document(chat_id, product_data)
                    else:
                        bot.send_message(chat_id, f"❌ Error obteniendo {name_good}: {product_data}")
                elif dop.get_goodformat(name_good) == 'text':
                    product_data = dop.get_tovar(name_good, shop_id)
                    if product_data != "Error obteniendo producto" and product_data != "Producto agotado":
                        text += product_data + '\n'
                    else:
                        bot.send_message(chat_id, f"❌ Error obteniendo {name_good}: {product_data}")

            if dop.get_goodformat(name_good) == 'text' and text.strip():
                bot.send_message(chat_id, text)
        
        # Mensaje después de compra
        if dop.check_message('after_buy') is True:
            with shelve.open(files.bot_message_bd) as bd: 
                after_buy = bd['after_buy']
            after_buy = after_buy.replace('username', username)
            after_buy = after_buy.replace('name', first_name)
            bot.send_message(chat_id, after_buy)
        
        # Notificar a admins
        for admin_id in dop.get_adminlist(): 
            try:
                bot.send_message(admin_id, f'*Venta Completada*\nID: `{chat_id}`\nUsername: @{username}\nCompró *{name_good}* x{amount}\nPor ${sum_amount} USD ({payment_method})', parse_mode='Markdown')
            except Exception as e:
                print(f"DEBUG: Error notificando admin {admin_id}: {e}")
        
        # Registrar compra asociada a la tienda del usuario
        dop.new_buy(chat_id, username, name_good, amount, sum_amount, shop_id)
        dop.new_buyer(chat_id, username, sum_amount, shop_id)
        
        print(f"DEBUG: Producto entregado exitosamente a {chat_id}")
        return True
        
    except Exception as e:
        print(f"Error entregando producto: {e}")
        return False
