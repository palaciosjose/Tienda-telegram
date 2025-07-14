#!/usr/bin/env python3
"""Script para ejecutar el sistema de publicidad automatizada"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from advertising_system.auto_sender import AutoSender

load_dotenv()

def load_config():
    tokens_env = os.getenv("TELEGRAM_TOKEN")
    if not tokens_env:
        raise SystemExit("TELEGRAM_TOKEN environment variable is required")
    telegram_tokens = [t.strip() for t in tokens_env.split(',') if t.strip()]
    if not telegram_tokens:
        raise SystemExit("TELEGRAM_TOKEN is empty")

    return {
        'db_path': 'data/db/main_data.db',
        'telegram_tokens': telegram_tokens
    }

def is_running():
    pid_file = 'data/autosender.pid'
    if not os.path.exists(pid_file):
        return False
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read())
        os.kill(pid, 0)
        return True
    except Exception:
        try:
            os.remove(pid_file)
        except Exception:
            pass
        return False


def main():
    config = load_config()
    if is_running():
        print("AutoSender ya está ejecutándose")
        return
    auto_sender = AutoSender("data/db/main_data.db")
    auto_sender.start()
    print(f"AutoSender iniciado: {datetime.now()}")

if __name__ == '__main__':
    main()
