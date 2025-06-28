from pathlib import Path

import duckdb
import pytest

import src.db as db


def test_get_connection_creates_file(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    get_connection() should create the DuckDB file if it does not exist
    and return a valid connection.
    """
    tmp_db: Path = tmp_path / "test.duckdb"
    # Override the DB_FILE path
    monkeypatch.setattr(db, "DB_FILE", tmp_db)

    # Ensure file does not yet exist
    assert not tmp_db.exists()

    conn = db.get_connection()
    conn.close()

    # After connecting, the file should exist
    assert tmp_db.exists()

    # Verify we can run a simple query
    result = duckdb.connect(database=str(tmp_db)) \
        .execute("SELECT 123 AS val") \
        .fetchone()
    assert result[0] == 123


def test_init_db_dir_not_found(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    init_db() should raise FileNotFoundError if the schema directory is missing.
    """
    fake_dir: Path = tmp_path / "no_sql_dir"
    monkeypatch.setattr(db, "SCHEMA_DIR", fake_dir)
    # Override DB_FILE to avoid side effects
    monkeypatch.setattr(db, "DB_FILE", tmp_path / "irrelevant.duckdb")

    with pytest.raises(FileNotFoundError):
        db.init_db()


def test_init_db_creates_table(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    init_db() should execute all DDL files in the schema directory
    and create the expected table.
    """
    # Create a temporary schema directory
    schema_dir: Path = tmp_path / "sql"
    schema_dir.mkdir()

    # Write a sample DDL file
    ddl_file: Path = schema_dir / "001_create_schedules.sql"
    ddl_file.write_text(
        """
        CREATE TABLE IF NOT EXISTS schedules (
          id INTEGER
        );
        """
    )

    tmp_db: Path = tmp_path / "test.duckdb"
    monkeypatch.setattr(db, "SCHEMA_DIR", schema_dir)
    monkeypatch.setattr(db, "DB_FILE", tmp_db)

    # Run schema initialization
    db.init_db()

    # Verify the table exists
    conn = duckdb.connect(database=str(tmp_db), read_only=True)
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='main';"
    ).fetchall()
    conn.close()

    table_names = [row[0] for row in tables]
    assert "schedules" in table_names
