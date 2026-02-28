# Muthu Performance Lab

A beginner-friendly, fully local Garmin dashboard for macOS.

This project reads your Garmin `.FIT` workout files from `GARMIN/Activity`, stores run metrics in SQLite, and shows insights in a Streamlit dashboard.

## What this dashboard includes

- Total number of runs
- Total lifetime distance
- Monthly mileage trend
- Pace vs Heart Rate scatter
- Cadence trend over time
- Distance per run over time
- HR Efficiency Score (`pace / avg_hr`)
- Weekly mileage
- 7-day vs 28-day training load ratio

## Project structure

```text
muthu-performance-lab/
├── app.py
├── requirements.txt
├── run_dashboard.sh
├── README.md
├── data/
│   └── garmin_export/
│       └── (put GARMIN folder here)
└── muthu_performance_lab/
    ├── __init__.py
    ├── config.py
    ├── database.py
    ├── fit_ingest.py
    └── metrics.py
```

## Where to place your Garmin folder

Option A (recommended):
1. Copy your exported `GARMIN` folder to:
   `muthu-performance-lab/data/garmin_export/GARMIN`

Option B (already works in your current workspace):
1. Keep `GARMIN` next to this project folder.
2. The app auto-detects common locations, including sibling `GARMIN` folders.

Your `GARMIN` folder should contain:
- `Activity/`
- `Monitor/`
- `Sleep/`
- `HRVStatus/`

> Current app ingests **Activity FIT files** (required by your current scope).

## Beginner setup (macOS)

1. Open Terminal.
2. Go to the project folder:

```bash
cd "/Users/muthukumar/Library/CloudStorage/OneDrive-FICO/Documents/Tech_Playground/Garmin-Dashboard/Garmin Device Data/muthu-performance-lab"
```

3. Run one command:

```bash
./run_dashboard.sh
```

That command will:
- Create a Python virtual environment (`.venv`) if needed
- Install dependencies
- Start the dashboard

When Streamlit starts, it will show a local URL (usually `http://localhost:8501`). Open it in your browser.

## Everyday use

After first setup, run the same command whenever you want:

```bash
./run_dashboard.sh
```

If you add new FIT files, click **Refresh from FIT files** in the sidebar.

## Database details

- SQLite file: `data/performance_lab.db`
- Table: `workouts`
- One row per FIT activity file (upserted by source file path)

## Notes

- Everything runs fully local on your Mac.
- No cloud services are used.
- If a FIT file cannot be parsed, the app continues and logs the issue to:
  `data/ingestion_errors.log`

## Optional future upgrades

1. Sleep vs performance analysis
- Parse `GARMIN/Sleep/*.FIT`
- Correlate sleep score/duration with next-day pace and heart-rate efficiency

2. HRV fatigue tracking
- Parse `GARMIN/HRVStatus/*.FIT`
- Track HRV baseline trend vs weekly mileage and load ratio
- Add simple readiness/fatigue indicator
