#!/usr/bin/env python3
"""Script para ejecutar el sistema de publicidad automatizada"""
import os
import sys
from datetime import datetime
from advertising_system.auto_sender import AutoSender

def load_config():
    tokens_env = os.getenv("TELEGRAM_TOKEN")
    if tokens_env:
        telegram_tokens = [t.strip() for t in tokens_env.split(',') if t.strip()]
    else:
        telegram_tokens = [
            '8107512310:AAGPO-rwj48QwVM8uK41ndj8q4Cy0f5QMKk',
        ]

    return {
        'db_path': 'data/db/main_data.db',
        'telegram_tokens': telegram_tokens,
        'whaticket_url': os.getenv('WHATICKET_URL', 'https://tu-whaticket.com'),
        'whaticket_token': os.getenv('WHATICKET_TOKEN', 'tu_token_whaticket')
    }

def is_running():
    try:
        with open('data/autosender.pid', 'r') as f:
            pid = int(f.read())
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def main():
    config = load_config()
    if is_running():
        print("AutoSender ya está ejecutándose")
        return
    auto_sender = AutoSender(config)
    auto_sender.start()
    print(f"AutoSender iniciado: {datetime.now()}")

if __name__ == '__main__':
    main()
