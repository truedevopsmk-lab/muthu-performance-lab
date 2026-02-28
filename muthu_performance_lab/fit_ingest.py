from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fitparse import FitFile


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_field(session_data: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in session_data and session_data[key] is not None:
            return session_data[key]
    return None


def _extract_session_data(fit_path: Path) -> Dict[str, Any]:
    fit_file = FitFile(str(fit_path))
    session_message = None

    for msg in fit_file.get_messages("session"):
        session_message = msg
        break

    if session_message is None:
        raise ValueError("No session record found in FIT file")

    session_data: Dict[str, Any] = {}
    for field in session_message:
        session_data[field.name] = field.value

    start_time = _get_field(session_data, ["start_time", "timestamp"])
    if isinstance(start_time, datetime):
        workout_date = start_time.date().isoformat()
    else:
        workout_date = None

    distance_m = _safe_float(_get_field(session_data, ["total_distance"]))
    distance_km = (distance_m / 1000.0) if distance_m is not None else None

    duration_sec = _safe_float(_get_field(session_data, ["total_timer_time", "total_elapsed_time"]))
    duration_min = (duration_sec / 60.0) if duration_sec is not None else None

    avg_hr = _safe_float(_get_field(session_data, ["avg_heart_rate"]))
    max_hr = _safe_float(_get_field(session_data, ["max_heart_rate"]))

    # Garmin devices can use different cadence field names depending on activity type.
    avg_cadence = _safe_float(
        _get_field(session_data, ["avg_running_cadence", "avg_cadence"])
    )

    calories = _safe_float(_get_field(session_data, ["total_calories"]))
    avg_temperature = _safe_float(_get_field(session_data, ["avg_temperature"]))

    # Pace in minutes per kilometer.
    avg_pace = None
    if distance_km and duration_min and distance_km > 0:
        avg_pace = duration_min / distance_km

    sport = _get_field(session_data, ["sport"])
    sub_sport = _get_field(session_data, ["sub_sport"])

    return {
        "workout_date": workout_date,
        "sport": str(sport) if sport is not None else None,
        "sub_sport": str(sub_sport) if sub_sport is not None else None,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "avg_hr": avg_hr,
        "max_hr": max_hr,
        "avg_cadence": avg_cadence,
        "avg_pace_min_per_km": avg_pace,
        "calories": calories,
        "avg_temperature": avg_temperature,
    }


def ingest_activity_folder(activity_dir: Path, error_log_path: Path) -> List[Dict[str, Any]]:
    if not activity_dir.exists() or not activity_dir.is_dir():
        raise FileNotFoundError(f"Activity folder not found: {activity_dir}")

    rows: List[Dict[str, Any]] = []
    fit_files = sorted(
        [p for p in activity_dir.rglob("*") if p.suffix.lower() == ".fit"]
    )

    error_log_path.parent.mkdir(parents=True, exist_ok=True)

    for fit_path in fit_files:
        try:
            extracted = _extract_session_data(fit_path)
            extracted["source_file"] = str(fit_path.resolve())
            extracted["source_mtime"] = fit_path.stat().st_mtime
            rows.append(extracted)
        except Exception as exc:  # noqa: BLE001 - keep ingest resilient for beginners
            with error_log_path.open("a", encoding="utf-8") as f:
                f.write(f"{fit_path}: {exc}\n")

    return rows
