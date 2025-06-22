#!/usr/bin/env python3
"""
INSTALADOR AUTOMÁTICO - FUNCIONALIDAD "MÁS INFORMACIÓN"
======================================================

Este script automatiza la instalación de la nueva funcionalidad.
Ejecutar DESPUÉS de hacer backup de tus archivos.

Funcionalidad: Agrega botón "Más información" a productos con descripción adicional.
"""

import sqlite3
import os
import shutil
from datetime import datetime

def create_backup():
    """Crear backup de archivos importantes"""
    print("📦 Creando backup de archivos...")
    
    backup_dir = f"backup_mas_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = ['main.py', 'adminka.py', 'dop.py', 'data/db/main_data.db']
    backed_up = []
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_dir)
            backed_up.append(file_path)
            print(f"✅ Backup: {file_path}")
    
    if backed_up:
        print(f"✅ Backup creado en: {backup_dir}")
        return backup_dir
    else:
        print("⚠️ No se encontraron archivos para backup")
        return None

def update_database():
    """Actualizar base de datos"""
    print("\\n🔄 Actualizando base de datos...")
    
    if not os.path.exists('data/db/main_data.db'):
        print("❌ No se encuentra data/db/main_data.db")
        return False
    
    try:
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(goods)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'additional_description' in columns:
            print("ℹ️ La columna 'additional_description' ya existe")
            conn.close()
            return True
        
        # Agregar nueva columna
        cursor.execute("ALTER TABLE goods ADD COLUMN additional_description TEXT DEFAULT ''")
        conn.commit()
        conn.close()
        
        print("✅ Base de datos actualizada")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando base de datos: {e}")
        return False

def add_functions_to_dop():
    """Agregar funciones a dop.py"""
    print("\\n📝 Agregando funciones a dop.py...")
    
    if not os.path.exists('dop.py'):
        print("❌ No se encuentra dop.py")
        return False
    
    # Leer archivo actual
    with open('dop.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya están las funciones
    if 'get_additional_description' in content:
        print("ℹ️ Las funciones ya están en dop.py")
        return True
    
    # Funciones a agregar
    new_functions = '''

# ============================================
# FUNCIONES PARA DESCRIPCIÓN ADICIONAL
# Agregadas automáticamente por el instalador
# ============================================

def get_additional_description(good_name):
    """Obtiene la descripción adicional de un producto"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT additional_description FROM goods WHERE name = ?", (good_name,))
        result = cursor.fetchone()
        con.close()
        
        if result and result[0]:
            return result[0]
        else:
            return "No hay información adicional disponible para este producto."
    except Exception as e:
        print(f"Error obteniendo descripción adicional: {e}")
        return "Error al cargar información adicional."

def set_additional_description(good_name, additional_description):
    """Establece la descripción adicional de un producto"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("UPDATE goods SET additional_description = ? WHERE name = ?", 
                      (additional_description, good_name))
        con.commit()
        con.close()
        return True
    except Exception as e:
        print(f"Error estableciendo descripción adicional: {e}")
        return False

def get_product_full_info(good_name):
    """Obtiene toda la información del producto incluyendo descripción adicional"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("""
            SELECT name, description, additional_description, format, minimum, price 
            FROM goods WHERE name = ?
        """, (good_name,))
        result = cursor.fetchone()
        con.close()
        
        if result:
            name, description, additional_desc, format, minimum, price = result
            return {
                'name': name,
                'description': description,
                'additional_description': additional_desc or '',
                'format': format,
                'minimum': minimum,
                'price': price
            }
        else:
            return None
    except Exception as e:
        print(f"Error obteniendo información completa del producto: {e}")
        return None

def format_product_basic_info(good_name):
    """Formatea la información básica del producto (sin descripción adicional)"""
    try:
        product_info = get_product_full_info(good_name)
        if not product_info:
            return "Producto no encontrado"
        
        amount = amount_of_goods(good_name)  # Usar función existente
        
        info_text = f"""🛍️ **{product_info['name']}**

📝 **Descripción:**
{product_info['description']}

💰 **Precio:** ${product_info['price']} USD
📦 **Cantidad mínima:** {product_info['minimum']}
📋 **Formato:** {product_info['format']}
📊 **Disponibles:** {amount}"""
        
        return info_text
    except Exception as e:
        print(f"Error formateando información básica: {e}")
        return "Error al cargar información del producto"

def format_product_additional_info(good_name):
    """Formatea la información adicional del producto"""
    try:
        additional_desc = get_additional_description(good_name)
        
        info_text = f"""ℹ️ **Información Adicional**

{additional_desc}

━━━━━━━━━━━━━━━━━━━━━━"""
        
        return info_text
    except Exception as e:
        print(f"Error formateando información adicional: {e}")
        return "Error al cargar información adicional"

def has_additional_description(good_name):
    """Verifica si un producto tiene descripción adicional"""
    try:
        additional_desc = get_additional_description(good_name)
        return additional_desc and additional_desc.strip() != "" and additional_desc != "No hay información adicional disponible para este producto."
    except:
        return False
'''
    
    # Agregar funciones al archivo
    try:
        with open('dop.py', 'a', encoding='utf-8') as f:
            f.write(new_functions)
        
        print("✅ Funciones agregadas a dop.py")
        return True
        
    except Exception as e:
        print(f"❌ Error agregando funciones: {e}")
        return False

def show_manual_steps():
    """Mostrar pasos manuales requeridos"""
    print("\\n🔧 PASOS MANUALES REQUERIDOS:")
    print("=" * 50)
    
    print("\\n1️⃣ ACTUALIZAR main.py:")
    print("   • Busca la sección: elif callback.data in the_goods:")
    print("   • Reemplázala con el código de main_modificaciones.py")
    print("   • Agrega el nuevo callback MAS_INFO_")
    
    print("\\n2️⃣ ACTUALIZAR adminka.py:")
    print("   • Agrega 'import os' al inicio")
    print("   • Agrega opción '📝 Descripción adicional' al menú")
    print("   • Agrega estados 8 y 9 para editar descripciones")
    
    print("\\n3️⃣ REINICIAR EL BOT:")
    print("   python3 main.py")
    
    print("\\n📋 Archivos de referencia creados:")
    print("   • main_modificaciones.py")
    print("   • admin_modificaciones.py")
    print("   • INSTRUCCIONES_INSTALACION.md")

def test_installation():
    """Probar la instalación"""
    print("\\n🧪 Probando instalación...")
    
    try:
        # Probar base de datos
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(goods)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'additional_description' not in columns:
            print("❌ Error: Columna additional_description no encontrada")
            return False
        
        # Probar funciones
        with open('dop.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            'get_additional_description',
            'set_additional_description',
            'has_additional_description'
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Error: Funciones faltantes: {missing_functions}")
            return False
        
        conn.close()
        print("✅ Instalación base completada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        return False

def main():
    """Función principal del instalador"""
    print("🚀 INSTALADOR AUTOMÁTICO")
    print("Funcionalidad: Más información en productos")
    print("=" * 50)
    
    # Crear backup
    backup_dir = create_backup()
    
    # Actualizar base de datos
    if not update_database():
        print("\\n❌ Error en actualización de base de datos")
        return
    
    # Agregar funciones a dop.py
    if not add_functions_to_dop():
        print("\\n❌ Error agregando funciones")
        return
    
    # Probar instalación
    if test_installation():
        print("\\n🎉 ¡INSTALACIÓN BASE COMPLETADA!")
        show_manual_steps()
        
        if backup_dir:
            print(f"\\n💾 Backup guardado en: {backup_dir}")
        
        print("\\n⚠️ IMPORTANTE:")
        print("La instalación automática completó la base de datos y funciones.")
        print("Debes completar manualmente main.py y adminka.py siguiendo las instrucciones.")
    else:
        print("\\n❌ Error en la instalación")

if __name__ == '__main__':
    main()