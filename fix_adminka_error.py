#!/usr/bin/env python3
"""
CORRECTOR DEL ERROR DE INSERCIÓN EN BASE DE DATOS
===============================================

Error: table goods has 7 columns but 6 values were supplied
Solución: Corregir el INSERT en adminka.py
"""

import os
import shutil
from datetime import datetime

def fix_insert_error():
    """Corregir el error de inserción en adminka.py"""
    print("🔧 Corrigiendo error de INSERT en adminka.py...")
    
    # Hacer backup
    backup_name = f"adminka_before_insert_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2('adminka.py', backup_name)
    print(f"✅ Backup creado: {backup_name}")
    
    try:
        with open('adminka.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar y corregir el INSERT problemático
        old_insert = 'cursor.execute("INSERT INTO goods VALUES(?, ?, ?, ? , ?, ?)", (name, description, format, minimum, price, \'data/goods/\' + name + \'.txt\'))'
        
        # Nuevo INSERT con 7 valores (agregando campo additional_description vacío)
        new_insert = 'cursor.execute("INSERT INTO goods VALUES(?, ?, ?, ? , ?, ?, ?)", (name, description, format, minimum, price, \'data/goods/\' + name + \'.txt\', \'\'))'
        
        # Reemplazar
        if old_insert in content:
            content = content.replace(old_insert, new_insert)
            print("✅ INSERT corregido: agregado campo additional_description")
        else:
            # Buscar variaciones del INSERT
            variations = [
                'cursor.execute("INSERT INTO goods VALUES(?, ?, ?, ?, ?, ?)"',
                'INSERT INTO goods VALUES(?, ?, ?, ? , ?, ?)',
                'INSERT INTO goods VALUES(?, ?, ?, ?, ?, ?)'
            ]
            
            found = False
            for variation in variations:
                if variation in content:
                    print(f"📍 Encontrada variación: {variation}")
                    # Reemplazar la línea completa
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if variation in line and 'goods VALUES' in line:
                            # Corregir la línea
                            if '?, ?, ?, ? , ?, ?' in line:
                                lines[i] = line.replace('?, ?, ?, ? , ?, ?', '?, ?, ?, ? , ?, ?, ?')
                            elif '?, ?, ?, ?, ?, ?' in line:
                                lines[i] = line.replace('?, ?, ?, ?, ?, ?', '?, ?, ?, ?, ?, ?, ?')
                            
                            # Buscar la línea de valores correspondiente
                            if i + 1 < len(lines) and '(name, description, format, minimum, price,' in lines[i + 1]:
                                # Agregar campo vacío para additional_description
                                if lines[i + 1].endswith("'.txt'))"):
                                    lines[i + 1] = lines[i + 1].replace("'.txt'))", "'.txt', '')")
                                elif lines[i + 1].endswith("'.txt')"):
                                    lines[i + 1] = lines[i + 1].replace("'.txt')", "'.txt', '')")
                            
                            found = True
                            break
                    
                    if found:
                        content = '\n'.join(lines)
                        print("✅ INSERT corregido usando detección automática")
                        break
        
        # Escribir archivo corregido
        with open('adminka.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Archivo adminka.py corregido")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Restaurar backup
        shutil.copy2(backup_name, 'adminka.py')
        return False

def verify_syntax():
    """Verificar sintaxis de adminka.py"""
    print("🔍 Verificando sintaxis...")
    
    try:
        with open('adminka.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, 'adminka.py', 'exec')
        print("✅ Sintaxis correcta")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_database_structure():
    """Verificar estructura de la base de datos"""
    print("🔍 Verificando estructura de base de datos...")
    
    try:
        import sqlite3
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(goods)")
        columns = cursor.fetchall()
        
        print("📋 Columnas en tabla 'goods':")
        for i, col in enumerate(columns):
            print(f"   {i+1}. {col[1]} ({col[2]})")
        
        expected_columns = ['name', 'description', 'format', 'minimum', 'price', 'stored', 'additional_description']
        actual_columns = [col[1] for col in columns]
        
        if len(actual_columns) == 7 and 'additional_description' in actual_columns:
            print("✅ Estructura de base de datos correcta (7 columnas)")
            return True
        else:
            print(f"⚠️ Estructura inesperada. Esperadas: {expected_columns}")
            print(f"   Actuales: {actual_columns}")
            return False
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def main():
    """Función principal"""
    print("🚨 CORRECTOR DEL ERROR DE INSERCIÓN")
    print("Error: table goods has 7 columns but 6 values were supplied")
    print("=" * 60)
    
    # Verificar estructura de base de datos
    if not check_database_structure():
        print("\n❌ Problema con la estructura de base de datos")
        return
    
    # Corregir el INSERT
    if fix_insert_error():
        # Verificar sintaxis
        if verify_syntax():
            print("\n🎉 ¡CORRECCIÓN EXITOSA!")
            print("\n📋 Próximos pasos:")
            print("1. Ejecuta: python3 main.py")
            print("2. Tu bot debería funcionar sin errores")
            print("3. Prueba crear un nuevo producto para verificar")
            
        else:
            print("\n⚠️ Corrección aplicada pero hay errores de sintaxis")
    else:
        print("\n❌ Error en la corrección")
        print("\n🔧 CORRECCIÓN MANUAL:")
        print("1. Abre adminka.py")
        print("2. Busca la línea ~744 con 'INSERT INTO goods VALUES'")
        print("3. Cambia (?, ?, ?, ?, ?, ?) por (?, ?, ?, ?, ?, ?, ?)")
        print("4. En la línea siguiente, agrega '', al final antes del )")

if __name__ == '__main__':
    main()