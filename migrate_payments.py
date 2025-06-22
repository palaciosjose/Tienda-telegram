import sqlite3
import shelve
import files

def migrate_to_new_payments():
    print("🔄 Migrando base de datos a nuevos métodos de pago...")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(files.main_db)
    cursor = conn.cursor()
    
    # Eliminar tablas antiguas si existen
    cursor.execute("DROP TABLE IF EXISTS qiwi_data")
    cursor.execute("DROP TABLE IF EXISTS coinbase_data")
    print("✅ Tablas antiguas eliminadas")
    
    # Crear tabla para datos de PayPal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paypal_data (
            client_id TEXT,
            client_secret TEXT,
            sandbox INTEGER DEFAULT 1
        )
    ''')
    print("✅ Tabla 'paypal_data' creada")
    
    # Crear tabla para datos de Binance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS binance_data (
            api_key TEXT,
            api_secret TEXT,
            merchant_id TEXT
        )
    ''')
    print("✅ Tabla 'binance_data' creada")
    
    # Commit cambios
    conn.commit()
    conn.close()
    
    # Actualizar configuración de pagos
    try:
        with shelve.open(files.payments_bd) as bd:
            bd['paypal'] = '❌'
            bd['binance'] = '❌'
            # Eliminar configuraciones antiguas
            if 'qiwi' in bd:
                del bd['qiwi']
            if 'btc' in bd:
                del bd['btc']
        print("✅ Configuración de pagos actualizada")
    except:
        print("⚠️ Error actualizando configuración de pagos")
    
    print("🎉 ¡Migración completada!")
    print("\nPróximos pasos:")
    print("1. Ejecutar: python3 migrate_payments.py")
    print("2. Configurar credenciales de PayPal y Binance")
    print("3. Reiniciar el bot")

if __name__ == '__main__':
    migrate_to_new_payments()