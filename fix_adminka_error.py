#!/usr/bin/env python3
"""
MOSTRAR PROBLEMA EN LÍNEA 750
=============================
Mostrar exactamente qué hay en la línea 750 y cómo corregirlo
"""

def show_problem():
    """Mostrar el problema específico en línea 750"""
    try:
        with open('adminka.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("🔍 MOSTRANDO CONTEXTO LÍNEA 750")
        print("=" * 40)
        
        # Mostrar líneas alrededor de 750
        start = max(0, 745)
        end = min(len(lines), 755)
        
        for i in range(start, end):
            marker = ">>> ERROR " if i == 749 else "    "  # línea 750 = índice 749
            indent_level = len(lines[i]) - len(lines[i].lstrip()) if lines[i].strip() else 0
            print(f"{marker}{i+1:3}: [{indent_level:2}] {repr(lines[i].rstrip())}")
        
        print("\n🔧 DIAGNÓSTICO:")
        
        # Verificar si hay bloques vacíos
        for i in range(745, min(len(lines), 755)):
            line = lines[i].strip()
            if line.endswith(':') and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or (i + 2 < len(lines) and lines[i + 2].strip() and not lines[i + 2].startswith(' ')):
                    print(f"❌ Bloque vacío encontrado en línea {i+1}: {line}")
                    print(f"   Necesita contenido o 'pass'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def quick_fix():
    """Aplicar corrección rápida"""
    print("\n🔧 APLICANDO CORRECCIÓN RÁPIDA...")
    
    try:
        with open('adminka.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Buscar líneas que terminan en : y no tienen contenido
        fixed = False
        
        for i in range(len(lines) - 1):
            line = lines[i].strip()
            if line.endswith(':') and line:
                # Verificar si la siguiente línea está vacía o mal indentada
                next_line = lines[i + 1]
                current_indent = len(lines[i]) - len(lines[i].lstrip())
                
                if (not next_line.strip() or 
                    (next_line.strip() and len(next_line) - len(next_line.lstrip()) <= current_indent)):
                    
                    # Agregar pass con indentación correcta
                    pass_line = ' ' * (current_indent + 4) + 'pass\n'
                    lines.insert(i + 1, pass_line)
                    print(f"✅ Agregado 'pass' después de línea {i+1}: {line}")
                    fixed = True
                    break
        
        if fixed:
            with open('adminka.py', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print("✅ Archivo corregido")
            return True
        else:
            print("❌ No se encontró el problema específico")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_syntax():
    """Verificar sintaxis"""
    try:
        with open('adminka.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, 'adminka.py', 'exec')
        print("✅ ¡SINTAXIS CORRECTA!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
        return False

def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO DE LÍNEA 750")
    print("=" * 30)
    
    if show_problem():
        print("\n¿Aplicar corrección automática? (y/n):")
        response = input().lower()
        
        if response in ['y', 'yes', 'sí', 's', '']:
            if quick_fix():
                if verify_syntax():
                    print("\n🎉 ¡PROBLEMA RESUELTO!")
                    print("\nEjecuta: python3 main.py")
                else:
                    print("\n⚠️ Aún hay errores de sintaxis")
            else:
                print("\n💡 CORRECCIÓN MANUAL NECESARIA:")
                print("1. nano adminka.py")
                print("2. Ve a línea 750")
                print("3. Si ves una línea que termina en ':' sin contenido")
                print("4. Agrega '    pass' en la siguiente línea")
        else:
            print("\n💡 Para corrección manual:")
            print("1. nano adminka.py +750")
            print("2. Busca líneas que terminan en ':' sin contenido")
            print("3. Agrega 'pass' con indentación correcta")

if __name__ == "__main__":
    main()