# setup_discounts.py
import sqlite3

def setup_discount_system():
    conn = sqlite3.connect('data/db/main_data.db')
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()
    print("✅ Sistema de descuentos configurado")

if __name__ == '__main__':
    setup_discount_system()