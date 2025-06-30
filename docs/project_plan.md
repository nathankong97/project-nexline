# Project Plan

## Goals

1. Ingest daily train-schedule data from SEPTA.  
2. Store cleansed records in DuckDB.  
3. Lay the groundwork for future OLAP and web-visualization layers.

---

## Phase 1: Environment Setup
- Create and activate `.venv`
- Install dependencies via `pip install -r requirements.txt`
- Initialize Git repository and push to GitHub
- Configure PyCharm to use the project interpreter

## Phase 2: Database Schema & Connection
- Implement `src/db.py` to open DuckDB and define the `schedules` table
- Verify schema with a simple connection test

## Phase 3: Extraction Layer
- In `src/extractors.py`, implement `get_train_numbers()` to scrape `/TrainView/index.php`

## Phase 4: Fetchers Package
- Create `src/fetchers/rrschedules.py` with a function to call RRSchedules
- Add rate-limit (4 req/sec) and retry logic
- Write unit tests for the fetcher module

## Phase 5: Transformation
- In `src/transformer.py`, implement `transform(raw_records)`:
  - Convert times to 24-hour `TIME` format
  - Filter out duplicates and invalid entries
- Write tests for edge cases (e.g., missing or malformed times)

## Phase 6: Loading
- In `src/loader.py`, implement `load(records)` to upsert into DuckDB
- Ensure incremental loads don’t create duplicates
- Test upsert behavior and conflict handling

## Phase 7: Orchestration Script
- Build `scripts/run_etl.py` to wire extractor → fetchers → transformer → loader
- Embed logging, rate limiting, and error handling
- Perform a local end-to-end run to validate the full pipeline

## Phase 8: Testing & CI
- Expand unit tests and add integration tests against sample responses
- Configure GitHub Actions to run all tests on every push

## Phase 9: Deployment & Scheduling
- Deploy `run_etl.py` to the remote server
- Set up a crontab entry to execute the script nightly at 2:00 AM

## Phase 10: Documentation & Handoff
- Finalize `README.md` with setup, usage, and extension instructions
- Document where and how to add new APIs or custom logic

---

## Phase 11: Dashboard Scaffold

* **Folder & entrypoint**

  * Create `dashboard/` directory
  * Add `dashboard/app.py`
* **Dependencies**

  * Add `streamlit`, `duckdb`, `pandas` to `requirements.txt`
* **Configuration**

  * Read DuckDB filepath from an environment variable (for Streamlit Cloud)
  * Add `.streamlit/secrets.toml` stub

## Phase 12: Data Loading & Cache

* In `app.py`, connect to DuckDB and load the `schedules` table via `pandas.read_sql()`
* Wrap the load in `@st.cache_data` to avoid repeated queries
* Expose a “Last updated” timestamp in the sidebar

## Phase 13: Filters & UI Controls

* Add sidebar widgets:

  * **Date picker** (`st.date_input`) for range selection
  * **Multiselect** for `train_no` and `station`
* Write helper functions to apply filters to the DataFrame

## Phase 14: Visualizations & Metrics

* Time-series chart of average delay by day (`st.line_chart`)
* Histogram or boxplot of delay distribution (`st.altair_chart`)
* Data table preview (`st.dataframe`) limited to 10–15 rows
* Summary stats (mean, median, max delay) in `st.metric` cards

## Phase 15: Deployment & Automation

* **Streamlit Cloud setup**:

  * Connect GitHub repo to Streamlit Cloud
  * Set `DUCKDB_PATH` in secrets
* **GitHub Actions**: (optional) nightly ETL → push updated `data/*.duckdb` → trigger a redeploy
* **Success check**: validate that live app refreshes with new data

---

## Success Criteria

- ETL runs nightly without errors.  
- DuckDB contains accurate, timestamped schedules.  
- Tests cover ≥ 90% of code paths.  
- Project is Git-managed and easily extensible for new data sources.