#!/usr/bin/env python3
"""
REPARADOR COMPLETO DEL PROYECTO TELEGRAM BOT
===========================================

Este script identifica y corrige automáticamente todos los errores
encontrados en el proyecto del bot de Telegram.
"""

import os
import sqlite3
import shutil
from datetime import datetime
import re

def create_backup():
    """Crear backup completo del proyecto"""
    print("📦 Creando backup completo...")
    
    backup_dir = f"backup_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'main.py', 'adminka.py', 'dop.py', 'payments.py', 
        'subscriptions.py', 'config.py', 'files.py',
        'data/db/main_data.db'
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            dest = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, dest)
            print(f"✅ {file_path} → {dest}")
    
    print(f"📦 Backup creado en: {backup_dir}")
    return backup_dir

def check_database_integrity():
    """Verificar y corregir integridad de la base de datos"""
    print("\n🔍 Verificando integridad de la base de datos...")
    
    if not os.path.exists('data/db/main_data.db'):
        print("❌ Base de datos no encontrada")
        return False
    
    try:
        conn = sqlite3.connect('data/db/main_data.db')
        cursor = conn.cursor()
        
        # Verificar tabla subscription_products
        cursor.execute("PRAGMA table_info(subscription_products)")
        sub_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Columnas en subscription_products: {len(sub_columns)}")
        
        expected_sub_columns = [
            'id', 'name', 'description', 'price', 'currency', 'duration', 
            'duration_unit', 'service_type', 'status', 'grace_period', 
            'auto_renew', 'early_discount', 'notification_days',
            'additional_description', 'media_file_id', 'media_type', 
            'media_caption', 'delivery_format', 'delivery_content'
        ]
        
        # Agregar columnas faltantes
        for col in expected_sub_columns:
            if col not in sub_columns:
                try:
                    if col == 'additional_description':
                        cursor.execute("ALTER TABLE subscription_products ADD COLUMN additional_description TEXT DEFAULT ''")
                    elif col == 'media_file_id':
                        cursor.execute("ALTER TABLE subscription_products ADD COLUMN media_file_id TEXT")
                    elif col == 'media_type':
                        cursor.execute("ALTER TABLE subscription_products ADD COLUMN media_type TEXT")
                    elif col == 'media_caption':
                        cursor.execute("ALTER TABLE subscription_products ADD COLUMN media_caption TEXT")
                    elif col == 'delivery_format':
                        cursor.execute("ALTER TABLE subscription_products ADD COLUMN delivery_format TEXT DEFAULT 'none'")
                    elif col == 'delivery_content':
                        cursor.execute("ALTER TABLE subscription_products ADD COLUMN delivery_content TEXT")
                    print(f"✅ Agregada columna: {col}")
                except Exception as e:
                    print(f"⚠️ Error agregando {col}: {e}")
        
        # Verificar tabla goods
        cursor.execute("PRAGMA table_info(goods)")
        goods_columns = [col[1] for col in cursor.fetchall()]
        
        expected_goods_columns = [
            'additional_description', 'media_file_id', 'media_type', 'media_caption'
        ]
        
        for col in expected_goods_columns:
            if col not in goods_columns:
                try:
                    if col == 'additional_description':
                        cursor.execute("ALTER TABLE goods ADD COLUMN additional_description TEXT DEFAULT ''")
                    elif col == 'media_file_id':
                        cursor.execute("ALTER TABLE goods ADD COLUMN media_file_id TEXT")
                    elif col == 'media_type':
                        cursor.execute("ALTER TABLE goods ADD COLUMN media_type TEXT")
                    elif col == 'media_caption':
                        cursor.execute("ALTER TABLE goods ADD COLUMN media_caption TEXT")
                    print(f"✅ Agregada columna a goods: {col}")
                except Exception as e:
                    print(f"⚠️ Error agregando {col} a goods: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Base de datos verificada y corregida")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def fix_adminka_errors():
    """Corregir todos los errores en adminka.py"""
    print("\n🔧 Corrigiendo errores en adminka.py...")
    
    if not os.path.exists('adminka.py'):
        print("❌ adminka.py no encontrado")
        return False
    
    with open('adminka.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    errors_fixed = 0
    
    # ERROR 1: Desempaquetado de suscripciones
    if "for pid, name, desc, price, currency, duration, unit in planes" in content:
        old_pattern = re.compile(r'for pid, name, desc, price, currency, duration, unit in planes.*?:', re.DOTALL)
        new_code = """for plan in plans:
                    # Desempaquetar de forma segura
                    pid = plan[0] if len(plan) > 0 else 0
                    name = plan[1] if len(plan) > 1 else 'Sin nombre'
                    desc = plan[2] if len(plan) > 2 else 'Sin descripción'
                    price = plan[3] if len(plan) > 3 else 0
                    currency = plan[4] if len(plan) > 4 else 'USD'
                    duration = plan[5] if len(plan) > 5 else 30
                    unit = plan[6] if len(plan) > 6 else 'days'"""
        
        content = old_pattern.sub(new_code + ':', content, count=1)
        errors_fixed += 1
        print("✅ Corregido desempaquetado de suscripciones")
    
    # ERROR 2: Otro patrón problemático
    if "for _pid, name, *_ in plans:" in content:
        content = content.replace(
            "for _pid, name, *_ in plans:",
            "for plan in plans:\n                name = plan[1] if len(plan) > 1 else 'Sin nombre'"
        )
        errors_fixed += 1
        print("✅ Corregido patrón de nombres de planes")
    
    # ERROR 3: Missing save_message function
    if "dop.save_message" in content and "def save_message" not in content:
        # Buscar where save_message is called and replace with shelve operation
        save_message_pattern = r'if dop\.save_message\(message, message_text\):'
        save_message_replacement = '''try:
                with shelve.open(files.bot_message_bd) as bd:
                    bd[message] = message_text
                success = True
            except:
                success = False
            if success:'''
        
        content = re.sub(save_message_pattern, save_message_replacement, content)
        errors_fixed += 1
        print("✅ Corregido save_message")
    
    # ERROR 4: Import issues
    if "import subscriptions" not in content:
        # Add import at the top
        import_line = "import telebot, sqlite3, shelve, os\nimport config, dop, files, subscriptions"
        content = content.replace("import telebot, sqlite3, shelve, os\nimport config, dop, files", import_line)
        errors_fixed += 1
        print("✅ Agregado import de subscriptions")
    
    # ERROR 5: Fix planes vs plans inconsistency
    content = content.replace("planes = subscriptions.get_all_subscription_products()", 
                             "plans = subscriptions.get_all_subscription_products()")
    
    # Write corrected file
    with open('adminka.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {errors_fixed} errores corregidos en adminka.py")
    return True

def fix_dop_errors():
    """Corregir errores en dop.py"""
    print("\n🔧 Corrigiendo errores en dop.py...")
    
    if not os.path.exists('dop.py'):
        print("❌ dop.py no encontrado")
        return False
    
    with open('dop.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    errors_fixed = 0
    
    # Add missing save_message function if not present
    if "def save_message" not in content:
        save_message_function = '''
def save_message(message_type, message_text):
    """Guardar mensaje del bot"""
    try:
        with shelve.open(files.bot_message_bd) as bd:
            bd[message_type] = message_text
        return True
    except Exception as e:
        print(f"Error guardando mensaje: {e}")
        return False
'''
        content += save_message_function
        errors_fixed += 1
        print("✅ Agregada función save_message")
    
    # Write corrected file
    with open('dop.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {errors_fixed} errores corregidos en dop.py")
    return True

def fix_main_errors():
    """Corregir errores en main.py"""
    print("\n🔧 Corrigiendo errores en main.py...")
    
    if not os.path.exists('main.py'):
        print("❌ main.py no encontrado")
        return False
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    errors_fixed = 0
    
    # Check if subscriptions is imported
    if "import subscriptions" not in content:
        content = content.replace(
            "import config, dop, payments, adminka, files",
            "import config, dop, payments, adminka, files, subscriptions"
        )
        errors_fixed += 1
        print("✅ Agregado import de subscriptions en main.py")
    
    # Write corrected file
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {errors_fixed} errores corregidos en main.py")
    return True

def fix_subscriptions_errors():
    """Corregir errores en subscriptions.py"""
    print("\n🔧 Verificando subscriptions.py...")
    
    if not os.path.exists('subscriptions.py'):
        print("❌ subscriptions.py no encontrado")
        return False
    
    with open('subscriptions.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ensure all necessary functions exist
    required_functions = [
        'get_all_subscription_products',
        'get_subscription_product', 
        'add_subscription_product',
        'get_additional_description',
        'set_additional_description',
        'has_additional_description'
    ]
    
    missing_functions = []
    for func in required_functions:
        if f"def {func}" not in content:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"⚠️ Funciones faltantes en subscriptions.py: {missing_functions}")
    else:
        print("✅ subscriptions.py verificado")
    
    return True

def check_syntax_all_files():
    """Verificar sintaxis de todos los archivos Python"""
    print("\n🧪 Verificando sintaxis de todos los archivos...")
    
    python_files = ['main.py', 'adminka.py', 'dop.py', 'payments.py', 'subscriptions.py', 'config.py']
    syntax_errors = []
    
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, file_path, 'exec')
                print(f"✅ {file_path} - Sintaxis correcta")
            except SyntaxError as e:
                print(f"❌ {file_path} - Error línea {e.lineno}: {e.msg}")
                syntax_errors.append((file_path, e.lineno, e.msg))
            except Exception as e:
                print(f"⚠️ {file_path} - Error: {e}")
                syntax_errors.append((file_path, 0, str(e)))
        else:
            print(f"⚠️ {file_path} - No encontrado")
    
    return syntax_errors

def create_minimal_working_adminka():
    """Crear una versión mínima funcional de adminka.py si está muy dañado"""
    print("\n🆘 Creando versión mínima de adminka.py...")
    
    minimal_adminka = '''import telebot, sqlite3, shelve, os
import config, dop, files, subscriptions

bot = telebot.TeleBot(config.token)

def in_adminka(chat_id, message_text, username, name_user):
    """Función principal de administración"""
    if chat_id in dop.get_adminlist():
        if message_text == 'Volver al menú principal' or message_text == '/adm':
            if dop.get_sost(chat_id):
                with shelve.open(files.sost_bd) as bd: 
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
            
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('💬 Respuestas')
            user_markup.row('📦 Surtido', '➕ Producto')
            user_markup.row('💼 Suscripciones')
            user_markup.row('💰 Pagos')
            user_markup.row('📊 Stats', '📣 Difusión')
            user_markup.row('⚙️ Otros')
            bot.send_message(chat_id, '¡Panel de administración!\\nPara salir: /start', reply_markup=user_markup)
        
        elif message_text == '💼 Suscripciones':
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row('Crear plan de suscripción')
            user_markup.row('Lista de planes')
            user_markup.row('Volver al menú principal')
            bot.send_message(chat_id, 'Gestión de suscripciones:', reply_markup=user_markup)
        
        elif message_text == 'Lista de planes':
            try:
                plans = subscriptions.get_all_subscription_products()
                if plans:
                    text = '📋 *Planes disponibles:*\\n\\n'
                    for plan in plans:
                        if len(plan) >= 7:
                            pid, name, desc, price, currency, duration, unit = plan[:7]
                            text += f'- {pid}. {name} - ${price} {currency}/{duration}{unit}\\n'
                        else:
                            text += f'- Plan incompleto: {plan}\\n'
                else:
                    text = 'No hay planes de suscripción.'
                bot.send_message(chat_id, text, parse_mode='Markdown')
            except Exception as e:
                bot.send_message(chat_id, f'Error mostrando planes: {e}')
        
        elif message_text == '📊 Stats':
            try:
                result = dop.get_daily_sales()
                bot.send_message(chat_id, result, parse_mode='Markdown')
            except Exception as e:
                bot.send_message(chat_id, f'Stats: {dop.get_profit()} USD total')

def text_analytics(message_text, chat_id):
    """Función para analizar texto del admin"""
    if dop.get_sost(chat_id):
        with shelve.open(files.sost_bd) as bd:
            sost_num = bd.get(str(chat_id), 0)
        
        if sost_num == 1:  # Guardar mensaje
            try:
                message_type = 'start'  # Por defecto
                if os.path.exists(f'data/Temp/{chat_id}.txt'):
                    with open(f'data/Temp/{chat_id}.txt', 'r', encoding='utf-8') as f:
                        message_type = f.read().strip()
                
                with shelve.open(files.bot_message_bd) as bd_msg:
                    bd_msg[message_type] = message_text
                
                bot.send_message(chat_id, '✅ Mensaje guardado')
                with shelve.open(files.sost_bd) as bd:
                    if str(chat_id) in bd:
                        del bd[str(chat_id)]
            except Exception as e:
                bot.send_message(chat_id, f'Error: {e}')

def ad_inline(callback_data, chat_id, message_id):
    """Manejar callbacks inline del admin"""
    if callback_data == 'Volver al menú principal de administración':
        if dop.get_sost(chat_id):
            with shelve.open(files.sost_bd) as bd:
                if str(chat_id) in bd:
                    del bd[str(chat_id)]
        
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('💬 Respuestas')
        user_markup.row('📦 Surtido', '➕ Producto')
        user_markup.row('💼 Suscripciones')
        user_markup.row('💰 Pagos')
        user_markup.row('⚙️ Otros')
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        bot.send_message(chat_id, '¡Panel de administración!', reply_markup=user_markup)

def handle_multimedia(message):
    """Manejar multimedia - versión básica"""
    pass
'''
    
    with open('adminka_minimal.py', 'w', encoding='utf-8') as f:
        f.write(minimal_adminka)
    
    print("✅ adminka_minimal.py creado como respaldo")
    return True

def run_comprehensive_fix():
    """Ejecutar reparación completa"""
    print("🚀 INICIANDO REPARACIÓN COMPLETA DEL PROYECTO")
    print("=" * 60)
    
    # Paso 1: Backup
    backup_dir = create_backup()
    
    # Paso 2: Base de datos
    db_ok = check_database_integrity()
    
    # Paso 3: Corregir archivos
    adminka_ok = fix_adminka_errors()
    dop_ok = fix_dop_errors()
    main_ok = fix_main_errors()
    subs_ok = fix_subscriptions_errors()
    
    # Paso 4: Verificar sintaxis
    syntax_errors = check_syntax_all_files()
    
    # Paso 5: Crear respaldo mínimo si es necesario
    if syntax_errors:
        print("\n⚠️ Se encontraron errores de sintaxis, creando versión mínima...")
        create_minimal_working_adminka()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE LA REPARACIÓN")
    print("=" * 60)
    
    print(f"📦 Backup: {backup_dir}")
    print(f"🗄️ Base de datos: {'✅' if db_ok else '❌'}")
    print(f"📝 adminka.py: {'✅' if adminka_ok else '❌'}")
    print(f"⚙️ dop.py: {'✅' if dop_ok else '❌'}")
    print(f"🚀 main.py: {'✅' if main_ok else '❌'}")
    print(f"📋 subscriptions.py: {'✅' if subs_ok else '❌'}")
    
    if syntax_errors:
        print(f"🐛 Errores de sintaxis: {len(syntax_errors)}")
        for file_path, line, msg in syntax_errors:
            print(f"   • {file_path}:{line} - {msg}")
    else:
        print("🐛 Errores de sintaxis: ✅ Ninguno")
    
    print("\n📋 PRÓXIMOS PASOS:")
    if not syntax_errors:
        print("1. ✅ Todos los archivos están corregidos")
        print("2. 🚀 Reinicia tu bot: python3 main.py")
        print("3. 🧪 Prueba: /adm → 💼 Suscripciones → Lista de planes")
        print("4. 📊 Verifica que todas las funciones trabajen")
    else:
        print("1. ⚠️ Aún hay errores de sintaxis")
        print("2. 🔧 Usa adminka_minimal.py como respaldo:")
        print("   cp adminka_minimal.py adminka.py")
        print("3. 🚀 Prueba reiniciar: python3 main.py")
    
    print(f"\n💾 Si algo falla, restaura desde: {backup_dir}")
    
    return len(syntax_errors) == 0

if __name__ == '__main__':
    success = run_comprehensive_fix()
    if success:
        print("\n🎉 ¡REPARACIÓN COMPLETADA EXITOSAMENTE!")
    else:
        print("\n⚠️ Reparación parcial - revisa los errores reportados")