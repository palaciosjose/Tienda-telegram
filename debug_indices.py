import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('data/db/main_data.db')
cursor = conn.cursor()

# Obtener la programación exacta como lo hace el script
cursor.execute('''
SELECT cs.*, c.name, c.message_text, c.media_file_id, c.media_type,
       c.button1_text, c.button1_url, c.button2_text, c.button2_url
FROM campaign_schedules cs
JOIN campaigns c ON cs.campaign_id = c.id
WHERE cs.is_active = 1 AND c.status = 'active'
''')

row = cursor.fetchone()
if row:
    print(f"Total elementos en tupla: {len(row)}")
    for i, item in enumerate(row):
        print(f"[{i}]: {item}")
else:
    print("No hay datos")

conn.close()
