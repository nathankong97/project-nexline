from datetime import date, time
from pathlib import Path
from typing import List, Optional, Tuple

import duckdb
import pytest

import src.db as db_module
from src.loader import load_records
from src.transformer import CleanRecord


def setup_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Set up a temporary DuckDB database and initialize the schema.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.
        monkeypatch (pytest.MonkeyPatch): MonkeyPatch fixture.

    Returns:
        Path: Path to the temporary DuckDB file.
    """
    tmp_db: Path = tmp_path / "test_schedules.duckdb"
    # Override the DB_FILE path for testing
    monkeypatch.setattr(db_module, "DB_FILE", tmp_db)
    # Initialize schema
    db_module.init_db()
    return tmp_db


def fetch_all_records(db_path: Path) -> List[Tuple[date, str, str, time, time, Optional[str]]]:
    """
    Helper to fetch all rows from the schedules table.

    Args:
        db_path (Path): Path to the DuckDB file.

    Returns:
        List[Tuple]: Rows as tuples of (date_scraped, train_no, station,
            sched_time, est_time, act_time).
    """
    conn = duckdb.connect(database=str(db_path), read_only=True)
    rows = conn.execute(
        "SELECT date_scraped, train_no, station, sched_time, est_time, act_time "
        "FROM schedules"
    ).fetchall()
    conn.close()
    return rows


def test_load_records_inserts_and_none_act_time(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    load_records should insert records, storing None for act_time when appropriate.
    """
    db_path = setup_database(tmp_path, monkeypatch)
    # Prepare a cleaned record with act_time = None
    clean: List[CleanRecord] = [
        CleanRecord(
            station="StationX",
            sched_time=time(hour=9, minute=0),
            est_time=time(hour=9, minute=5),
            act_time=None
        )
    ]

    load_records(date(2025, 6, 27), "123", clean)
    rows = fetch_all_records(db_path)

    assert len(rows) == 1
    record = rows[0]
    assert record[0] == date(2025, 6, 27)
    assert record[1] == "123"
    assert record[2] == "StationX"
    assert record[3] == time(hour=9, minute=0)
    assert record[4] == time(hour=9, minute=5)
    assert record[5] is None


def test_load_records_handles_duplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    load_records should ignore duplicate records based on the primary key.
    """
    db_path = setup_database(tmp_path, monkeypatch)
    # Two identical cleaned records
    clean: List[CleanRecord] = [
        CleanRecord(
            station="StationY",
            sched_time=time(hour=10, minute=0),
            est_time=time(hour=10, minute=5),
            act_time=time(hour=10, minute=7)
        )
    ]

    # First load
    load_records(date(2025, 6, 27), "456", clean)
    # Second load with the same record
    load_records(date(2025, 6, 27), "456", clean)

    rows = fetch_all_records(db_path)
    # Should only have one entry despite two loads
    assert len(rows) == 1
    record = rows[0]
    assert record[1] == "456"
    assert record[2] == "StationY"


def test_load_records_multiple_trains_and_dates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    load_records should correctly insert records for different trains and dates.
    """
    db_path = setup_database(tmp_path, monkeypatch)
    clean1: List[CleanRecord] = [
        CleanRecord(
            station="A1",
            sched_time=time(hour=6, minute=0),
            est_time=time(hour=6, minute=5),
            act_time=None
        )
    ]
    clean2: List[CleanRecord] = [
        CleanRecord(
            station="B1",
            sched_time=time(hour=7, minute=0),
            est_time=time(hour=7, minute=5),
            act_time=time(hour=7, minute=7)
        )
    ]

    load_records(date(2025, 6, 27), "100", clean1)
    load_records(date(2025, 6, 28), "200", clean2)

    rows = fetch_all_records(db_path)
    # Two distinct entries should exist
    assert len(rows) == 2
    entries = {(r[0], r[1], r[2]) for r in rows}
    assert (date(2025, 6, 27), "100", "A1") in entries
    assert (date(2025, 6, 28), "200", "B1") in entries
