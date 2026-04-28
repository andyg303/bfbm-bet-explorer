"""One-off migration: add performance indexes to the `bets` table.

Adds two partial composite indexes that target the hot dashboard query pattern
(`user_id = ? AND is_deleted = false AND is_archived = false`):

  * idx_bets_user_active        — speeds up filter-options, summary-stats,
                                  strategy-stats and odds-bands-profit.
  * idx_bets_user_starttime     — also covers the ORDER BY/GROUP BY start_time
                                  used by monthly-pl and pl-over-time.

Both are created with `IF NOT EXISTS` so the script is safe to re-run.

Usage (from repo root):
    # Local Docker dev DB
    docker compose exec backend python scripts/add_performance_indexes.py

    # Live server (after `git pull && docker compose -f docker-compose.prod.yml up -d --build`)
    docker compose -f docker-compose.prod.yml exec backend python scripts/add_performance_indexes.py
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()


INDEXES = [
    (
        "idx_bets_user_active",
        """
        CREATE INDEX IF NOT EXISTS idx_bets_user_active
            ON bets (user_id)
            WHERE is_deleted = false AND is_archived = false
        """,
    ),
    (
        "idx_bets_user_starttime",
        """
        CREATE INDEX IF NOT EXISTS idx_bets_user_starttime
            ON bets (user_id, start_time)
            WHERE is_deleted = false AND is_archived = false
        """,
    ),
]


def add_performance_indexes() -> None:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    # autocommit so each CREATE INDEX runs in its own transaction; keeps the
    # script idempotent and avoids any long lock if it ever needs to rebuild.
    conn.autocommit = True
    cur = conn.cursor()
    try:
        for name, ddl in INDEXES:
            print(f"→ ensuring {name} …", flush=True)
            cur.execute(ddl)
            print(f"  ✓ {name}", flush=True)

        # Show what we now have on the bets table for sanity.
        cur.execute(
            """
            SELECT indexname
              FROM pg_indexes
             WHERE schemaname = 'public' AND tablename = 'bets'
             ORDER BY indexname
            """
        )
        print("\nIndexes on `bets` after migration:")
        for (idx,) in cur.fetchall():
            print(f"  • {idx}")
        print("\nDone.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    try:
        add_performance_indexes()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
