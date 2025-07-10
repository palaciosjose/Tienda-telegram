#!/usr/bin/env python3
"""Resetear por completo la base de datos y archivos de 'data/'.
Elimina la carpeta data/ y vuelve a ejecutar los scripts de inicialización."""

import os
import shutil
import init_db
import setup_advertising
import setup_discounts


def reset():
    confirm = input(
        "Esto eliminará la carpeta 'data/'. ¿Seguro que deseas continuar? (s/N): "
    )
    if confirm.lower() != "s":
        print("Operación cancelada")
        return

    shutil.rmtree("data", ignore_errors=True)
    print("🗑️ Carpeta 'data/' eliminada")

    init_db.create_database()

    setup_discounts.setup_discount_system()
    setup_advertising.setup_database()
    setup_advertising.create_directories()
    print("✅ Sistema reiniciado")


if __name__ == "__main__":
    reset()
