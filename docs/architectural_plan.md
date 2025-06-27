# Architectural Plan

## Overview

A simple, layered ETL pipeline designed for end-of-day train-schedule ingestion and storage. Each layer has a single responsibility, enabling easy extension, testing, and maintenance.

## Layers & Responsibilities

1. **Configuration (`config.py`)**  
   - Centralize all constants: API base URLs, endpoints, DuckDB file path, rate limits, and retry settings.  
   - Justification: Single source of truth for environment-specific values; simplifies future refactoring.

2. **Extraction (`src/extractors.py`)**  
   - Scrape `/TrainView/index.php` every 2–3 min during service hours to build a deduplicated set of train numbers.  
   - Exposes a function `get_train_numbers() → Set[str]`.  
   - Justification: Keeps HTML-parsing logic separate from API-calling logic.

3. **Fetching (`src/fetchers/`)**  
   - A package where each module handles one API:  
     - `trainview.py` – logic to fetch and parse the train-list page.  
     - `rrschedules.py` – logic to call the RRSchedules endpoint for a single train number.  
   - Each module exposes a uniform interface, e.g. `fetch(schedule_id: str) → List[ScheduleRecord]`.  
   - Justification: Encourages clear boundaries; future endpoints slot in seamlessly.

4. **Transformation (`src/transformer.py`)**  
   - Normalize and validate raw JSON:  
     - Convert `“3:08 pm”` → `15:08` (24-hour `TIME` format).  
     - Filter out duplicates and invalid/missing data.  
   - Exposes `transform(raw_records: List[dict]) → List[CleanRecord]`.  
   - Justification: Central location for data-shaping logic; simplifies loader.

5. **Loading (`src/loader.py` + `src/db.py`)**  
   - **`db.py`**: Opens DuckDB connection, ensures the `schedules` table exists:  
     ```sql
     CREATE TABLE IF NOT EXISTS schedules (
       date_scraped DATE,
       train_no    VARCHAR,
       station     VARCHAR,
       sched_time  TIME,
       est_time    TIME,
       PRIMARY KEY (date_scraped, train_no, station)
     );
     ```  
   - **`loader.py`**: Accepts `List[CleanRecord]`, performs upserts into DuckDB.  
   - Justification: DuckDB offers file-based simplicity with analytic performance; no extra server overhead.

6. **Orchestration (`scripts/run_etl.py`)**  
   - Coordinates the flow:  
     1. Call extractor → get train numbers  
     2. For each number, invoke fetchers.rrschedules → raw JSON  
     3. Pass raw JSON to transformer → clean records  
     4. Pass clean records to loader → persist to DuckDB  
   - Adds rate-limit throttling (4 req/sec) and retry logic.  
   - Justification: Single entry-point; easy to wrap in cron.

## Error Handling & Robustness

- **Rate Limiting**: Pause 0.25 s between API calls.  
- **Retries**: Exponential back-off on 5xx errors (max 3 attempts).  
- **Logging**: Standard Python `logging` with timestamps, levels, and context.  

## Testing Strategy

- **Unit Tests (`tests/`)**  
  - Mock HTML for extractor; mock HTTP responses for each fetcher.  
  - Test transformation edge cases (midnight, invalid times).  
- **Integration Tests**  
  - End-to-end against a small sample of real responses.  
- Justification: Layer isolation guarantees high confidence before deployment.
