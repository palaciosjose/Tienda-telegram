#!/usr/bin/env python3
"""Notify users when their purchases expire."""
from datetime import datetime
import db
from bot_instance import bot

def main():
    conn = db.get_db_connection()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute(
        "SELECT id, username, name_good, expires_at FROM purchases WHERE expires_at IS NOT NULL AND expires_at <= ?",
        (now,)
    )
    rows = cur.fetchall()
    for user_id, username, product, expires_at in rows:
        try:
            bot.send_message(
                user_id,
                f"Tu compra de {product} ha expirado. Vuelve a comprar si deseas renovarla."
            )
        except Exception as e:
            print(f"Error notificando a {user_id}: {e}")

if __name__ == "__main__":
    main()
