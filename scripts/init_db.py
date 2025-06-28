#!/usr/bin/env python3
"""Initialize the DuckDB database schema for project-nexline.

This script reads the SQL DDL from `sql/create_schedules_table.sql` and executes it
against the DuckDB database file to ensure the `schedules` table exists.
"""

import sys

from src.db import init_db  # noqa: E402


def main() -> None:
    """Run the database initialization and report status."""
    try:
        init_db()
        print("✅ Database schema initialized successfully.")
    except Exception as error:
        print(f"❌ Failed to initialize schema: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
