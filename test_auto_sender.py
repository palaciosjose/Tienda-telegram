#!/usr/bin/env python3
"""Run AutoSender once to process scheduled campaigns."""

__test__ = False  # prevent pytest from treating this module as a test

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute AutoSender.process_campaigns once")
    parser.add_argument('--token', action='append', help='Telegram bot token (can be used multiple times)')
    parser.add_argument('--db', default='data/db/main_data.db', help='Path to the advertising database')
    parser.add_argument('--shop-id', type=int, help='Shop identifier')
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    from advertising_system.auto_sender import AutoSender

    tokens = args.token
    if not tokens:
        token_env = os.getenv('TELEGRAM_TOKEN')
        if token_env:
            tokens = [t.strip() for t in token_env.split(',') if t.strip()]

    config = {'db_path': args.db}
    if tokens:
        config['telegram_tokens'] = tokens
    if args.shop_id is not None:
        config['shop_id'] = args.shop_id
    elif os.getenv('SHOP_ID'):
        try:
            config['shop_id'] = int(os.getenv('SHOP_ID'))
        except ValueError:
            pass

    sender = AutoSender(config)
    result = sender.process_campaigns()
    print(f"Processed: {result}")


if __name__ == '__main__':
    main()
