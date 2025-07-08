import sqlite3
import os

def create_database():
    print("Creando estructura de directorios...")
    
    # Crear directorios si no existen
    directories = [
        'data/db',
        'data/bd', 
        'data/lists',
        'data/goods',
        'data/Temp'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directorio creado: {directory}")
    
    print("\nCreando base de datos...")
    
    # Crear base de datos
    conn = sqlite3.connect('data/db/main_data.db')
    cursor = conn.cursor()
    
    # Crear tabla de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goods (
            name TEXT PRIMARY KEY,
            description TEXT,
            format TEXT,
            minimum INTEGER,
            price INTEGER,
            stored TEXT,
            additional_description TEXT DEFAULT '',
            media_file_id TEXT,
            media_type TEXT,
            media_caption TEXT,
            duration_days INTEGER DEFAULT NULL
        )
    ''')
    print("✓ Tabla 'goods' creada")
    
    # Crear tabla de compras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER,
            username TEXT,
            name_good TEXT,
            amount INTEGER,
            price INTEGER
        )
    ''')
    print("✓ Tabla 'purchases' creada")
    
    # Crear tabla de compradores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyers (
            id INTEGER PRIMARY KEY,
            username TEXT,
            payed INTEGER
        )
    ''')
    print("✓ Tabla 'buyers' creada")
    
    # Crear tabla de datos QIWI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qiwi_data (
            number TEXT PRIMARY KEY,
            token TEXT
        )
    ''')
    print("✓ Tabla 'qiwi_data' creada")
    
    # Crear tabla de datos Coinbase
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coinbase_data (
            api_key TEXT,
            private_key TEXT
        )
    ''')
    print("✓ Tabla 'coinbase_data' creada")

    # Tablas para sistema de suscripciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_products (
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
            notification_days TEXT DEFAULT '30,15,7,1'
        )
    ''')
    print("✓ Tabla 'subscription_products' creada")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            payment_method TEXT,
            renewal_history TEXT
        )
    ''')
    print("✓ Tabla 'user_subscriptions' creada")

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_subscriptions_end_date '
                   'ON user_subscriptions(end_date)')
    print("✓ Índice en 'user_subscriptions.end_date' creado")

    # Tablas para sistema de publicidad
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            message_text TEXT NOT NULL,
            media_file_id TEXT,
            media_type TEXT,
            media_caption TEXT,
            button1_text TEXT,
            button1_url TEXT,
            button2_text TEXT,
            button2_url TEXT,
            status TEXT DEFAULT 'active',
            created_date TEXT,
            created_by INTEGER,
            daily_limit INTEGER DEFAULT 3,
            priority INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            schedule_name TEXT,
            frequency TEXT,
            send_times TEXT,
            target_platforms TEXT,
            is_active INTEGER DEFAULT 1,
            next_send_telegram TEXT,
            next_send_whatsapp TEXT,
            created_date TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS target_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            group_id TEXT NOT NULL,
            group_name TEXT,
            category TEXT,
            status TEXT DEFAULT 'active',
            last_sent TEXT,
            success_rate REAL DEFAULT 1.0,
            added_date TEXT,
            notes TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT UNIQUE,
            config_data TEXT,
            is_active INTEGER DEFAULT 1,
            last_updated TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS send_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            group_id TEXT,
            platform TEXT,
            status TEXT,
            sent_date TEXT,
            response_time REAL,
            error_message TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            total_sent INTEGER DEFAULT 0,
            telegram_sent INTEGER DEFAULT 0,
            whatsapp_sent INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            success INTEGER,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("\nCreando archivos de listas...")
    
    # Crear archivos de listas vacíos si no existen
    lists_files = [
        'data/lists/admins_list.txt',
        'data/lists/chatid_list.txt', 
        'data/lists/blockusers_list.txt'
    ]
    
    for file_path in lists_files:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                pass
            print(f"✓ Archivo creado: {file_path}")
    
    # Crear archivo de log si no existe
    log_file = 'data/working_log.log'
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            pass
        print(f"✓ Archivo creado: {log_file}")
    
    print("\n🎉 ¡Base de datos y estructura creada exitosamente!")
    print("\nPróximos pasos:")
    print("1. Verifica que tu token en config.py sea correcto")
    print("2. Instala las dependencias: pip install pyTelegramBotAPI SimpleQIWI coinbase")
    print("3. Ejecuta: python main.py")
    print("4. Envía /start al bot para configuración inicial")

if __name__ == '__main__':
    create_database()
