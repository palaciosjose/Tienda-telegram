"""Módulo de gestión de productos por suscripción"""

import sqlite3
from datetime import datetime, timedelta
import files
import telebot
import config
import dop
import os
from bot_instance import bot

# Días de notificación por defecto (30, 15, 7 y 1 día antes)
DEFAULT_NOTIFICATION_DAYS = '30,15,7,1'


# ---------------------------------------------------------------------------
# Inicialización de base de datos
# ---------------------------------------------------------------------------

def init_subscription_db():
    """Crear tablas necesarias para el sistema de suscripciones"""
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()

    cursor.execute(
        f'''CREATE TABLE IF NOT EXISTS subscription_products (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT UNIQUE,
               description TEXT,
               price INTEGER,
               currency TEXT DEFAULT 'USD',
               duration INTEGER,
               duration_unit TEXT DEFAULT 'days',
               service_type TEXT,
               status TEXT DEFAULT 'active',
               grace_period INTEGER DEFAULT 0,
               auto_renew INTEGER DEFAULT 1,
               early_discount INTEGER DEFAULT 0,
               notification_days TEXT DEFAULT "{DEFAULT_NOTIFICATION_DAYS}",
               additional_description TEXT DEFAULT '',
               media_file_id TEXT,
               media_type TEXT,
               media_caption TEXT,
               delivery_format TEXT DEFAULT 'none',
               delivery_content TEXT
        )'''
    )

    # Asegurar columnas adicionales por compatibilidad
    cursor.execute("PRAGMA table_info(subscription_products)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    alter_commands = []
    if 'additional_description' not in existing_cols:
        alter_commands.append("ALTER TABLE subscription_products ADD COLUMN additional_description TEXT DEFAULT ''")
    if 'media_file_id' not in existing_cols:
        alter_commands.append("ALTER TABLE subscription_products ADD COLUMN media_file_id TEXT")
    if 'media_type' not in existing_cols:
        alter_commands.append("ALTER TABLE subscription_products ADD COLUMN media_type TEXT")
    if 'media_caption' not in existing_cols:
        alter_commands.append("ALTER TABLE subscription_products ADD COLUMN media_caption TEXT")
    if 'delivery_format' not in existing_cols:
        alter_commands.append("ALTER TABLE subscription_products ADD COLUMN delivery_format TEXT DEFAULT 'none'")
    if 'delivery_content' not in existing_cols:
        alter_commands.append("ALTER TABLE subscription_products ADD COLUMN delivery_content TEXT")

    for cmd in alter_commands:
        try:
            cursor.execute(cmd)
        except Exception:
            pass

    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS user_subscriptions (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER,
               product_id INTEGER,
               start_date TEXT,
               end_date TEXT,
               status TEXT DEFAULT 'active',
               payment_method TEXT,
               renewal_history TEXT
        )'''
    )

    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_user_subscriptions_end_date '
        'ON user_subscriptions(end_date)'
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Funciones de administración de productos de suscripción
# ---------------------------------------------------------------------------

def add_subscription_product(name, description, price, duration,
                             currency='USD', duration_unit='days',
                             service_type='default', status='active',
                             grace_period=0, auto_renew=True,
                             early_discount=0,
                             notification_days=DEFAULT_NOTIFICATION_DAYS,
                             additional_description='',
                             media_file_id=None, media_type=None,
                             media_caption=None,
                             delivery_format='none',
                             delivery_content=None):
    """Agregar un nuevo producto de suscripción"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO subscription_products
           (name, description, price, currency, duration, duration_unit,
            service_type, status, grace_period, auto_renew,
            early_discount, notification_days,
            additional_description, media_file_id, media_type,
            media_caption, delivery_format, delivery_content)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (name, description, price, currency, duration, duration_unit,
         service_type, status, grace_period, int(auto_renew),
         early_discount, notification_days,
         additional_description, media_file_id, media_type,
         media_caption, delivery_format, delivery_content)
    )
    conn.commit()
    conn.close()
    return True


def get_subscription_product(product_id):
    """Obtener información de un producto de suscripción"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM subscription_products WHERE id = ?', (product_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_all_subscription_products():
    """Obtener todos los planes de suscripción disponibles"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subscription_products')
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_plan_media(plan_name):
    """Obtener información multimedia asociada a un plan"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT media_file_id, media_type, media_caption FROM subscription_products WHERE name = ?",
        (plan_name,)
    )
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return {'file_id': row[0], 'type': row[1], 'caption': row[2]}
    return None


def save_plan_media(plan_name, file_id, media_type, caption=None):
    """Guardar multimedia para un plan"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE subscription_products SET media_file_id=?, media_type=?, media_caption=? WHERE name=?",
            (file_id, media_type, caption, plan_name),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def remove_plan_media(plan_name):
    """Eliminar multimedia de un plan"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE subscription_products SET media_file_id=NULL, media_type=NULL, media_caption=NULL WHERE name=?",
            (plan_name,),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def has_plan_media(plan_name):
    return get_plan_media(plan_name) is not None


def get_plans_with_media():
    """Listar planes con multimedia"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT name, media_type FROM subscription_products WHERE media_file_id IS NOT NULL"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_plans_without_media():
    """Listar planes sin multimedia"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM subscription_products WHERE media_file_id IS NULL"
    )
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def get_delivery_info(plan_id):
    """Obtener información de entrega de un plan"""
    plan = get_subscription_product(plan_id)
    if not plan:
        return None, None
    delivery_format = plan[17] if len(plan) > 17 else 'none'
    delivery_content = plan[18] if len(plan) > 18 else None
    return delivery_format, delivery_content


def set_delivery_info(plan_name, delivery_format, delivery_content):
    """Actualizar información de entrega"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE subscription_products SET delivery_format=?, delivery_content=? WHERE name=?",
            (delivery_format, delivery_content, plan_name),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_additional_description(plan_name):
    """Obtener descripción adicional de un plan"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT additional_description FROM subscription_products WHERE name=?",
        (plan_name,),
    )
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return ""


def set_additional_description(plan_name, desc):
    """Actualizar descripción adicional de un plan"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE subscription_products SET additional_description=? WHERE name=?",
            (desc, plan_name),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def has_additional_description(plan_name):
    desc = get_additional_description(plan_name)
    return bool(desc and desc.strip())


def format_plan_with_media(plan_id):
    """Formatear información de un plan para mostrar al usuario"""
    plan = get_subscription_product(plan_id)
    if not plan:
        return None
    (
        _pid,
        name,
        desc,
        price,
        currency,
        duration,
        unit,
        *_rest,
        additional_desc,
        media_file_id,
        media_type,
        media_caption,
        _delivery_format,
        _delivery_content,
    ) = plan
    info = f"**{name}**\n\n{desc}\n\nPrecio: {price} {currency}\nDuración: {duration} {unit}"
    if media_file_id:
        media_types = {
            'photo': '📸',
            'video': '🎥',
            'document': '📄',
            'audio': '🎵',
            'animation': '🎬',
        }
        info += f"\n{media_types.get(media_type, '📎')}"
        if media_caption:
            info += f" {media_caption}"
    return info


def format_plan_additional_info(plan_id):
    plan = get_subscription_product(plan_id)
    if not plan:
        return None
    additional_desc = plan[13] if len(plan) > 13 else ''
    if not additional_desc:
        return 'No hay información adicional disponible'
    return additional_desc


# ---------------------------------------------------------------------------
# Funciones para manejar suscripciones de clientes
# ---------------------------------------------------------------------------

def create_user_subscription(user_id, product_id, payment_method,
                             start_date=None):
    """Crear registro de suscripción para un usuario"""
    init_subscription_db()
    product = get_subscription_product(product_id)
    if not product:
        return False

    _, _, _, price, currency, duration, duration_unit, _, _, grace_period, \
        auto_renew, early_discount, notification_days = product

    if start_date is None:
        start_date = datetime.utcnow()
    end_date = start_date + timedelta(**{duration_unit: duration})

    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO user_subscriptions
           (user_id, product_id, start_date, end_date, status, payment_method,
            renewal_history)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (user_id, product_id, start_date.isoformat(), end_date.isoformat(),
         'active', payment_method, '')
    )
    conn.commit()
    conn.close()
    return True


def renew_subscription(subscription_id, apply_early_discount=False):
    """Renovar una suscripción existente.

    Si ``apply_early_discount`` es ``True`` se registra en el historial con la
    etiqueta ``early``. El cálculo del descuento se debe gestionar en el sistema
    de pagos externo.
    """
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT product_id, end_date, renewal_history FROM user_subscriptions
           WHERE id = ?''', (subscription_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False

    product_id, end_date_str, history = result
    product = get_subscription_product(product_id)
    if not product:
        conn.close()
        return False

    _, _, _, _, _, duration, duration_unit, _, _, _, _, _, _ = product

    end_date = datetime.fromisoformat(end_date_str)
    new_end = end_date + timedelta(**{duration_unit: duration})
    tag = 'renewed'
    if apply_early_discount:
        tag += ':early'
    else:
        tag += ''
    new_history = (history or '') + f"|{tag}:{datetime.utcnow().isoformat()}"

    cursor.execute(
        '''UPDATE user_subscriptions
           SET end_date = ?, status = 'active', renewal_history = ?
           WHERE id = ?''',
        (new_end.isoformat(), new_history, subscription_id)
    )
    conn.commit()
    conn.close()
    return True


def suspend_subscription(subscription_id):
    """Suspender una suscripción"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE user_subscriptions SET status = ? WHERE id = ?',
        ('suspended', subscription_id))
    conn.commit()
    conn.close()
    log_action('suspended', subscription_id)
    return True


def cancel_subscription(subscription_id):
    """Cancelar una suscripción manualmente."""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE user_subscriptions SET status = ? WHERE id = ?',
        ('canceled', subscription_id))
    conn.commit()
    conn.close()
    log_action('canceled', subscription_id)
    return True


def get_user_subscriptions(user_id):
    """Obtener todas las suscripciones de un usuario."""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM user_subscriptions WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_subscription_status(subscription_id):
    """Devolver el estado actual de una suscripción."""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT status FROM user_subscriptions WHERE id = ?', (subscription_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def log_action(action, subscription_id):
    """Guardar acción en el archivo de log"""
    dop.log(f'Subscription {subscription_id}: {action}')


# ---------------------------------------------------------------------------
# Proceso de monitoreo de suscripciones
# ---------------------------------------------------------------------------

def check_subscriptions():
    """Proceso diario: notificar y suspender suscripciones"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, product_id, end_date, status FROM '
                   'user_subscriptions')
    subs = cursor.fetchall()
    conn.close()

    now = datetime.utcnow()
    for sub_id, user_id, product_id, end_date_str, status in subs:
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except Exception:
            continue

        product = get_subscription_product(product_id)
        if not product:
            continue
        (p_id, name, _, price, currency, duration, duration_unit,
         service_type, p_status, grace_period, auto_renew,
         early_discount, notification_days) = product

        if status in ('canceled', 'suspended'):
            continue

        days_remaining = (end_date - now).days

        # Notificaciones
        notif_levels = [int(x) for x in notification_days.split(',') if x]
        for days in notif_levels:
            if days_remaining == days:
                try:
                    bot.send_message(
                        user_id,
                        f"🔔 Tu suscripción a {name} vence en {days} días.")
                except Exception:
                    pass
                log_action(f'notify {days}', sub_id)

        if 0 <= days_remaining <= max(notif_levels) and status == 'active':
            conn = sqlite3.connect(files.main_db)
            cur = conn.cursor()
            cur.execute(
                'UPDATE user_subscriptions SET status = ? WHERE id = ?',
                ('due', sub_id))
            conn.commit()
            conn.close()
            status = 'due'
            log_action('due', sub_id)

        # Verificación de vencimiento y renovaciones automáticas
        if now > end_date:
            if auto_renew:
                renewed = renew_subscription(sub_id)
                if renewed:
                    log_action('auto_renew', sub_id)
                    try:
                        bot.send_message(
                            user_id,
                            f"🔄 Suscripción a {name} renovada automáticamente.")
                    except Exception:
                        pass
                    continue
            if grace_period and now <= end_date + timedelta(days=grace_period):
                if status != 'expired':
                    conn = sqlite3.connect(files.main_db)
                    cur = conn.cursor()
                    cur.execute(
                        'UPDATE user_subscriptions SET status = ? WHERE id = ?',
                        ('expired', sub_id))
                    conn.commit()
                    conn.close()
                    log_action('expired', sub_id)
                try:
                    bot.send_message(
                        user_id,
                        f"⚠️ Tu suscripción a {name} ha vencido."
                        f" Tienes {grace_period} días de gracia.")
                except Exception:
                    pass
            else:
                suspend_subscription(sub_id)
                try:
                    bot.send_message(
                        user_id,
                        f"❌ Tu suscripción a {name} ha sido suspendida.")
                except Exception:
                    pass

    return True


def get_upcoming_subscriptions(days=30):
    """Obtener suscripciones que vencen en los próximos `days` días."""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    end_limit = datetime.utcnow() + timedelta(days=days)
    cursor.execute(
        'SELECT id, user_id, product_id, end_date, status FROM user_subscriptions '
        'WHERE end_date <= ? AND status NOT IN ("canceled", "suspended")',
        (end_limit.isoformat(),)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ============================================
# FUNCIONES CRUD COMPLETAS PARA SUSCRIPCIONES
# Agregadas por instalador_suscripciones_completo.py
# ============================================

def update_plan_description(plan_id, new_description):
    """Actualizar descripción principal del plan"""
    try:
        init_subscription_db()
        conn = sqlite3.connect(files.main_db)
        cursor = conn.cursor()
        cursor.execute("UPDATE subscription_products SET description = ? WHERE id = ?", 
                      (new_description, plan_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando descripción del plan: {e}")
        return False

def update_plan_price(plan_id, new_price):
    """Actualizar precio del plan"""
    try:
        init_subscription_db()
        conn = sqlite3.connect(files.main_db)
        cursor = conn.cursor()
        cursor.execute("UPDATE subscription_products SET price = ? WHERE id = ?", 
                      (new_price, plan_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando precio del plan: {e}")
        return False

def delete_subscription_product(plan_id):
    """Eliminar plan de suscripción completamente"""
    try:
        init_subscription_db()
        
        # Obtener información del plan antes de eliminarlo
        plan = get_subscription_product(plan_id)
        if not plan:
            return False
            
        plan_name = plan[1] if len(plan) > 1 else f"plan_{plan_id}"
        
        # Eliminar archivo de contenido si existe
        content_file = f"data/subscriptions/{plan_name}.txt"
        if os.path.exists(content_file):
            os.remove(content_file)
            print(f"✅ Archivo de contenido eliminado: {content_file}")
        
        # Eliminar de base de datos
        conn = sqlite3.connect(files.main_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subscription_products WHERE id = ?", (plan_id,))
        
        # También eliminar suscripciones activas de usuarios para este plan
        cursor.execute("UPDATE user_subscriptions SET status = 'canceled' WHERE product_id = ?", (plan_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error eliminando plan: {e}")
        return False

def get_plan_content_file(plan_name):
    """Obtener ruta del archivo de contenido del plan"""
    return f"data/subscriptions/{plan_name}.txt"

def add_content_to_plan(plan_name, content):
    """Agregar contenido/productos al plan (similar a productos normales)"""
    try:
        content_file = get_plan_content_file(plan_name)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(content_file), exist_ok=True)
        
        # Escribir contenido
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Actualizar ruta en base de datos
        init_subscription_db()
        conn = sqlite3.connect(files.main_db)
        cursor = conn.cursor()
        cursor.execute("UPDATE subscription_products SET stored = ? WHERE name = ?", 
                      (content_file, plan_name))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error agregando contenido al plan: {e}")
        return False

def get_plan_content(plan_name):
    """Obtener contenido actual de un plan"""
    try:
        content_file = get_plan_content_file(plan_name)
        if os.path.exists(content_file):
            with open(content_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    except Exception as e:
        print(f"Error obteniendo contenido del plan: {e}")
        return ""

def get_plan_by_name(plan_name):
    """Obtener plan por nombre"""
    try:
        init_subscription_db()
        conn = sqlite3.connect(files.main_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subscription_products WHERE name = ?", (plan_name,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"Error obteniendo plan por nombre: {e}")
        return None

def count_plan_content_lines(plan_name):
    """Contar líneas de contenido disponibles en un plan"""
    try:
        content_file = get_plan_content_file(plan_name)
        if os.path.exists(content_file):
            with open(content_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return len([line for line in lines if line.strip()])
        return 0
    except Exception as e:
        print(f"Error contando contenido del plan: {e}")
        return 0

def get_plan_format(plan_name):
    """Obtener formato del plan (text/file)"""
    try:
        plan = get_plan_by_name(plan_name)
        if plan and len(plan) > 19:  # Asumiendo que format está en posición 19
            return plan[19] or 'text'
        return 'text'
    except Exception as e:
        print(f"Error obteniendo formato del plan: {e}")
        return 'text'

def get_one_plan_content_item(plan_name):
    """Obtener y consumir una línea de contenido del plan (similar a get_tovar)"""
    try:
        content_file = get_plan_content_file(plan_name)
        if not os.path.exists(content_file):
            return "Plan sin contenido"
            
        with open(content_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return "Plan agotado"
            
        # Obtener primera línea y eliminarla
        first_line = lines[0].strip()
        remaining_lines = lines[1:]
        
        with open(content_file, 'w', encoding='utf-8') as f:
            f.writelines(remaining_lines)
        
        return first_line
        
    except Exception as e:
        print(f"Error obteniendo item del plan: {e}")
        return "Error obteniendo contenido"

def update_plan_format(plan_name, new_format):
    """Actualizar formato del plan (text/file)"""
    try:
        init_subscription_db()
        conn = sqlite3.connect(files.main_db)
        cursor = conn.cursor()
        cursor.execute("UPDATE subscription_products SET format = ? WHERE name = ?", 
                      (new_format, plan_name))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando formato del plan: {e}")
        return False

def get_all_plan_names():
    """Obtener solo los nombres de todos los planes"""
    try:
        plans = get_all_subscription_products()
        return [plan[1] for plan in plans]  # plan[1] es el nombre
    except Exception as e:
        print(f"Error obteniendo nombres de planes: {e}")
        return []
