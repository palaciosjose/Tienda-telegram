#!/usr/bin/env bash
# Instala dependencias y prepara la base de datos para Tienda Telegram
set -e

# Actualizar paquetes e instalar dependencias básicas
if command -v apt >/dev/null; then
    sudo apt update -y
    sudo apt install -y python3 python3-venv python3-pip git sqlite3
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activar entorno
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Inicializar base de datos y estructura
python init_db.py

echo "\n✅ Instalación completada. Configura tus datos en .env y ejecuta:\nsource venv/bin/activate && python main.py"
