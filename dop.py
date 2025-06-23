import telebot, shelve, datetime, sqlite3, random, os
import files, config

# ---------------------------------------------------------------------------
# Utilidad para asegurar que la base de datos tenga las columnas necesarias
# para la descripción adicional y la gestión de multimedia. Algunas
# instalaciones antiguas pueden carecer de estas columnas y provocar errores
# "no such column" cuando se utilizan las funciones relacionadas. Esta función
# se ejecuta al importar el módulo y modifica la tabla `goods` si es necesario.
# ---------------------------------------------------------------------------
def ensure_database_schema():
    """Agregar columnas faltantes a la tabla goods si es necesario."""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()

        cursor.execute("PRAGMA table_info(goods)")
        columns = [c[1] for c in cursor.fetchall()]
        updated = False

        if 'additional_description' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN additional_description TEXT DEFAULT ''")
            updated = True
        if 'media_file_id' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN media_file_id TEXT")
            updated = True
        if 'media_type' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN media_type TEXT")
            updated = True
        if 'media_caption' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN media_caption TEXT")
            updated = True
        if 'is_subscription' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN is_subscription INTEGER DEFAULT 0")
            updated = True
        if 'duration' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN duration INTEGER DEFAULT 0")
            updated = True
        if 'duration_unit' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN duration_unit TEXT DEFAULT 'days'")
            updated = True
        if 'auto_renew' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN auto_renew INTEGER DEFAULT 1")
            updated = True
        if 'grace_period' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN grace_period INTEGER DEFAULT 0")
            updated = True

        if updated:
            con.commit()
    except Exception as e:
        print(f"Error asegurando esquema de base de datos: {e}")
    finally:
        try:
            con.close()
        except:
            pass

# Asegurar el esquema al importar el módulo
ensure_database_schema()

bot = telebot.TeleBot(config.token)

# -------------------------------------------------
# Utilidad para editar mensajes con o sin multimedia
# -------------------------------------------------
def safe_edit_message(bot, message, text, reply_markup=None, parse_mode=None):
    """Edita texto o caption según el tipo de mensaje"""
    try:
        if getattr(message, 'content_type', 'text') == 'text':
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        else:
            bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=message.message_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        return True
    except Exception as e:
        print(f"Error editando mensaje de forma segura: {e}")
        return False

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
    """Catálogo limpio - solo muestra texto de descuento"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM goods;")
        product_count = cursor.fetchone()[0]
        con.close()
        
        if product_count == 0:
            return None
        
        # Obtener configuración de descuentos
        discount_config = get_discount_config()
        
        # Mensaje del catálogo limpio
        catalog_text = '*Catálogo de productos disponibles:*\n\n'
        
        # Agregar texto de descuento si está habilitado
        if discount_config['enabled']:
            catalog_text += f"*{discount_config['text']}*\n\n"
        
        catalog_text += '*Selecciona un producto para ver detalles y precios*'
        
        return catalog_text
        
    except Exception as e:
        print(f"Error obteniendo catálogo: {e}")
        return None

def get_goods():
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT name FROM goods WHERE is_subscription=0 OR is_subscription IS NULL;")
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
    """Descripción del producto con sistema de descuentos"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT description, price FROM goods WHERE name = ?;", (name_good,))
        result = cursor.fetchone()
        con.close()
        
        if not result:
            return "Producto no encontrado"
        
        description, price = result
        good_amount = amount_of_goods(name_good)
        
        # Obtener configuración de descuentos
        discount_config = get_discount_config()
        
        # Construir descripción
        product_description = f"*{name_good}*\n\n"
        product_description += f"📝 *Descripción:*\n{description}\n\n"
        
        # Mostrar precios con o sin descuento
        if discount_config['enabled'] and discount_config['show_fake_price']:
            # Calcular precio "anterior" falso
            fake_price = int(price * discount_config['multiplier'])
            fake_price_str = str(fake_price) + ' USD'
            array = list(fake_price_str)
            crossed_price = "̶" + "̶".join(array) + "̶"
            
            # Calcular porcentaje de "descuento" para mostrar
            discount_percent = int(((fake_price - price) / fake_price) * 100)
            
            product_description += f"💰 *Precio:*\n"
            product_description += f"~~{crossed_price}~~ 🔥\n"
            product_description += f"*${price} USD* (-{discount_percent}% OFF)\n\n"
        else:
            product_description += f"💰 *Precio:* ${price} USD\n\n"
        
        product_description += f"📦 *Stock disponible:* {good_amount} unidades\n"
        product_description += f"🛒 *Mínimo de compra:* {get_minimum(name_good)} unidades"
        
        return product_description
        
    except Exception as e:
        print(f"Error obteniendo descripción: {e}")
        return "Error obteniendo información del producto"

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
def new_buy_improved(his_id, username, name_good, amount, price, payment_method="Unknown", payment_id=None):
    """Versión mejorada de new_buy que incluye método de pago y timestamp"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        # Usar timestamp actual
        from datetime import datetime
        current_time = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO purchases 
            (id, username, name_good, amount, price, payment_method, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (his_id, username, name_good, amount, price, payment_method, current_time))
        
        # También insertar en tabla de validación si existe
        try:
            cursor.execute("""
                INSERT INTO purchase_validation 
                (user_id, username, product_name, amount, price, payment_method, payment_id, timestamp, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed')
            """, (his_id, username, name_good, amount, price, payment_method, payment_id, current_time))
        except:
            pass  # Si la tabla no existe, continuar
        
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"Error en new_buy_improved: {e}")
        return False

def get_daily_sales():
    """Obtiene las ventas del día actual"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        # Obtener ventas recientes (aproximación por rowid)
        cursor.execute("""
            SELECT COUNT(*), SUM(price)
            FROM purchases 
            ORDER BY rowid DESC 
            LIMIT 100
        """)
        
        count, total = cursor.fetchone()
        
        cursor.execute("""
            SELECT name_good, COUNT(*), SUM(price)
            FROM purchases 
            GROUP BY name_good
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        products = cursor.fetchall()
        con.close()
        
        response = "📊 **Estadísticas de Ventas:**\n\n"
        response += f"🛍️ **Transacciones recientes:** {count or 0}\n"
        response += f"💰 **Ingresos totales:** ${total or 0} USD\n\n"
        
        if products:
            response += "📦 **Productos más vendidos:**\n"
            for product, qty, revenue in products:
                response += f"• {product}: {qty} ventas (${revenue} USD)\n"
        
        return response
        
    except Exception as e:
        return f"❌ Error: {e}"

def search_user_purchases(search_term):
    """Busca compras por ID de usuario o username"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        # Si es número, buscar por ID
        if search_term.isdigit():
            cursor.execute("""
                SELECT id, username, name_good, amount, price, payment_method, timestamp 
                FROM purchases 
                WHERE id = ?
                ORDER BY rowid DESC
            """, (int(search_term),))
        else:
            # Si no, buscar por username
            clean_username = search_term.replace('@', '')
            cursor.execute("""
                SELECT id, username, name_good, amount, price, payment_method, timestamp 
                FROM purchases 
                WHERE username LIKE ?
                ORDER BY rowid DESC
            """, (f"%{clean_username}%",))
        
        purchases = cursor.fetchall()
        con.close()
        
        if not purchases:
            return "❌ No se encontraron compras para este usuario"
        
        # Formatear respuesta
        response = f"📋 **Compras encontradas para: {search_term}**\n\n"
        total_spent = 0
        
        for i, purchase in enumerate(purchases, 1):
            user_id, username, product, amount, price, payment_method, timestamp = purchase
            total_spent += price
            
            # Formatear fecha
            try:
                if timestamp and 'T' in timestamp:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                else:
                    date_str = str(timestamp) if timestamp else "Fecha no disponible"
            except:
                date_str = str(timestamp) if timestamp else "Fecha no disponible"
            
            response += f"🛒 **Compra #{i}**\n"
            response += f"📦 {product} x{amount}\n"
            response += f"💰 ${price} USD\n"
            response += f"💳 {payment_method or 'No especificado'}\n"
            response += f"📅 {date_str}\n"
            response += f"👤 ID: `{user_id}` | @{username}\n"
            response += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        response += f"💎 **Total gastado:** ${total_spent} USD\n"
        response += f"🛍️ **Total compras:** {len(purchases)}"
        
        return response
        
    except Exception as e:
        return f"❌ Error buscando compras: {e}"


def get_discount_config():
    """Obtiene la configuración de descuentos"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT discount_enabled, discount_text, discount_multiplier, show_fake_price FROM discount_config WHERE id = 1;")
        result = cursor.fetchone()
        con.close()
        
        if result:
            return {
                'enabled': bool(result[0]),
                'text': result[1],
                'multiplier': result[2],
                'show_fake_price': bool(result[3])
            }
        else:
            # Configuración por defecto si no existe
            return {
                'enabled': True,
                'text': '🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥',
                'multiplier': 1.5,
                'show_fake_price': True
            }
    except:
        # Configuración por defecto en caso de error
        return {
            'enabled': True,
            'text': '🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥',
            'multiplier': 1.5,
            'show_fake_price': True
        }

def update_discount_config(enabled=None, text=None, multiplier=None, show_fake_price=None):
    """Actualiza la configuración de descuentos"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        # Crear tabla si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discount_config (
                id INTEGER PRIMARY KEY,
                discount_enabled INTEGER DEFAULT 1,
                discount_text TEXT DEFAULT '🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥',
                discount_multiplier REAL DEFAULT 1.5,
                show_fake_price INTEGER DEFAULT 1
            )
        ''')
        
        # Verificar si existe configuración
        cursor.execute("SELECT COUNT(*) FROM discount_config WHERE id = 1;")
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            # Crear configuración inicial
            cursor.execute("""
                INSERT INTO discount_config (id, discount_enabled, discount_text, discount_multiplier, show_fake_price)
                VALUES (1, 1, '🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥', 1.5, 1)
            """)
        
        # Actualizar campos especificados
        if enabled is not None:
            cursor.execute("UPDATE discount_config SET discount_enabled = ? WHERE id = 1;", (int(enabled),))
        
        if text is not None:
            cursor.execute("UPDATE discount_config SET discount_text = ? WHERE id = 1;", (text,))
            
        if multiplier is not None:
            cursor.execute("UPDATE discount_config SET discount_multiplier = ? WHERE id = 1;", (multiplier,))
            
        if show_fake_price is not None:
            cursor.execute("UPDATE discount_config SET show_fake_price = ? WHERE id = 1;", (int(show_fake_price),))
        
        con.commit()
        con.close()
        return True
        
    except Exception as e:
        print(f"Error actualizando configuración de descuentos: {e}")
        return False

def setup_discount_system():
    """Configura el sistema de descuentos por primera vez"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discount_config (
                id INTEGER PRIMARY KEY,
                discount_enabled INTEGER DEFAULT 1,
                discount_text TEXT DEFAULT '🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥',
                discount_multiplier REAL DEFAULT 1.5,
                show_fake_price INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM discount_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO discount_config 
                VALUES (1, 1, '🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥', 1.5, 1)
            """)
        
        con.commit()
        con.close()
        print("✅ Sistema de descuentos configurado")
        return True
        
    except Exception as e:
        print(f"Error configurando sistema de descuentos: {e}")
        return False

# ============================================
# FUNCIONES PARA DESCRIPCIÓN ADICIONAL
# Agregadas automáticamente por el instalador
# ============================================

def get_additional_description(good_name):
    """Obtiene la descripción adicional de un producto"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT additional_description FROM goods WHERE name = ?", (good_name,))
        result = cursor.fetchone()
        con.close()
        
        if result and result[0]:
            return result[0]
        else:
            return "No hay información adicional disponible para este producto."
    except Exception as e:
        print(f"Error obteniendo descripción adicional: {e}")
        return "Error al cargar información adicional."

def set_additional_description(good_name, additional_description):
    """Establece la descripción adicional de un producto"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("UPDATE goods SET additional_description = ? WHERE name = ?", 
                      (additional_description, good_name))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"Error estableciendo descripción adicional: {e}")
        return False

def get_product_full_info(good_name):
    """Obtiene toda la información del producto incluyendo descripción adicional"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            SELECT name, description, additional_description, format, minimum, price 
            FROM goods WHERE name = ?
        """, (good_name,))
        result = cursor.fetchone()
        con.close()
        
        if result:
            name, description, additional_desc, format, minimum, price = result
            return {
                'name': name,
                'description': description,
                'additional_description': additional_desc or '',
                'format': format,
                'minimum': minimum,
                'price': price
            }
        else:
            return None
    except Exception as e:
        print(f"Error obteniendo información completa del producto: {e}")
        return None

def format_product_basic_info(good_name):
    """Formatea la información básica del producto (sin descripción adicional)"""
    try:
        product_info = get_product_full_info(good_name)
        if not product_info:
            return "Producto no encontrado"
        
        amount = amount_of_goods(good_name)  # Usar función existente
        
        format_map = {'text': 'Texto', 'file': 'Archivo'}
        format_display = format_map.get(product_info['format'], product_info['format'])

        info_text = f"""🛍️ **{product_info['name']}**

📝 **Descripción:**
{product_info['description']}

💰 **Precio:** ${product_info['price']} USD
📦 **Cantidad mínima:** {product_info['minimum']}
📋 **Formato:** {format_display}
📊 **Disponibles:** {amount}"""

        if is_subscription_product(good_name):
            dur, unit = get_subscription_duration(good_name)
            if dur is not None:
                info_text += f"\n⏳ **Duración:** {dur} {unit}"

        return info_text
    except Exception as e:
        print(f"Error formateando información básica: {e}")
        return "Error al cargar información del producto"

def format_product_additional_info(good_name):
    """Formatea la información adicional del producto"""
    try:
        additional_desc = get_additional_description(good_name)
        
        info_text = f"""ℹ️ **Información Adicional**

{additional_desc}

━━━━━━━━━━━━━━━━━━━━━━"""
        
        return info_text
    except Exception as e:
        print(f"Error formateando información adicional: {e}")
        return "Error al cargar información adicional"

def has_additional_description(good_name):
    """Verifica si un producto tiene descripción adicional"""
    try:
        additional_desc = get_additional_description(good_name)
        return additional_desc and additional_desc.strip() != "" and additional_desc != "No hay información adicional disponible para este producto."
    except:
        return False

def save_product_media(product_name, file_id, media_type, caption=None):
    """Guardar información multimedia de un producto"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            UPDATE goods 
            SET media_file_id = ?, media_type = ?, media_caption = ?
            WHERE name = ?
        """, (file_id, media_type, caption, product_name))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"Error guardando multimedia: {e}")
        return False

def get_product_media(product_name):
    """Obtener información multimedia de un producto"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            SELECT media_file_id, media_type, media_caption 
            FROM goods 
            WHERE name = ?
        """, (product_name,))
        result = cursor.fetchone()
        con.close()
        
        if result and result[0]:
            return {
                'file_id': result[0],
                'type': result[1],
                'caption': result[2]
            }
        return None
    except Exception as e:
        print(f"Error obteniendo multimedia: {e}")
        return None

def has_product_media(product_name):
    """Verificar si un producto tiene multimedia"""
    media_info = get_product_media(product_name)
    return media_info is not None

def remove_product_media(product_name):
    """Eliminar multimedia de un producto"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            UPDATE goods 
            SET media_file_id = NULL, media_type = NULL, media_caption = NULL
            WHERE name = ?
        """, (product_name,))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"Error eliminando multimedia: {e}")
        return False

def get_products_with_media():
    """Obtener lista de productos que tienen multimedia"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            SELECT name, media_type 
            FROM goods 
            WHERE media_file_id IS NOT NULL
        """)
        results = cursor.fetchall()
        con.close()
        return results
    except Exception as e:
        print(f"Error obteniendo productos con multimedia: {e}")
        return []

def get_products_without_media():
    """Obtener lista de productos que NO tienen multimedia"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            SELECT name 
            FROM goods 
            WHERE media_file_id IS NULL
        """)
        results = cursor.fetchall()
        con.close()
        return [row[0] for row in results]
    except Exception as e:
        print(f"Error obteniendo productos sin multimedia: {e}")
        return []

def format_product_with_media(product_name):
    """Formatear información del producto incluyendo multimedia"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            SELECT name, description, price, media_file_id, media_type, media_caption
            FROM goods 
            WHERE name = ?
        """, (product_name,))
        result = cursor.fetchone()
        con.close()
        
        if not result:
            return None
            
        name, description, price, file_id, media_type, caption = result

        info = f"🎯 **{name}**\n"
        info += f"💰 **Precio:** ${price} USD\n"
        info += f"📝 **Descripción:** {description}\n"

        if is_subscription_product(name):
            dur, unit = get_subscription_duration(name)
            if dur is not None:
                info += f"⏳ **Duración:** {dur} {unit}\n"

        if file_id:
            media_types = {
                'photo': '📸 Imagen',
                'video': '🎥 Video', 
                'document': '📄 Documento',
                'audio': '🎵 Audio',
                'animation': '🎬 GIF'
            }
            media_name = media_types.get(media_type, '📎 Archivo')
            info += f"\n{media_name} disponible"
            
            if caption:
                info += f"\n*{caption}*"
        
        return info
        
    except Exception as e:
        print(f"Error formateando producto: {e}")
        return None


def is_subscription_product(product_name):
    """Verificar si un producto es una suscripción"""
    try:
        con = sqlite3.connect(files.main_db)
        cur = con.cursor()
        cur.execute(
            "SELECT is_subscription FROM goods WHERE name = ?", (product_name,)
        )
        row = cur.fetchone()
        con.close()
        return row is not None and row[0] == 1
    except Exception:
        return False


def get_subscription_duration(product_name):
    """Obtener la duración y unidad de una suscripción"""
    try:
        con = sqlite3.connect(files.main_db)
        cur = con.cursor()
        cur.execute(
            "SELECT duration, duration_unit FROM goods WHERE name = ?",
            (product_name,),
        )
        row = cur.fetchone()
        con.close()
        if row:
            return row[0], row[1]
        return None, None
    except Exception:
        return None, None


def format_subscription_info(product_name):
    """Formatear información de suscripción"""
    dur, unit = get_subscription_duration(product_name)
    if dur is None:
        return ""
    return f"⏳ *Duración:* {dur} {unit}"
