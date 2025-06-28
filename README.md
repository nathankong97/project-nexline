# 🚄 Project Nexline

**Pilot ETL & Visualization Pipeline for Public Transit Schedules**

This repository contains a simple, extensible ETL pipeline to collect, transform, and store daily SEPTA train schedules using
DuckDB, with plans to power a future web-based visualization layer. The project is git‑managed, CI‑tested, and designed
to scale to multiple agencies.

---

## 🚀 Highlights

* **Modular, Layered Architecture**: Clear separation of configuration, extraction, fetching, transformation, loading,
  and orchestration.
* **Extensible Fetchers**: Fetch schedules via API packages under `src/fetchers/`; add new endpoints by dropping in a
  new module.
* **Reliable Data Collection**: Collect script (`collect_train_numbers.py`) runs every 2–3 min from 4 AM–1 AM to
  accumulate a full day’s train numbers.
* **DuckDB Storage**: Lightweight, zero‑server analytics store; stores both raw schedule snapshots and collected train
  numbers.
* **CLI Orchestration**: `run_etl.py` supports flags for date, dry‑run, verbosity, and concurrency.
* **Automated Testing & CI**: Pytest, flake8 linting, and coverage checks on every push via GitHub Actions.
* **Easy Deployment**: Versioned cronjobs file under `deploy/cronjobs.txt` for automated scheduling.

---

## 📂 Repository Structure

```
project-nexline/
├── .github/workflows/ci.yml       # CI pipeline (tests, lint, coverage)
├── config.py                      # Central constants and URLs
├── data/                          # DuckDB database files (git‑ignored)
├── deploy/cronjobs.txt            # Versioned crontab entries
├── docs/                          # (Future) documentation or design artifacts
├── logs/                          # Cron logs (git‑ignored)
├── requirements.txt               # Python dependencies
├── sql/                           # DDL for DuckDB tables
│   ├── create_schedules_table.sql
│   └── create_train_numbers_table.sql
├── scripts/
│   ├── collect_train_numbers.py   # Periodic train‑number collection
│   ├── init_db.py                 # One‑off DB initialization
│   └── run_etl.py                 # Nightly ETL orchestration
├── src/
│   ├── db.py                      # DuckDB connection & schema + data access helpers
│   ├── extractors.py              # TrainView API extraction
│   ├── fetchers/                  # Package of API fetch modules
│   │   ├── __init__.py
│   │   └── rrschedules.py         # RRSchedules endpoint
│   ├── loader.py                  # Load cleaned records into DuckDB
│   ├── transformer.py             # Normalize & validate raw data
│   └── ...                        # Future extensions
├── tests/                         # Unit tests for all modules
└── README.md                      # This file
```

---

## ⚙️ Getting Started

1. **Clone the repo**

   ```bash
   git clone https://github.com/nathankong97/project-nexline.git
   cd project-nexline
   ```

2. **Set up a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .venv\Scripts\activate    # Windows PowerShell
   ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Initialize the database**

   ```bash
   python scripts/init_db.py
   ```

5. **Run a dry‑run ETL**

   ```bash
   python scripts/run_etl.py --dry-run
   ```

6. **Inspect data in DuckDB** (via Python REPL or DataGrip)

   ```python
   import duckdb
   conn = duckdb.connect('data/schedules.duckdb')
   print(conn.execute('SELECT * FROM train_numbers LIMIT 5').fetchall())
   ```

---

## 🛠 Usage

**Nightly ETL**:

```bash
python3 scripts/run_etl.py [--db-path PATH] [--date YYYY-MM-DD] [--workers N] [--verbose]
```

* `--db-path`: Path to DuckDB file (default: `./.tmp/test.duckdb`)
* `--date`: Target service date (default: yesterday)
* `--workers`: Concurrent fetch threads (default: 10)
* `--dry-run`: Skip writes, only report counts
* `--verbose`: Enable debug logging

**Continuous Collection**:

```bash
python3 scripts/collect_train_numbers.py
```

Run every 2–3 minutes (4 AM–2 AM) via cron as defined in `deploy/cronjobs.txt`.

---

## 🎯 Next Milestones

* **Web Visualization**: Integrate an OLAP layer, build a React dashboard to plot delays and schedules.
* **Additional Agencies**: Add fetchers for MTA, NJ Transit, Amtrak, etc.
* **Enhanced Analytics**: Build summary tables, weekly/monthly rollups in DuckDB or BI tools.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
