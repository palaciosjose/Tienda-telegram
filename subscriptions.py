"""Módulo de gestión de productos por suscripción"""

import sqlite3
from datetime import datetime, timedelta
import files
import telebot
import config
import dop

# Días de notificación por defecto (30, 15, 7 y 1 día antes)
DEFAULT_NOTIFICATION_DAYS = '30,15,7,1'

bot = telebot.TeleBot(config.token)

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
               notification_days TEXT DEFAULT "{DEFAULT_NOTIFICATION_DAYS}"
        )'''
    )

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
                             notification_days=DEFAULT_NOTIFICATION_DAYS):
    """Agregar un nuevo producto de suscripción"""
    init_subscription_db()
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO subscription_products
           (name, description, price, currency, duration, duration_unit,
            service_type, status, grace_period, auto_renew,
            early_discount, notification_days)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (name, description, price, currency, duration, duration_unit,
         service_type, status, grace_period, int(auto_renew),
         early_discount, notification_days)
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
