from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from muthu_performance_lab.config import DB_PATH, DEFAULT_GARMIN_CANDIDATES, ERROR_LOG_PATH
from muthu_performance_lab.database import get_connection, upsert_workouts
from muthu_performance_lab.fit_ingest import ingest_activity_folder
from muthu_performance_lab.metrics import (
    filter_runs,
    kpi_lifetime_distance_km,
    kpi_total_runs,
    load_workouts_df,
    monthly_mileage,
    training_load_ratio,
    weekly_mileage_km,
)


def detect_default_garmin_path() -> Path | None:
    for candidate in DEFAULT_GARMIN_CANDIDATES:
        if (candidate / "Activity").exists():
            return candidate
    return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_rows(df: pd.DataFrame, cols: list[str]) -> list[dict[str, Any]]:
    records = []
    for _, row in df.iterrows():
        record: dict[str, Any] = {}
        for col in cols:
            value = row[col]
            if isinstance(value, pd.Timestamp):
                record[col] = value.date().isoformat()
            elif pd.isna(value):
                record[col] = None
            else:
                record[col] = value
        records.append(record)
    return records


def refresh_database_from_garmin(garmin_root: Path) -> tuple[int, int]:
    activity_dir = garmin_root / "Activity"
    rows = ingest_activity_folder(activity_dir=activity_dir, error_log_path=ERROR_LOG_PATH)

    conn = get_connection(DB_PATH)
    try:
        count = upsert_workouts(conn, rows)
    finally:
        conn.close()

    return count, len(rows)


def build_dashboard_payload() -> dict[str, Any]:
    conn = get_connection(DB_PATH)
    try:
        all_df = load_workouts_df(conn)
    finally:
        conn.close()

    runs_df = filter_runs(all_df)

    if runs_df.empty:
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "has_data": False,
            "message": "No running workouts available.",
        }

    runs_df = runs_df.sort_values("workout_date")
    monthly_df = monthly_mileage(runs_df)

    latest = runs_df.iloc[-1]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "has_data": True,
        "kpis": {
            "total_runs": kpi_total_runs(runs_df),
            "lifetime_distance_km": round(kpi_lifetime_distance_km(runs_df), 2),
            "weekly_mileage_km": round(weekly_mileage_km(runs_df), 2),
            "training_load_ratio": round(training_load_ratio(runs_df), 3),
            "latest_run_date": latest["workout_date"].date().isoformat(),
            "latest_run_pace": _to_float(latest.get("avg_pace_min_per_km")),
        },
        "series": {
            "monthly_mileage": _clean_rows(monthly_df, ["month", "distance_km"]),
            "pace_vs_hr": _clean_rows(
                runs_df.dropna(subset=["avg_hr", "avg_pace_min_per_km"]),
                ["workout_date", "avg_hr", "avg_pace_min_per_km", "distance_km", "duration_min"],
            ),
            "cadence_trend": _clean_rows(
                runs_df.dropna(subset=["avg_cadence"]),
                ["workout_date", "avg_cadence"],
            ),
            "distance_trend": _clean_rows(runs_df, ["workout_date", "distance_km"]),
            "run_table": _clean_rows(
                runs_df,
                [
                    "workout_date",
                    "distance_km",
                    "duration_min",
                    "avg_hr",
                    "max_hr",
                    "avg_cadence",
                    "avg_pace_min_per_km",
                    "hr_efficiency",
                    "calories",
                    "avg_temperature",
                ],
            ),
        },
    }
    return payload


def export_pwa_json(output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_payload()
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
