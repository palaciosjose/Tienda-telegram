"""Funciones auxiliares para la integración con :mod:`adminka.py`."""

from .ad_manager import AdvertisingManager
from .statistics import StatisticsManager
import files

# Instancia única usada por los helpers de este módulo
_manager = AdvertisingManager(files.main_db)

# Reexportamos la instancia por si otros módulos necesitan acceso directo
manager = _manager


def create_campaign_from_admin(data):
    """Crear una campaña mostrando un mensaje apto para la interfaz admin."""

    try:
        campaign_id = _manager.create_campaign(data)
        return True, f"Campaña creada con ID {campaign_id}"
    except Exception as exc:
        return False, f"Error al crear campaña: {exc}"


def list_campaigns_for_admin():
    """Devolver un resumen de campañas para mostrar en el panel de admin."""

    try:
        campaigns = _manager.get_all_campaigns()
    except Exception as exc:
        return f"Error al obtener campañas: {exc}"

    if not campaigns:
        return "ℹ️ No hay campañas registradas."

    lines = ["📋 *Campañas registradas:*"]
    for camp in campaigns:
        lines.append(f"- {camp['id']}. {camp['name']} ({camp['status']})")
    return "\n".join(lines)


def add_target_group_from_admin(platform, group_id, name=None):
    """Registrar un grupo objetivo y devolver un mensaje para el admin."""

    try:
        ok, msg = _manager.add_target_group(platform, group_id, name)
        return ok, msg
    except Exception as exc:
        return False, f"Error al agregar grupo: {exc}"


# Las funciones existentes en AdvertisingManager se siguen exponiendo si se
# requieren importarlas directamente desde adminka.py.
