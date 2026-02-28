# Muthu Performance Lab

This repo tracks workouts and running with a fully local Garmin dashboard.

You now have **two local dashboards**:
- **Streamlit Dashboard** (original): interactive Python app
- **PWA Dashboard** (new): installable web app (works offline after first load)

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
├── export_pwa_data.py
├── requirements.txt
├── run_dashboard.sh
├── run_pwa.sh
├── README.md
├── data/
│   └── garmin_export/
│       └── (put GARMIN folder here)
├── muthu_performance_lab/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── fit_ingest.py
│   ├── metrics.py
│   └── pwa_export.py
└── pwa/
    ├── index.html
    ├── manifest.webmanifest
    ├── sw.js
    ├── assets/
    │   ├── app.js
    │   ├── styles.css
    │   ├── icon.svg
    │   └── icon-maskable.svg
    └── data/
        └── dashboard_data.json (generated locally)
```

## Where to place your Garmin folder

Option A (recommended):
1. Copy your exported `GARMIN` folder to:
   `muthu-performance-lab/data/garmin_export/GARMIN`

Option B:
1. Keep `GARMIN` next to this project folder.
2. The app auto-detects common locations, including sibling `GARMIN` folders.

Your `GARMIN` folder should contain:
- `Activity/`
- `Monitor/`
- `Sleep/`
- `HRVStatus/`

> Current ingestion scope is `Activity/*.FIT` (running workout metrics).

## Beginner setup (macOS)

1. Open Terminal.
2. Go to the project folder:

```bash
cd "/Users/muthukumar/Library/CloudStorage/OneDrive-FICO/Documents/Tech_Playground/Garmin-Dashboard/Garmin Device Data/muthu-performance-lab"
```

## Run the original Streamlit dashboard

```bash
./run_dashboard.sh
```

## Run the new PWA dashboard

```bash
./run_pwa.sh
```

Then open:
- `http://localhost:8765/pwa/`

To install as an app (Chrome/Edge):
1. Open the URL above.
2. Click **Install App** (button in the page) or browser install prompt.

### Optional: pass GARMIN path manually

If auto-detect does not find your data:

```bash
./run_pwa.sh "/absolute/path/to/GARMIN"
```

## Everyday use

- Add new FIT files.
- Run `./run_pwa.sh` (or `./run_dashboard.sh`).
- PWA data JSON is regenerated each run from SQLite.

## Database details

- SQLite file: `data/performance_lab.db`
- Table: `workouts`
- One row per FIT activity file (upserted by source file path)

## Notes

- Fully local on your Mac.
- No cloud backend is used.
- FIT parsing issues are logged to `data/ingestion_errors.log`.
- Generated PWA data file: `pwa/data/dashboard_data.json`.

## Optional future upgrades

1. Sleep vs performance analysis
- Parse `GARMIN/Sleep/*.FIT`
- Correlate sleep score/duration with next-day pace and heart-rate efficiency

2. HRV fatigue tracking
- Parse `GARMIN/HRVStatus/*.FIT`
- Track HRV baseline trend vs weekly mileage and load ratio
- Add simple readiness/fatigue indicator
