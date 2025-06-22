#!/usr/bin/env python3
"""
Script para corregir errores de sintaxis en adminka.py
"""

import os
import shutil
from datetime import datetime

def fix_adminka_file():
    """Corrige el archivo adminka.py con errores de sintaxis"""
    print("🔧 Corrigiendo errores de sintaxis en adminka.py...")
    
    # Hacer backup del archivo actual
    backup_file = f"adminka_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy2('adminka.py', backup_file)
    print(f"✅ Backup creado: {backup_file}")
    
    try:
        # Leer el archivo con problemas
        with open('adminka.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Corregir los caracteres literales \n
        content = content.replace('\\n', '\n')
        
        # Corregir imports duplicados o malformados
        lines = content.split('\n')
        corrected_lines = []
        
        imports_added = False
        
        for line in lines:
            # Corregir la línea de imports problemática
            if 'import config, dop, files' in line and 'purchase_validator' in line:
                if not imports_added:
                    corrected_lines.append('import config, dop, files')
                    corrected_lines.append('import purchase_validator')
                    imports_added = True
            elif line.strip() == 'import purchase_validator':
                # Skip if already added
                if not imports_added:
                    corrected_lines.append(line)
                    imports_added = True
            else:
                corrected_lines.append(line)
        
        # Escribir el archivo corregido
        with open('adminka.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(corrected_lines))
        
        print("✅ Errores de sintaxis corregidos")
        return True
        
    except Exception as e:
        print(f"❌ Error corrigiendo archivo: {e}")
        # Restaurar backup
        shutil.copy2(backup_file, 'adminka.py')
        print(f"🔄 Archivo restaurado desde backup")
        return False

def create_clean_adminka_patch():
    """Crea un parche limpio para adminka.py"""
    print("📝 Creando parche limpio para adminka.py...")
    
    # Usar el backup original
    backup_files = [f for f in os.listdir('.') if f.startswith('backup_') and os.path.isdir(f)]
    if not backup_files:
        print("❌ No se encontraron backups")
        return False
    
    latest_backup = max(backup_files)
    original_adminka = os.path.join(latest_backup, 'adminka.py')
    
    if not os.path.exists(original_adminka):
        print("❌ No se encontró adminka.py en el backup")
        return False
    
    try:
        # Leer el archivo original
        with open(original_adminka, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Agregar import de purchase_validator después de la línea de imports existente
        if 'import purchase_validator' not in content:
            # Buscar la línea de imports
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'import config, dop, files' in line:
                    lines.insert(i + 1, 'import purchase_validator')
                    break
            content = '\n'.join(lines)
        
        # Agregar la nueva opción al menú principal
        if '🔍 Validar Compras' not in content:
            old_menu = "user_markup.row('Estadísticas', 'Boletín informativo')\n            user_markup.row('Otras configuraciones')"
            new_menu = "user_markup.row('Estadísticas', 'Boletín informativo')\n            user_markup.row('🔍 Validar Compras', 'Otras configuraciones')"
            content = content.replace(old_menu, new_menu)
        
        # Agregar las nuevas opciones del menú antes de "Otras configuraciones"
        validation_menu = """
        elif '🔍 Validar Compras' == message_text:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('🔎 Buscar por ID usuario', '🔎 Buscar por username')
            user_markup.row('📊 Ventas generales', '📈 Estadísticas detalladas')
            user_markup.row('🕐 Compras recientes')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, '🔍 **Panel de Validación de Compras**\\n\\nSelecciona una opción para buscar y validar compras:', reply_markup=user_markup, parse_mode='Markdown')

        elif '🔎 Buscar por ID usuario' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '🔎 **Buscar por ID de Usuario**\\n\\nEnvía el ID de Telegram del usuario (número):', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 50

        elif '🔎 Buscar por username' == message_text:
            key = telebot.types.InlineKeyboardMarkup()
            key.add(telebot.types.InlineKeyboardButton(text='Cancelar', callback_data='Volver al menú principal de administración'))
            bot.send_message(chat_id, '🔎 **Buscar por Username**\\n\\nEnvía el username del usuario (con o sin @):', reply_markup=key, parse_mode='Markdown')
            with shelve.open(files.sost_bd) as bd: bd[str(chat_id)] = 51

        elif '📊 Ventas generales' == message_text:
            result = dop.get_daily_sales()
            bot.send_message(chat_id, result, parse_mode='Markdown')

        elif '📈 Estadísticas detalladas' == message_text:
            result = purchase_validator.get_purchase_stats()
            bot.send_message(chat_id, result, parse_mode='Markdown')

        elif '🕐 Compras recientes' == message_text:
            result = purchase_validator.search_recent_purchases(24)
            bot.send_message(chat_id, result, parse_mode='Markdown')
"""
        
        # Insertar antes de "Otras configuraciones"
        if '🔍 Validar Compras' not in content:
            insert_point = content.find("elif 'Otras configuraciones' == message_text:")
            if insert_point != -1:
                content = content[:insert_point] + validation_menu + "\n        " + content[insert_point:]
        
        # Agregar los nuevos estados al final de la función de estados
        new_states = """
            elif sost_num == 50:  # Buscar por ID
                try:
                    user_id = int(message_text)
                    result = purchase_validator.validate_purchase_by_user(user_id=user_id)
                    bot.send_message(chat_id, result, parse_mode='Markdown')
                    
                    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                    user_markup.row('🔎 Buscar por ID usuario', '🔎 Buscar por username')
                    user_markup.row('📊 Ventas generales', '📈 Estadísticas detalladas')
                    user_markup.row('🕐 Compras recientes')
                    user_markup.row('Volver al menú principal')
                    bot.send_message(chat_id, '✅ Búsqueda completada. ¿Qué más deseas hacer?', reply_markup=user_markup)
                    
                    with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
                except ValueError:
                    bot.send_message(chat_id, '❌ El ID debe ser un número. Intenta de nuevo:')

            elif sost_num == 51:  # Buscar por username
                result = purchase_validator.validate_purchase_by_user(username=message_text)
                bot.send_message(chat_id, result, parse_mode='Markdown')
                
                user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
                user_markup.row('🔎 Buscar por ID usuario', '🔎 Buscar por username')
                user_markup.row('📊 Ventas generales', '📈 Estadísticas detalladas')
                user_markup.row('🕐 Compras recientes')
                user_markup.row('Volver al menú principal')
                bot.send_message(chat_id, '✅ Búsqueda completada. ¿Qué más deseas hacer?', reply_markup=user_markup)
                
                with shelve.open(files.sost_bd) as bd: del bd[str(chat_id)]
"""
        
        # Buscar dónde insertar los nuevos estados
        if 'sost_num == 50' not in content:
            # Buscar el último estado y agregar después
            lines = content.split('\n')
            last_elif_line = -1
            for i, line in enumerate(lines):
                if 'elif sost_num ==' in line:
                    last_elif_line = i
            
            if last_elif_line != -1:
                # Encontrar el final de ese bloque elif
                indent_level = len(lines[last_elif_line]) - len(lines[last_elif_line].lstrip())
                end_line = last_elif_line + 1
                
                while end_line < len(lines):
                    line = lines[end_line]
                    if line.strip() == '':
                        end_line += 1
                        continue
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= indent_level and line.strip():
                        break
                    end_line += 1
                
                # Insertar los nuevos estados
                new_state_lines = new_states.strip().split('\n')
                for j, state_line in enumerate(new_state_lines):
                    lines.insert(end_line + j, state_line)
                
                content = '\n'.join(lines)
        
        # Escribir el archivo corregido
        with open('adminka.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Parche limpio aplicado a adminka.py")
        return True
        
    except Exception as e:
        print(f"❌ Error aplicando parche: {e}")
        return False

def verify_syntax():
    """Verifica que el archivo no tenga errores de sintaxis"""
    print("🔍 Verificando sintaxis de adminka.py...")
    
    try:
        with open('adminka.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Compilar para verificar sintaxis
        compile(code, 'adminka.py', 'exec')
        print("✅ Sintaxis correcta")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        print(f"Línea {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal para corregir errores"""
    print("🔧 CORRECTOR DE ERRORES DE SINTAXIS")
    print("=" * 40)
    
    # Método 1: Intentar corregir el archivo actual
    if fix_adminka_file():
        if verify_syntax():
            print("✅ Archivo corregido exitosamente")
        else:
            print("⚠️ Aún hay errores, intentando método 2...")
            create_clean_adminka_patch()
    else:
        print("⚠️ Método 1 falló, intentando método 2...")
        create_clean_adminka_patch()
    
    # Verificación final
    if verify_syntax():
        print("\n🎉 ¡Corrección completada!")
        print("\n📋 Ahora puedes:")
        print("1. Ejecutar: python3 main.py")
        print("2. Ir a /adm en tu bot")
        print("3. Ver la nueva opción '🔍 Validar Compras'")
    else:
        print("\n❌ No se pudo corregir automáticamente")
        print("📋 Solución manual:")
        print("1. Restaurar desde backup:")
        print("   cp backup_*/adminka.py .")
        print("2. Editar manualmente o solicitar ayuda")

if __name__ == '__main__':
    main()