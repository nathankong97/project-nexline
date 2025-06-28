"""Database module for managing DuckDB connection and schema initialization.

This module provides functions to connect to the DuckDB database file and initialize
its schema by loading all SQL DDL files from the `sql/` directory.
"""
from datetime import date
from pathlib import Path
from typing import List

import duckdb

# Base directory of the project (two levels up from this file)
BASE_DIR: Path = Path(__file__).parent.parent
# Path to the DuckDB database file
DB_FILE: Path = BASE_DIR / 'data' / 'schedules.duckdb'
# Directory containing all SQL schema files
SCHEMA_DIR: Path = BASE_DIR / 'sql'


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Get a DuckDB connection to the schedules database file.

    Returns:
        duckdb.DuckDBPyConnection: An open connection to the DuckDB file.
    """
    # Connect to DuckDB, creating the file if it does not exist
    return duckdb.connect(database=str(DB_FILE), read_only=False)


def init_db() -> None:
    """
    Initialize the database schema by executing all DDL files in the SQL directory.

    Iterates over each `.sql` file in `sql/`, sorted alphabetically, and executes their
    contents against the DuckDB database to ensure required tables exist.

    Raises:
        FileNotFoundError: If the schema directory does not exist.
    """
    if not SCHEMA_DIR.exists() or not SCHEMA_DIR.is_dir():
        raise FileNotFoundError(f"Schema directory not found: {SCHEMA_DIR}")

    # Execute all schema DDL files in order
    conn = get_connection()
    for schema_file in sorted(SCHEMA_DIR.glob('*.sql')):
        ddl = schema_file.read_text()
        conn.execute(ddl)
    conn.close()


def get_stored_train_numbers(service_date: date) -> List[str]:
    """
    Retrieve distinct train numbers stored for a given service date.

    Args:
        service_date (date): The service date to filter train numbers by.

    Returns:
        List[str]: A list of train numbers saved for that date.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT train_no FROM train_numbers WHERE date_scraped = ?", [service_date]
        ).fetchall()
    finally:
        conn.close()
    return [row[0] for row in rows]
