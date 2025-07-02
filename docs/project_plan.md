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

## Phase 16: Historical On-Time Scorecard

### 16.1 Scoring Rubric & Windows

* **Windows**: 3 days, 7 days, 14 days, 30 days.
* **Minimum data**: Require each window length of days (e.g. 3 days needs at least 3 days of records).
* **Grade cut-offs** (example—please adjust if you prefer different bands):

  * **A**: ≥ 95% on-time
  * **B**: ≥ 90%
  * **C**: ≥ 80%
  * **D**: ≥ 70%
  * **F**: < 70%

### 16.2 ETL: Build Summary Table

**Table schema** (in DuckDB):

```sql
CREATE TABLE IF NOT EXISTS ontime_scorecard (
  end_date    DATE,       -- the window’s last day (e.g. ’2025-06-30’)
  window_days INT,        -- 3, 7, 14, or 30
  line        TEXT,       -- Regional Rail line name
  pct_on_time DOUBLE,     -- computed % on-time over that window
  grade       TEXT        -- letter grade per rubric
);
```

**Nightly ETL logic** (in your existing pipeline):

1. For each `window_days` in \[3,7,14,30]:
2. Compute `start_date = today() - (window_days - 1) days`.
3. For each `line` in your `schedules` table, calculate

   ```sql
   SELECT 
     AVG(CASE WHEN act_tm <= sched_tm THEN 1 ELSE 0 END) * 100 
   FROM schedules 
   WHERE service_date BETWEEN start_date AND today()
     AND line = :line;
   ```
4. Map that percentage to a grade, then upsert into `ontime_scorecard` with `end_date = today()`.

### 16.3 Dashboard UI: Scorecard View

In `dashboard/app.py` (Streamlit):

1. **Sidebar widgets**:

   * **Window selector** (`st.selectbox`): “3 days”, “7 days”, “14 days”, “30 days”
   * **Date selector** (`st.selectbox` of available `end_date` values from `ontime_scorecard`)
2. **Main panel**:

   * **Table or st.metric cards** listing each `line → grade` for the chosen window & date.
   * A footnote: “Scores computed over X days of data.”

## Phase 17: Data Overview Section

* **Define UI placement**: Add a “Data Overview” tab in your Streamlit app.
* **Load filters**: Expose date-range and (optionally) line selectors.
* **Surface core metrics**: Show total trains and overall on-time percentage as text or metric cards.

## Phase 18: On-Time vs. Late Proportion Chart

* **Data query**: Compute counts of on-time vs. late departures for the selected window.
* **Chart design**: Embed a pie (or donut) chart illustrating those two shares.
* **Contextual labeling**: Include clear labels/percentages so non-technical viewers immediately grasp the split.

## Phase 19: Delay Distribution Histogram
## Phase 18: On-Time vs. Late Proportion Chart

* **Data query**: Compute counts of on-time vs. late departures for the selected window.
* **Chart design**: Embed a pie (or donut) chart illustrating those two shares.
* **Contextual labeling**: Include clear labels/percentages so non-technical viewers immediately grasp the split.

## Phase 19: Delay Distribution Histogram

* **Data bins**: Bucket delays into 0–5 min, 5–10 min, and 10 + min categories.
* **Chart design**: Display a simple bar chart showing train counts in each bin.
* **Interpretation aid**: Add axis titles and a brief caption (“Most delays fall within 0–5 min”).
* **Data bins**: Bucket delays into 0–5 min, 5–10 min, and 10 + min categories.
* **Chart design**: Display a simple bar chart showing train counts in each bin.
* **Interpretation aid**: Add axis titles and a brief caption (“Most delays fall within 0–5 min”).

## Phase 20: Review, QA & Refinement

* **Usability check**: Verify clarity with a sample audience or colleague.
* **Performance test**: Ensure charts render quickly under typical data volumes.
* **Visual polish**: Tweak titles, colors (Streamlit defaults), and layout for maximal readability.

## Phase 21: Deploy & Announce

* **Push to Streamlit Cloud**: Confirm secrets and deployment settings.
* **Share public link**: Announce your new “Data Overview” section to your audience.
* **Monitor feedback**: Gather user reactions for future enhancement.

---

## Success Criteria

- ETL runs nightly without errors.  
- DuckDB contains accurate, timestamped schedules.  
- Tests cover ≥ 90% of code paths.  
- Project is Git-managed and easily extensible for new data sources.