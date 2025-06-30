"""Collect script for project-nexline.

Runs periodically to upsert unique train numbers into the `train_numbers` table for
the correct service date. Service date rolls over at 2 AM (times between 00:00 and
01:29 map to the previous calendar date).
"""
import sys
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import Set, List, Tuple

# Ensure project root is on sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db import get_connection, init_db
from src.extractors import get_train_numbers


def get_service_date(now: datetime) -> date:
    """
    Determine the service date for a given timestamp.

    Args:
        now (datetime): The current timestamp.

    Returns:
        date: If `now` is before 01:30, returns yesterday's date; otherwise today's date.
    """
    cutoff = time(hour=1, minute=30)
    if now.time() < cutoff:
        return (now - timedelta(days=1)).date()
    return now.date()


def main() -> None:
    """
    Main entry point for collecting train numbers.

    Initializes the database schema, fetches the current set of train numbers,
    and upserts them into the `train_numbers` table for the service date.
    """
    # Initialize schema (creates both schedules and train_numbers tables)
    init_db()

    now: datetime = datetime.now()
    service_date: date = get_service_date(now)

    # Fetch current train numbers
    train_numbers: Set[str] = get_train_numbers()

    # Prepare upsert parameters
    params: List[Tuple[date, str]] = [
        (service_date, tn) for tn in train_numbers
    ]

    # Upsert into train_numbers table
    conn = get_connection()
    upsert_sql = (
        """
        INSERT INTO train_numbers (date_scraped, train_no)
        VALUES (?, ?)
        ON CONFLICT (date_scraped, train_no) DO NOTHING
        """
    )

    with conn:
        conn.executemany(upsert_sql, params)
    conn.close()

    print(f"Upserted {len(params)} train numbers for {service_date}")


if __name__ == "__main__":
    main()
