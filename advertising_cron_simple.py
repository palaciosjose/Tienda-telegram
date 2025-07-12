#!/usr/bin/env python3
import os
from datetime import datetime
from dotenv import load_dotenv
from advertising_system.auto_sender import AutoSender

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

load_dotenv()
config = load_config()
auto_sender = AutoSender(config)

print(f"AutoSender iniciado: {datetime.now()}")
result = auto_sender._check_and_send_campaigns()
print(f"Resultado: {result}")
