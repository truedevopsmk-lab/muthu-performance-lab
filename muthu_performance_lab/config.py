from pathlib import Path

# Project root folder (where app.py lives).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default places where the GARMIN folder might exist.
# The app checks these paths in order and picks the first one that exists.
DEFAULT_GARMIN_CANDIDATES = [
    PROJECT_ROOT / "data" / "garmin_export" / "GARMIN",
    PROJECT_ROOT / "GARMIN",
    PROJECT_ROOT.parent / "GARMIN",
]

DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "performance_lab.db"
ERROR_LOG_PATH = DATA_DIR / "ingestion_errors.log"
