#!/usr/bin/env python3
"""
Script para configurar el sistema de descuentos en la base de datos
Ejecutar una sola vez después de agregar las funciones a dop.py
"""

import sqlite3
import os

def setup_discount_system():
    """Configura el sistema de descuentos"""
    print("🔧 Configurando sistema de descuentos...")
    
    # Verificar que existe la base de datos
    if not os.path.exists('data/db/main_data.db'):
        print("❌ ERROR: No se encuentra la base de datos.")
        print("Ejecuta init_db.py primero.")
        return False
    
    try:
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        
        # Crear tabla de configuración de descuentos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discount_config (
                id INTEGER PRIMARY KEY,
                discount_enabled INTEGER DEFAULT 1,
                discount_text TEXT DEFAULT '🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥',
                discount_multiplier REAL DEFAULT 1.5,
                show_fake_price INTEGER DEFAULT 1
            )
        ''')
        
        # Verificar si ya existe configuración
        cursor.execute("SELECT COUNT(*) FROM discount_config WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            # Insertar configuración inicial
            cursor.execute("""
                INSERT INTO discount_config 
                VALUES (1, 1, '🔥 DESCUENTOS ESPECIALES ACTIVOS 🔥', 1.5, 1)
            """)
            print("✅ Configuración inicial de descuentos creada")
        else:
            print("ℹ️ La configuración de descuentos ya existe")
        
        conn.commit()
        conn.close()
        
        print("✅ Sistema de descuentos configurado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_discount_functions():
    """Prueba las funciones de descuentos"""
    print("\n🧪 Probando funciones de descuentos...")
    
    try:
        # Importar las funciones (esto solo funcionará después de agregar las funciones a dop.py)
        import dop
        
        # Probar get_discount_config
        config = dop.get_discount_config()
        print(f"✅ Configuración actual: {config}")
        
        # Probar update_discount_config
        result = dop.update_discount_config(text="🎉 PROMOCIÓN DE PRUEBA 🎉")
        if result:
            print("✅ Actualización de texto exitosa")
        
        # Verificar el cambio
        new_config = dop.get_discount_config()
        print(f"✅ Nueva configuración: {new_config}")
        
        return True
        
    except ImportError:
        print("⚠️ No se pueden probar las funciones (agregar primero las funciones a dop.py)")
        return False
    except Exception as e:
        print(f"❌ Error probando funciones: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 CONFIGURADOR DEL SISTEMA DE DESCUENTOS")
    print("=" * 50)
    
    # Paso 1: Configurar base de datos
    if not setup_discount_system():
        print("\n❌ Falló la configuración. Revisa los errores arriba.")
        return
    
    # Paso 2: Probar funciones (opcional)
    test_discount_functions()
    
    print("\n🎉 ¡Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("1. Agrega las funciones de descuentos a tu archivo dop.py")
    print("2. Usa el archivo adminka.py corregido")
    print("3. Reinicia tu bot: python3 main.py")
    print("4. Ve a /adm → Configurar descuentos")
    
    print("\n✨ Características del sistema de descuentos:")
    print("• 🎯 Activar/desactivar descuentos globalmente")
    print("• ✏️ Personalizar texto del descuento")
    print("• 🔢 Ajustar multiplicador de precio falso")
    print("• 👁️ Mostrar/ocultar precios tachados")
    print("• 👀 Vista previa del catálogo")

if __name__ == '__main__':
    main()
