#!/usr/bin/env python
"""
Migration: Add ML categorization columns to the transactions table.

The server does this automatically on startup via _ensure_ml_columns() in main.py,
so running this script manually is only needed if you want to apply the migration
without restarting the server.

Usage:
    cd backend
    python scripts/migrate_add_ml_columns.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.database.database import engine

COLUMNS = [
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS predicted_category VARCHAR(100)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS prediction_confidence FLOAT",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS categorization_method VARCHAR(20)",
]


def migrate():
    with engine.connect() as conn:
        for stmt in COLUMNS:
            conn.execute(text(stmt))
            print(f"OK  {stmt}")
        conn.commit()
    print("\nMigration complete.")


if __name__ == "__main__":
    migrate()
