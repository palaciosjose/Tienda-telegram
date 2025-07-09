"""Funciones auxiliares para la integración con :mod:`adminka.py`."""

from .ad_manager import AdvertisingManager
from .statistics import StatisticsManager
import files
import os
import json

# Instancia única usada por los helpers de este módulo
_manager = AdvertisingManager(files.main_db, shop_id=1)

# Reexportamos la instancia por si otros módulos necesitan acceso directo
manager = _manager

def set_shop_id(shop_id):
    """Actualizar la instancia interna con el shop_id indicado."""
    global _manager, manager
    _manager = AdvertisingManager(files.main_db, shop_id=shop_id)
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


def get_admin_telegram_groups(bot, admin_id):
    """Obtener grupos donde el usuario admin es miembro."""

    try:
        updates = bot.get_updates()
    except Exception:
        updates = []

    groups = {}
    for upd in updates:
        chat = None
        if getattr(upd, "message", None):
            chat = upd.message.chat
        elif getattr(upd, "channel_post", None):
            chat = upd.channel_post.chat

        if chat and chat.type in ("group", "supergroup"):
            gid = chat.id
            if gid in groups:
                continue
            try:
                member = bot.get_chat_member(gid, admin_id)
                if getattr(member, "status", "") not in ("left", "kicked"):
                    groups[gid] = chat.title or str(gid)
            except Exception:
                continue

    return [{"id": gid, "title": title} for gid, title in groups.items()]


# Las funciones existentes en AdvertisingManager se siguen exponiendo si se
# requieren importarlas directamente desde adminka.py.
