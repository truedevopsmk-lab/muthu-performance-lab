import sqlite3
from pathlib import Path
from typing import Iterable, Dict, Any


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT UNIQUE NOT NULL,
    source_mtime REAL NOT NULL,
    workout_date TEXT,
    sport TEXT,
    sub_sport TEXT,
    distance_km REAL,
    duration_min REAL,
    avg_hr REAL,
    max_hr REAL,
    avg_cadence REAL,
    avg_pace_min_per_km REAL,
    calories REAL,
    avg_temperature REAL
);
"""


UPSERT_SQL = """
INSERT INTO workouts (
    source_file,
    source_mtime,
    workout_date,
    sport,
    sub_sport,
    distance_km,
    duration_min,
    avg_hr,
    max_hr,
    avg_cadence,
    avg_pace_min_per_km,
    calories,
    avg_temperature
)
VALUES (
    :source_file,
    :source_mtime,
    :workout_date,
    :sport,
    :sub_sport,
    :distance_km,
    :duration_min,
    :avg_hr,
    :max_hr,
    :avg_cadence,
    :avg_pace_min_per_km,
    :calories,
    :avg_temperature
)
ON CONFLICT(source_file) DO UPDATE SET
    source_mtime = excluded.source_mtime,
    workout_date = excluded.workout_date,
    sport = excluded.sport,
    sub_sport = excluded.sub_sport,
    distance_km = excluded.distance_km,
    duration_min = excluded.duration_min,
    avg_hr = excluded.avg_hr,
    max_hr = excluded.max_hr,
    avg_cadence = excluded.avg_cadence,
    avg_pace_min_per_km = excluded.avg_pace_min_per_km,
    calories = excluded.calories,
    avg_temperature = excluded.avg_temperature;
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def upsert_workouts(conn: sqlite3.Connection, rows: Iterable[Dict[str, Any]]) -> int:
    rows = list(rows)
    if not rows:
        return 0

    conn.executemany(UPSERT_SQL, rows)
    conn.commit()
    return len(rows)
