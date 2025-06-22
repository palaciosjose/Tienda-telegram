#!/usr/bin/env bash
# Actualiza el repositorio y aplica posibles cambios de dependencias y base de datos
set -e

# Obtener últimas actualizaciones del repositorio
if [ -d .git ]; then
    git pull
fi

# Activar entorno virtual
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Actualizar dependencias
pip install -r requirements.txt

# Ejecutar posibles migraciones o ajustes de base de datos
python init_db.py

echo "\n✅ Actualización completada. Reinicia el bot si está en ejecución."
