import telebot, shelve, datetime, sqlite3, random, os
import files, config
import db
from bot_instance import bot

# ---------------------------------------------------------------------------
# Utilidad para asegurar que la base de datos tenga las columnas necesarias
# para la descripción adicional y la gestión de multimedia. Algunas
# instalaciones antiguas pueden carecer de estas columnas y provocar errores
# "no such column" cuando se utilizan las funciones relacionadas. Esta función
# se ejecuta al importar el módulo y modifica la tabla `goods` si es necesario.
# ---------------------------------------------------------------------------
def ensure_database_schema():
    """Agregar tablas y columnas faltantes si es necesario."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()

        # Tabla de tiendas
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                name TEXT UNIQUE NOT NULL
            )
            """
        )

        cursor.execute("PRAGMA table_info(categories)")
        cat_cols = [c[1] for c in cursor.fetchall()]
        if "shop_id" not in cat_cols:
            try:
                cursor.execute("ALTER TABLE categories ADD COLUMN shop_id INTEGER DEFAULT 1")
            except sqlite3.OperationalError:
                pass

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, shop_id INTEGER)"
        )

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
        if 'duration_days' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN duration_days INTEGER DEFAULT NULL")
            updated = True
        if 'manual_delivery' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN manual_delivery INTEGER DEFAULT 0")
            updated = True
        if 'category_id' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN category_id INTEGER")
            updated = True
        if 'shop_id' not in columns:
            cursor.execute("ALTER TABLE goods ADD COLUMN shop_id INTEGER DEFAULT 1")
            updated = True

        cursor.execute("PRAGMA table_info(campaigns)")
        camp_cols = [c[1] for c in cursor.fetchall()]
        if 'shop_id' not in camp_cols:
            try:
                cursor.execute("ALTER TABLE campaigns ADD COLUMN shop_id INTEGER DEFAULT 1")
                updated = True
            except sqlite3.OperationalError:
                pass

        cursor.execute("PRAGMA table_info(purchases)")
        purch_cols = [c[1] for c in cursor.fetchall()]
        if 'shop_id' not in purch_cols:
            try:
                cursor.execute("ALTER TABLE purchases ADD COLUMN shop_id INTEGER DEFAULT 1")
                updated = True
            except sqlite3.OperationalError:
                pass

        cursor.execute("PRAGMA table_info(buyers)")
        buyer_cols = [c[1] for c in cursor.fetchall()]
        if 'shop_id' not in buyer_cols:
            try:
                cursor.execute("ALTER TABLE buyers ADD COLUMN shop_id INTEGER DEFAULT 1")
                updated = True
            except sqlite3.OperationalError:
                pass

        if updated:
            con.commit()
        con.commit()
    except Exception as e:
        print(f"Error asegurando esquema de base de datos: {e}")
ensure_database_schema()

# -------------------------------------------------
# Utilidad para editar mensajes con o sin multimedia
# -------------------------------------------------
def safe_edit_message(bot, message, text, reply_markup=None, parse_mode=None):
    """TRIPLE_FALLBACK - Edita mensajes de forma segura"""
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except:
        try:
            bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=message.message_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        except:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(
                    chat_id=message.chat.id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                return True
            except:
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
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM goods;")
        product_count = cursor.fetchone()[0]
        
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

def get_goods(shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT name FROM goods WHERE shop_id = ?;", (shop_id,))
        goods = []
        for row in cursor.fetchall():
            goods.append(row[0])
        return goods
    except:
        return []

def list_categories(shop_id=1):
    """Devuelve lista de categorías (id, nombre)."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, name FROM categories WHERE shop_id = ? ORDER BY name",
            (shop_id,),
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Error listando categorías: {e}")
        return []

def create_category(name, shop_id=1):
    """Crear una categoría y devolver su ID."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO categories (name, shop_id) VALUES (?, ?)",
            (name, shop_id),
        )
        con.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute(
            "SELECT id FROM categories WHERE name = ? AND shop_id = ?",
            (name, shop_id),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"Error creando categoría: {e}")
        return None

def get_category_id(name, shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id FROM categories WHERE name = ? AND shop_id = ?",
            (name, shop_id),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"Error obteniendo id de categoría: {e}")
        return None

def get_category_name(cat_id, shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT name FROM categories WHERE id = ? AND shop_id = ?",
            (cat_id, shop_id),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"Error obteniendo nombre de categoría: {e}")
        return None

def assign_product_category(product, category_id, shop_id=1):
    """Asigna una categoría a un producto."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "UPDATE goods SET category_id = ? WHERE name = ? AND shop_id = ?",
            (category_id, product, shop_id),
        )
        con.commit()
        return True
    except Exception as e:
        print(f"Error asignando categoría: {e}")
        return False

def get_stored(name_good, shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT stored FROM goods WHERE name = ? AND shop_id = ?;",
            (name_good, shop_id),
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    except:
        return None

def amount_of_goods(name_good, shop_id=1):
    if is_manual_delivery(name_good, shop_id):
        return 10 ** 9
    stored = get_stored(name_good, shop_id)
    if not stored:
        return 0
    try:
        with open(stored, encoding='utf-8') as f:
            lines = f.readlines()
            return len([line for line in lines if line.strip()])
    except:
        return 0

def get_stock_overview(shop_id=1):
    """Return a list with stock summary lines for all products."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT name, price FROM goods WHERE shop_id = ?;", (shop_id,))
        goods = cursor.fetchall()

        overview = []
        for i, (name, price) in enumerate(goods, start=1):
            count = amount_of_goods(name, shop_id)
            overview.append(f"{i}. {name} — {count} unidades (${price} USD)")

        return overview
    except Exception as e:
        print(f"Error generando resumen de stock: {e}")
        return []

def get_minimum(name_good, shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT minimum FROM goods WHERE name = ? AND shop_id = ?;",
            (name_good, shop_id),
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        return 1
    except:
        return 1

def order_sum(name_good, amount, shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT price FROM goods WHERE name = ? AND shop_id = ?;",
            (name_good, shop_id),
        )
        result = cursor.fetchone()
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

def get_goodformat(name_good, shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT format FROM goods WHERE name = ? AND shop_id = ?;",
            (name_good, shop_id),
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        return 'text'
    except:
        return 'text'

def get_profit(shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT price FROM purchases WHERE shop_id = ?;", (shop_id,))
        price_amount = 0
        for row in cursor.fetchall(): 
            price_amount += int(row[0])
        return price_amount
    except:
        return 0

def get_amountsbayers(shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM buyers WHERE shop_id = ?;", (shop_id,))
        result = cursor.fetchone()
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

def rasl(group, amount, text, shop_id=1):
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
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute(
                "SELECT id FROM buyers WHERE shop_id = ? LIMIT ?;",
                (shop_id, int(amount))
            )
            buyers = cursor.fetchall()
            
            for buyer in buyers:
                chat_id = int(buyer[0])
                try:
                    bot.send_message(chat_id, text)
                    good_send += 1
                except: 
                    lose_send += 1
                    new_blockuser(chat_id)
        except:
            pass

    return f'¡{good_send} usuarios recibieron el mensaje exitosamente!\n{lose_send} usuarios bloquearon el bot y fueron agregados a la lista de usuarios bloqueados'


def _send_media_message(chat_id, text, media):
    """Enviar un mensaje multimedia según el tipo especificado."""
    mtype = media.get('type')
    fid = media.get('file_id')
    caption = media.get('caption') or text

    if mtype == 'photo':
        bot.send_photo(chat_id, fid, caption=caption)
    elif mtype == 'video':
        bot.send_video(chat_id, fid, caption=caption)
    elif mtype == 'document':
        bot.send_document(chat_id, fid, caption=caption)
    elif mtype == 'audio':
        bot.send_audio(chat_id, fid, caption=caption)
    elif mtype == 'animation':
        bot.send_animation(chat_id, fid, caption=caption)
    else:
        bot.send_message(chat_id, text)


def broadcast_message(group, amount, text, media=None, shop_id=1):
    """Enviar un anuncio masivo a usuarios o compradores."""
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
                    if media:
                        _send_media_message(chat_id, text, media)
                    else:
                        bot.send_message(chat_id, text)
                    good_send += 1
                except Exception:
                    lose_send += 1
                    new_blockuser(chat_id)
                i += 1
        except Exception:
            pass

    elif group == 'buyers':
        try:
            con = db.get_db_connection()
            cursor = con.cursor()
            cursor.execute(
                "SELECT id FROM buyers WHERE shop_id = ? LIMIT ?;",
                (shop_id, int(amount))
            )
            buyers = cursor.fetchall()

            for buyer in buyers:
                chat_id = int(buyer[0])
                try:
                    if media:
                        _send_media_message(chat_id, text, media)
                    else:
                        bot.send_message(chat_id, text)
                    good_send += 1
                except Exception:
                    lose_send += 1
                    new_blockuser(chat_id)
        except Exception:
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
        con = db.get_db_connection()
        cur = con.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO shops (admin_id, name) VALUES (?, ?)",
            (his_id, f'Shop {his_id}'),
        )
        con.commit()
    except:
        with open(files.admins_list, 'w', encoding='utf-8') as f:
            f.write(str(his_id) + '\n')

def get_shop_id(admin_id):
    """Obtener el ID de tienda asociado a un admin."""
    try:
        con = db.get_db_connection()
        cur = con.cursor()
        cur.execute("SELECT id FROM shops WHERE admin_id = ?", (admin_id,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO shops (admin_id, name) VALUES (?, ?)",
            (admin_id, f'Shop {admin_id}')
        )
        con.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"Error obteniendo shop_id: {e}")
        return 1

def list_shops():
    """Listar todas las tiendas registradas."""
    try:
        con = db.get_db_connection()
        cur = con.cursor()
        cur.execute("SELECT id, admin_id, name FROM shops ORDER BY id")
        return cur.fetchall()
    except Exception as e:
        print(f"Error listando tiendas: {e}")
        return []

def create_shop(name, admin_id=None):
    """Crear una nueva tienda y devolver su ID."""
    try:
        con = db.get_db_connection()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO shops (admin_id, name) VALUES (?, ?)",
            (admin_id, name)
        )
        con.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"Error creando tienda: {e}")
        return None

def assign_admin_to_shop(shop_id, admin_id):
    """Asignar un administrador existente a una tienda."""
    try:
        con = db.get_db_connection()
        cur = con.cursor()
        cur.execute(
            "UPDATE shops SET admin_id = ? WHERE id = ?",
            (admin_id, shop_id)
        )
        con.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"Error asignando admin a tienda: {e}")
        return False

def update_shop_name(shop_id, new_name):
    """Cambiar el nombre de una tienda."""
    try:
        con = db.get_db_connection()
        cur = con.cursor()
        cur.execute(
            "UPDATE shops SET name = ? WHERE id = ?",
            (new_name, shop_id),
        )
        con.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"Error actualizando nombre de tienda: {e}")
        return False

# ------------------------------------------------------------------
# Funciones para la tienda seleccionada por cada usuario
# ------------------------------------------------------------------

def set_user_shop(user_id, shop_id):
    """Guardar la tienda elegida por un usuario."""
    try:
        with shelve.open(files.user_shops_bd) as bd:
            bd[str(user_id)] = int(shop_id)
    except Exception:
        pass


def get_user_shop(user_id):
    """Obtener la tienda seleccionada por un usuario (por defecto 1)."""
    try:
        with shelve.open(files.user_shops_bd) as bd:
            return bd.get(str(user_id), 1)
    except Exception:
        return 1

def get_description(name_good):
    """Descripción del producto con sistema de descuentos"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT description, price, duration_days FROM goods WHERE name = ?;", (name_good,))
        result = cursor.fetchone()

        if not result:
            return "Producto no encontrado"

        description, price, duration = result
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
        if duration not in (None, 0):
            product_description += f"⏳ *Duración:* {duration} días\n"
        product_description += f"🛒 *Mínimo de compra:* {get_minimum(name_good)} unidades"
        
        return product_description
        
    except Exception as e:
        print(f"Error obteniendo descripción: {e}")
        return "Error obteniendo información del producto"

def get_paypaldata(shop_id=1):
    """Obtener credenciales PayPal asociadas a una tienda."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT client_id, client_secret, sandbox FROM paypal_data WHERE shop_id = ? ORDER BY rowid DESC LIMIT 1;",
            (shop_id,),
        )
        result = cursor.fetchone()
        if result:
            return result[0], result[1], bool(result[2])
        return None
    except Exception:
        return None

def get_binancedata(shop_id=1):
    """Obtener credenciales Binance asociadas a una tienda."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT api_key, api_secret, merchant_id FROM binance_data WHERE shop_id = ? ORDER BY rowid DESC LIMIT 1;",
            (shop_id,),
        )
        result = cursor.fetchone()
        if result:
            return result[0], result[1], result[2]
        return None
    except Exception:
        return None

def save_paypaldata(client_id, client_secret, sandbox=1, shop_id=1):
    """Guardar o actualizar credenciales PayPal para una tienda."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("DELETE FROM paypal_data WHERE shop_id = ?", (shop_id,))
        cursor.execute(
            "INSERT INTO paypal_data (client_id, client_secret, sandbox, shop_id) VALUES (?, ?, ?, ?)",
            (client_id, client_secret, int(bool(sandbox)), shop_id),
        )
        con.commit()
        return True
    except Exception as e:
        print(f"Error guardando PayPal data: {e}")
        return False

def save_binancedata(api_key, api_secret, merchant_id, shop_id=1):
    """Guardar o actualizar credenciales Binance para una tienda."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("DELETE FROM binance_data WHERE shop_id = ?", (shop_id,))
        cursor.execute(
            "INSERT INTO binance_data (api_key, api_secret, merchant_id, shop_id) VALUES (?, ?, ?, ?)",
            (api_key, api_secret, merchant_id, shop_id),
        )
        con.commit()
        return True
    except Exception as e:
        print(f"Error guardando Binance data: {e}")
        return False

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

def payments_checkvkl(shop_id=1):
    """Verificar métodos de pago activos para una tienda."""
    active_payment = []
    
    # Verificar PayPal
    if check_vklpayments('paypal') == '✅' and get_paypaldata(shop_id) != None:
        active_payment.append('paypal')
    elif check_vklpayments('paypal') == '✅' and get_paypaldata(shop_id) == None:
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
    if check_vklpayments('binance') == '✅' and get_binancedata(shop_id) != None:
        active_payment.append('binance')
    elif check_vklpayments('binance') == '✅' and get_binancedata(shop_id) == None:
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

def new_buy(his_id, username, name_good, amount, price, shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO purchases VALUES(?, ?, ?, ?, ?, ?)",
            (his_id, username, name_good, amount, price, shop_id)
        )
        con.commit()
    except:
        pass

def new_buyer(his_id, username, payed, shop_id=1):
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        
        cursor.execute("SELECT payed FROM buyers WHERE id = ? AND shop_id = ?;", (his_id, shop_id))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute(
                "INSERT INTO buyers VALUES(?, ?, ?, ?)",
                (his_id, username, payed, shop_id)
            )
        else:
            total_payed = int(result[0]) + int(payed)
            cursor.execute(
                "UPDATE buyers SET payed = ? WHERE id = ? AND shop_id = ?;",
                (total_payed, his_id, shop_id)
            )
        
        con.commit()
    except:
        pass
def new_buy_improved(his_id, username, name_good, amount, price, payment_method="Unknown", payment_id=None, shop_id=1):
    """Versión mejorada de new_buy que incluye método de pago y timestamp"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        
        # Usar timestamp actual
        from datetime import datetime
        current_time = datetime.now().isoformat()
        
        cursor.execute(
            """
            INSERT INTO purchases
            (id, username, name_good, amount, price, payment_method, timestamp, shop_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (his_id, username, name_good, amount, price, payment_method, current_time, shop_id)
        )
        
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
        return True
    except Exception as e:
        print(f"Error en new_buy_improved: {e}")
        return False

def get_daily_sales(shop_id=1):
    """Obtiene las ventas del día actual"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        
        # Obtener ventas recientes (aproximación por rowid)
        cursor.execute(
            """
            SELECT COUNT(*), SUM(price)
            FROM purchases
            WHERE shop_id = ?
            ORDER BY rowid DESC
            LIMIT 100
            """,
            (shop_id,)
        )
        
        count, total = cursor.fetchone()
        
        cursor.execute(
            """
            SELECT name_good, COUNT(*), SUM(price)
            FROM purchases
            WHERE shop_id = ?
            GROUP BY name_good
            ORDER BY COUNT(*) DESC
            LIMIT 10
            """,
            (shop_id,)
        )
        
        products = cursor.fetchall()
        
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

def search_user_purchases(search_term, shop_id=1):
    """Busca compras por ID de usuario o username"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        
        # Si es número, buscar por ID
        if search_term.isdigit():
            cursor.execute(
                """
                SELECT id, username, name_good, amount, price, payment_method, timestamp
                FROM purchases
                WHERE id = ? AND shop_id = ?
                ORDER BY rowid DESC
                """,
                (int(search_term), shop_id),
            )
        else:
            # Si no, buscar por username
            clean_username = search_term.replace('@', '')
            cursor.execute(
                """
                SELECT id, username, name_good, amount, price, payment_method, timestamp
                FROM purchases
                WHERE username LIKE ? AND shop_id = ?
                ORDER BY rowid DESC
                """,
                (f"%{clean_username}%", shop_id),
            )
        
        purchases = cursor.fetchall()
        
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


def get_user_purchases(user_id, shop_id=1):
    con = db.get_db_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT name_good, amount, price FROM purchases "
        "WHERE id = ? AND shop_id = ? ORDER BY rowid DESC",
        (user_id, shop_id),
    )
    rows = cursor.fetchall()
    if not rows:
        return "❌ No tienes compras registradas."
    response = "📋 **Tus compras:**\n\n"
    total = 0
    for idx, (product, qty, price) in enumerate(rows, 1):
        total += price
        response += (
            f"🛒 **Compra #{idx}**\n"
            f"📦 {product} x{qty}\n"
            f"💰 ${price} USD\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )
    response += f"\n💎 **Total gastado:** ${total} USD"
    return response


def get_discount_config():
    """Obtiene la configuración de descuentos"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT discount_enabled, discount_text, discount_multiplier, show_fake_price FROM discount_config WHERE id = 1;")
        result = cursor.fetchone()
        
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
        con = db.get_db_connection()
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
        return True
        
    except Exception as e:
        print(f"Error actualizando configuración de descuentos: {e}")
        return False

def setup_discount_system():
    """Configura el sistema de descuentos por primera vez"""
    try:
        con = db.get_db_connection()
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
        print("✅ Sistema de descuentos configurado")
        return True
        
    except Exception as e:
        print(f"Error configurando sistema de descuentos: {e}")
        return False

# ============================================
# FUNCIONES PARA DESCRIPCIÓN ADICIONAL
# Agregadas automáticamente por el instalador
# ============================================

def get_additional_description(good_name, shop_id=1):
    """Obtiene la descripción adicional de un producto"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT additional_description FROM goods WHERE name = ? AND shop_id = ?", (good_name, shop_id))
        result = cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        else:
            return "No hay información adicional disponible para este producto."
    except Exception as e:
        print(f"Error obteniendo descripción adicional: {e}")
        return "Error al cargar información adicional."

def set_additional_description(good_name, additional_description, shop_id=1):
    """Establece la descripción adicional de un producto"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("UPDATE goods SET additional_description = ? WHERE name = ? AND shop_id = ?",
                      (additional_description, good_name, shop_id))
        con.commit()
        return True
    except Exception as e:
        print(f"Error estableciendo descripción adicional: {e}")
        return False

def get_duration_days(product_name, shop_id=1):
    """Devuelve la duración en días de un producto."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT duration_days FROM goods WHERE name = ? AND shop_id = ?",
            (product_name, shop_id),
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"Error obteniendo duración: {e}")
        return None

def set_duration_days(product_name, days, shop_id=1):
    """Establece la duración en días de un producto."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "UPDATE goods SET duration_days = ? WHERE name = ? AND shop_id = ?",
            (days, product_name, shop_id),
        )
        con.commit()
        return True
    except Exception as e:
        print(f"Error estableciendo duración: {e}")
        return False

def is_manual_delivery(product_name, shop_id=1):
    """Indica si un producto requiere entrega manual."""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT manual_delivery FROM goods WHERE name = ? AND shop_id = ?",
            (product_name, shop_id),
        )
        result = cursor.fetchone()
        return bool(result and result[0])
    except Exception as e:
        print(f"Error comprobando entrega manual: {e}")
        return False

def get_manual_delivery_message(username, name):
    """Obtiene el mensaje de entrega manual personalizado."""
    try:
        with shelve.open(files.bot_message_bd) as bd:
            text = bd.get('manual_delivery', 'Gracias por su compra, username')
    except Exception:
        text = 'Gracias por su compra, username'
    text = text.replace('username', username).replace('name', name)
    return text

def get_product_full_info(good_name, shop_id=1):
    """Obtiene toda la información del producto incluyendo descripción adicional"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT g.name, g.description, g.additional_description, g.format, g.minimum, g.price,
                   g.duration_days, g.manual_delivery, c.name
            FROM goods g LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.name = ? AND g.shop_id = ?
        """,
            (good_name, shop_id),
        )
        result = cursor.fetchone()

        if result:
            name, description, additional_desc, format, minimum, price, duration_days, manual, category = result
            return {
                'name': name,
                'description': description,
                'additional_description': additional_desc or '',
                'format': format,
                'minimum': minimum,
                'price': price,
                'duration_days': duration_days,
                'manual_delivery': bool(manual),
                'category': category,
            }
        else:
            return None
    except Exception as e:
        print(f"Error obteniendo información completa del producto: {e}")
        return None

def format_product_basic_info(good_name, shop_id=1):
    """Formatea la información básica del producto (sin descripción adicional)"""
    try:
        product_info = get_product_full_info(good_name, shop_id)
        if not product_info:
            return "Producto no encontrado"
        
        amount = amount_of_goods(good_name, shop_id)
        
        format_map = {'text': 'Texto', 'file': 'Archivo'}
        format_display = format_map.get(product_info['format'], product_info['format'])

        info_text = f"""🛍️ **{product_info['name']}**

📝 **Descripción:**
{product_info['description']}"""

        if product_info.get('category'):
            info_text += f"\n🏷️ **Categoría:** {product_info['category']}"

        info_text += f"""

💰 **Precio:** ${product_info['price']} USD
📦 **Cantidad mínima:** {product_info['minimum']}
📋 **Formato:** {format_display}"""

        if product_info.get('manual_delivery'):
            info_text += "\n🚚 **Entrega manual**"
        else:
            info_text += f"\n📊 **Disponibles:** {amount}"

        duration = product_info.get('duration_days')
        if duration not in (None, 0):
            info_text += f"\n⏳ **Duración:** {duration} días"
        
        return info_text
    except Exception as e:
        print(f"Error formateando información básica: {e}")
        return "Error al cargar información del producto"

def format_product_additional_info(good_name, shop_id=1):
    """Formatea la información adicional del producto"""
    try:
        additional_desc = get_additional_description(good_name, shop_id)
        
        info_text = f"""ℹ️ **Información Adicional**

{additional_desc}

━━━━━━━━━━━━━━━━━━━━━━"""
        
        return info_text
    except Exception as e:
        print(f"Error formateando información adicional: {e}")
        return "Error al cargar información adicional"

def has_additional_description(good_name, shop_id=1):
    """Verifica si un producto tiene descripción adicional"""
    try:
        additional_desc = get_additional_description(good_name, shop_id)
        return additional_desc and additional_desc.strip() != "" and additional_desc != "No hay información adicional disponible para este producto."
    except:
        return False

def save_product_media(product_name, file_id, media_type, caption=None):
    """Guardar información multimedia de un producto"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute("""
            UPDATE goods 
            SET media_file_id = ?, media_type = ?, media_caption = ?
            WHERE name = ?
        """, (file_id, media_type, caption, product_name))
        con.commit()
        return True
    except Exception as e:
        print(f"Error guardando multimedia: {e}")
        return False

def get_product_media(product_name, shop_id=1):
    """Obtener información multimedia de un producto para una tienda"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT media_file_id, media_type, media_caption
            FROM goods
            WHERE name = ? AND shop_id = ?
        """,
            (product_name, shop_id),
        )
        result = cursor.fetchone()
        
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

def has_product_media(product_name, shop_id=1):
    """Verificar si un producto tiene multimedia para la tienda indicada"""
    media_info = get_product_media(product_name, shop_id)
    return media_info is not None

def remove_product_media(product_name, shop_id=1):
    """Eliminar multimedia de un producto de una tienda"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            """
            UPDATE goods
            SET media_file_id = NULL, media_type = NULL, media_caption = NULL
            WHERE name = ? AND shop_id = ?
        """,
            (product_name, shop_id),
        )
        con.commit()
        return True
    except Exception as e:
        print(f"Error eliminando multimedia: {e}")
        return False

def get_products_with_media(shop_id=1):
    """Obtener lista de productos que tienen multimedia"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT name, media_type FROM goods WHERE media_file_id IS NOT NULL AND shop_id = ?",
            (shop_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Error obteniendo productos con multimedia: {e}")
        return []

def get_products_without_media(shop_id=1):
    """Obtener lista de productos que NO tienen multimedia"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT name FROM goods WHERE media_file_id IS NULL AND shop_id = ?",
            (shop_id,)
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error obteniendo productos sin multimedia: {e}")
        return []

def format_product_with_media(product_name, shop_id=1):
    """Formatear información del producto incluyendo multimedia"""
    try:
        con = db.get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT g.name, g.description, g.price, g.media_file_id, g.media_type, g.media_caption,
                   g.duration_days, g.manual_delivery, c.name
            FROM goods g LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.name = ? AND g.shop_id = ?
        """,
            (product_name, shop_id),
        )
        result = cursor.fetchone()
        
        if not result:
            return None
            
        name, description, price, file_id, media_type, caption, duration, manual, category = result

        info = f"🎯 **{name}**\n"
        info += f"💰 **Precio:** ${price} USD\n"
        info += f"📝 **Descripción:** {description}\n"
        if category:
            info += f"🏷️ **Categoría:** {category}\n"
        if duration not in (None, 0):
            info += f"⏳ **Duración:** {duration} días\n"

        if manual:
            info += "🚚 **Entrega manual**\n"

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

def save_message(message_type, message_text):
    """Guardar mensaje del bot"""
    try:
        with shelve.open(files.bot_message_bd) as bd:
            bd[message_type] = message_text
        return True
    except Exception as e:
        print(f"Error guardando mensaje: {e}")
        return False
