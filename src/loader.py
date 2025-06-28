"""
Loading module for project-nexline.

This module provides functionality to load cleaned schedule records into the
DuckDB `schedules` table. It handles inserting new records and ignores duplicates
based on the primary key constraints.

Strictly follows PEP8, uses Google style docstrings, and includes type hints.
"""
from datetime import date
from typing import List, Optional

from src.db import get_connection
from src.transformer import CleanRecord


def load_records(
    date_scraped: date,
    train_no: str,
    records: List[CleanRecord]
) -> None:
    """
    Load cleaned schedule records into the DuckDB database.

    Args:
        date_scraped (date): The date for which records were scraped.
        train_no (str): The train number associated with these records.
        records (List[CleanRecord]): A list of cleaned schedule records.

    Raises:
        Exception: Propagates any database errors.
    """
    conn = get_connection()
    insert_sql = (
        """
        INSERT INTO schedules (
            date_scraped, train_no, station, sched_time, est_time, act_time
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (date_scraped, train_no, station) DO NOTHING
        """
    )

    params_list: List[tuple] = []
    for record in records:
        params_list.append(
            (
                date_scraped,
                train_no,
                record["station"],
                record["sched_time"],
                record["est_time"],
                record["act_time"],
            )
        )

    with conn:
        conn.executemany(insert_sql, params_list)
        conn.commit()
    conn.close()
