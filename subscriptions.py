"""Módulo de gestión de productos por suscripción"""

import sqlite3
from datetime import datetime, timedelta
import files
import telebot
import config

bot = telebot.TeleBot(config.token)

# ---------------------------------------------------------------------------
# Inicialización de base de datos
# ---------------------------------------------------------------------------

def init_subscription_db():
    """Crear tablas necesarias para el sistema de suscripciones"""
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()

    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS subscription_products (
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
               notification_days TEXT DEFAULT '30,7,1'
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

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Funciones de administración de productos de suscripción
# ---------------------------------------------------------------------------

def add_subscription_product(name, description, price, duration,
                             currency='USD', duration_unit='days',
                             service_type='default', status='active',
                             grace_period=0, auto_renew=True,
                             early_discount=0, notification_days='30,7,1'):
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


def renew_subscription(subscription_id):
    """Renovar una suscripción existente"""
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
    new_history = (history or '') + f"|renewed:{datetime.utcnow().isoformat()}"

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
    return True


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

        # Verificación de vencimiento
        if now > end_date:
            if grace_period and now <= end_date + timedelta(days=grace_period):
                if status != 'grace':
                    suspend_subscription(sub_id)
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
