import sqlite3
import telebot
import files
import config
from datetime import datetime

bot = telebot.TeleBot(config.token)

def validate_purchase_by_user(user_id=None, username=None):
    """Valida las compras de un usuario específico"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT id, username, name_good, amount, price, payment_method, timestamp 
                FROM purchases 
                WHERE id = ?
                ORDER BY rowid DESC
            """, (user_id,))
        elif username:
            clean_username = username.replace('@', '')
            cursor.execute("""
                SELECT id, username, name_good, amount, price, payment_method, timestamp 
                FROM purchases 
                WHERE username = ?
                ORDER BY rowid DESC
            """, (clean_username,))
        else:
            return "❌ Debes proporcionar user_id o username"
        
        purchases = cursor.fetchall()
        con.close()
        
        if not purchases:
            return "❌ No se encontraron compras para este usuario"
        
        response = f"📋 **Historial de compras validado:**\n\n"
        total_spent = 0
        
        for i, purchase in enumerate(purchases, 1):
            user_id, username, product, amount, price, payment_method, timestamp = purchase
            total_spent += price
            
            # Formatear timestamp
            time_str = "Fecha no disponible"
            if timestamp:
                try:
                    if 'T' in timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime("%d/%m/%Y %H:%M")
                    else:
                        time_str = str(timestamp)
                except:
                    time_str = str(timestamp)
            
            response += f"🛒 **Compra #{i}**\n"
            response += f"📦 **Producto:** {product}\n"
            response += f"🔢 **Cantidad:** {amount}\n"
            response += f"💰 **Precio:** ${price} USD\n"
            response += f"💳 **Método:** {payment_method or 'No especificado'}\n"
            response += f"📅 **Fecha:** {time_str}\n"
            response += f"👤 **ID:** `{user_id}`\n"
            response += f"📱 **Username:** @{username}\n"
            response += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        response += f"💎 **Total gastado:** ${total_spent} USD\n"
        response += f"🛍️ **Total compras:** {len(purchases)}"
        
        return response
        
    except Exception as e:
        return f"❌ Error consultando base de datos: {e}"

def get_purchase_stats():
    """Obtiene estadísticas de compras"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        # Estadísticas generales
        cursor.execute("SELECT COUNT(*), SUM(price), COUNT(DISTINCT id) FROM purchases")
        result = cursor.fetchone()
        total_purchases, total_revenue, unique_buyers = result if result else (0, 0, 0)
        
        # Top productos
        cursor.execute("""
            SELECT name_good, COUNT(*) as sales, SUM(price) as revenue 
            FROM purchases 
            GROUP BY name_good 
            ORDER BY sales DESC 
            LIMIT 5
        """)
        top_products = cursor.fetchall()
        
        # Métodos de pago
        cursor.execute("""
            SELECT payment_method, COUNT(*), SUM(price) 
            FROM purchases 
            WHERE payment_method IS NOT NULL AND payment_method != ''
            GROUP BY payment_method
        """)
        payment_methods = cursor.fetchall()
        
        con.close()
        
        response = "📊 **Estadísticas de Ventas:**\n\n"
        response += f"🛍️ **Total compras:** {total_purchases or 0}\n"
        response += f"💰 **Ingresos totales:** ${total_revenue or 0} USD\n"
        response += f"👥 **Compradores únicos:** {unique_buyers or 0}\n\n"
        
        if top_products:
            response += "🏆 **Top Productos:**\n"
            for product, sales, revenue in top_products:
                response += f"• {product}: {sales} ventas (${revenue} USD)\n"
        
        if payment_methods:
            response += "\n💳 **Métodos de Pago:**\n"
            for method, count, revenue in payment_methods:
                method_name = method or "No especificado"
                response += f"• {method_name}: {count} transacciones (${revenue} USD)\n"
        
        return response
        
    except Exception as e:
        return f"❌ Error: {e}"

def search_recent_purchases(hours=24):
    """Busca compras recientes"""
    try:
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        
        # Para SQLite, usamos una aproximación con rowid
        cursor.execute(f"""
            SELECT id, username, name_good, amount, price, payment_method, timestamp 
            FROM purchases 
            ORDER BY rowid DESC 
            LIMIT 50
        """)
        
        purchases = cursor.fetchall()
        con.close()
        
        if not purchases:
            return f"❌ No hay compras recientes"
        
        response = f"📊 **Compras recientes:**\n\n"
        total = 0
        
        for purchase in purchases:
            user_id, username, product, amount, price, payment_method, timestamp = purchase
            total += price
            
            time_str = ""
            if timestamp:
                try:
                    if 'T' in timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime("%H:%M")
                    else:
                        time_str = str(timestamp)[:10]
                except:
                    time_str = "N/A"
            
            response += f"🛒 @{username} - {product} x{amount} - ${price} ({payment_method or 'N/A'}) {time_str}\n"
        
        response += f"\n💰 **Total:** ${total} USD | 🛍️ **Ventas:** {len(purchases)}"
        return response
        
    except Exception as e:
        return f"❌ Error: {e}"
