#!/usr/bin/env python3
"""Display campaign schedules and their target groups."""

import sqlite3
import files


def main():
    conn = sqlite3.connect(files.main_db)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, schedule_name, group_ids FROM campaign_schedules ORDER BY id"
    )
    schedules = cur.fetchall()

    if not schedules:
        print("No hay programaciones registradas")
        return

    for sched_id, name, group_ids in schedules:
        print(f"\nProgramación {sched_id}: {name}")
        groups = []
        if group_ids:
            ids = [int(g) for g in str(group_ids).split(',') if g.strip()]
            if ids:
                placeholders = ",".join("?" for _ in ids)
                cur.execute(
                    f"SELECT group_id, topic_id FROM target_groups WHERE id IN ({placeholders})",
                    ids,
                )
                groups = cur.fetchall()
        if not groups:
            print("  (sin grupos asociados)")
        else:
            for gid, topic in groups:
                topic_str = f"/{topic}" if topic is not None else ""
                print(f"  {gid}{topic_str}")

    conn.close()


if __name__ == "__main__":
    main()
