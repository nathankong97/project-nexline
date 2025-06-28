"""
Orchestration script for project-nexline.

Coordinates the full ETL pipeline: reads collected train numbers, fetches schedules
concurrently, transforms records, and loads them into a DuckDB database.

Usage:
    python -m scripts.run_etl [--db-path DB_PATH]
                              [--date YYYY-MM-DD]
                              [--dry-run]
                              [--verbose]
                              [--workers N]
"""
import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Ensure project root is on sys.path for module imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import src.db as db_module
from src.db import init_db, get_stored_train_numbers
from src.fetchers.rrschedules import ScheduleRecord, fetch_schedule
from src.loader import load_records
from src.transformer import transform


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the ETL script.

    Returns:
        argparse.Namespace: Parsed arguments namespace.
    """
    default_db = project_root / '.tmp' / 'test.duckdb'

    parser = argparse.ArgumentParser(
        description='Run the project-nexline ETL pipeline.'
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        default=default_db,
        help='Path to the DuckDB database file.'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date for which to run ETL (YYYY-MM-DD). Defaults to yesterday.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run ETL without writing to the database.'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging.'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of concurrent fetch workers.'
    )
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """
    Configure logging to stdout with the appropriate level.

    Args:
        verbose (bool): If True, set level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s: %(message)s',
    )


def main() -> None:
    """
    Main entry point for the ETL process.

    Orchestrates fetching, transformation, and loading of
    train schedule data based on previously collected train numbers.
    Supports dry-run to skip database writes.
    """
    args = parse_args()
    configure_logging(args.verbose)

    # Determine the ETL date
    if args.date:
        try:
            etl_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logging.error('Invalid date format. Use YYYY-MM-DD.')
            return
    else:
        etl_date = date.today() - timedelta(days=1)
    logging.info(f'Running ETL for date: {etl_date}')

    # Prepare the database and schema
    db_module.DB_FILE = args.db_path
    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    logging.info(f'Using database at: {args.db_path}')

    # Read distinct train numbers for this date
    train_numbers: List[str] = get_stored_train_numbers(etl_date)
    logging.info(f'Loaded {len(train_numbers)} train numbers from store.')

    # Concurrent fetching of schedules
    raw_data: Dict[str, List[ScheduleRecord]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(fetch_schedule, tn): tn for tn in train_numbers}
        for future in as_completed(future_map):
            tn = future_map[future]
            try:
                raw_data[tn] = future.result()
                logging.info(f'Fetched {len(raw_data[tn])} records for train {tn}')
            except Exception as exc:
                logging.error(f'Failed to fetch schedule for train {tn}: {exc}')

    # Dry run: report counts without loading
    if args.dry_run:
        total = 0
        for tn, records in raw_data.items():
            cleaned = transform(records)
            count = len(cleaned)
            total += count
            logging.info(f'(dry-run) Would load {count} records for train {tn}')
        logging.info(f'(dry-run) ETL complete. Total records processed: {total}')
        return

    # Transformation and loading into schedules table
    total_loaded = 0
    for tn, records in raw_data.items():
        cleaned = transform(records)
        load_records(etl_date, tn, cleaned)
        count = len(cleaned)
        total_loaded += count
        logging.info(f'Loaded {count} records for train {tn}')

    logging.info(f'ETL complete. Total records loaded: {total_loaded}')


if __name__ == '__main__':
    main()
