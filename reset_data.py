#!/usr/bin/env python3
"""Utility script to reset local data directory and reinitialize the databases."""

import os
import shutil

import init_db
import setup_discounts
import setup_advertising


def main():
    if os.path.exists('data'):
        confirm = input("This will delete the 'data/' directory. Continue? [y/N]: ").strip().lower()
        if confirm != 'y':
            print('Operation cancelled.')
            return
        shutil.rmtree('data')
        print("✅ 'data/' directory removed")

    init_db.create_database()
    setup_discounts.setup_discount_system()
    setup_advertising.setup_database()
    setup_advertising.create_directories()


if __name__ == '__main__':
    main()

