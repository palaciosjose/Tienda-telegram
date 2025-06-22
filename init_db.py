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
            media_caption TEXT
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
