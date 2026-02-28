from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from muthu_performance_lab.config import (
    DB_PATH,
    DEFAULT_GARMIN_CANDIDATES,
    ERROR_LOG_PATH,
)
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


st.set_page_config(page_title="Muthu Performance Lab", layout="wide")
st.title("Muthu Performance Lab")
st.caption("Local Garmin running analytics dashboard (no cloud)")


def detect_default_garmin_path() -> Path | None:
    for candidate in DEFAULT_GARMIN_CANDIDATES:
        if (candidate / "Activity").exists():
            return candidate
    return None


def pace_label(min_per_km: float) -> str:
    if pd.isna(min_per_km):
        return "N/A"
    minutes = int(min_per_km)
    seconds = int(round((min_per_km - minutes) * 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d} /km"


def run_ingestion(garmin_root: Path):
    activity_dir = garmin_root / "Activity"
    rows = ingest_activity_folder(activity_dir=activity_dir, error_log_path=ERROR_LOG_PATH)

    conn = get_connection(DB_PATH)
    try:
        count = upsert_workouts(conn, rows)
    finally:
        conn.close()

    return count, len(rows)


with st.sidebar:
    st.header("Data Source")
    detected = detect_default_garmin_path()
    default_path = str(detected) if detected else ""

    garmin_path_input = st.text_input(
        "GARMIN folder path",
        value=default_path,
        help="This folder should contain Activity/, Monitor/, Sleep/, and HRVStatus/.",
    )

    st.write("Use this button whenever you add new FIT files.")
    refresh_clicked = st.button("Refresh from FIT files", type="primary")

if not garmin_path_input.strip():
    st.warning("Please enter your GARMIN folder path in the sidebar.")
    st.stop()

try:
    garmin_root = Path(garmin_path_input).expanduser().resolve()
except Exception:  # noqa: BLE001
    st.error("The GARMIN folder path is not valid.")
    st.stop()

if refresh_clicked:
    try:
        upserted, parsed = run_ingestion(garmin_root)
        st.success(f"Refresh complete. Parsed {parsed} files and updated {upserted} rows.")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not refresh data: {exc}")

# Always try ingest once so first-time users get data without extra steps.
if DB_PATH.exists() is False:
    try:
        run_ingestion(garmin_root)
    except Exception:
        pass

conn = get_connection(DB_PATH)
try:
    all_df = load_workouts_df(conn)
finally:
    conn.close()

runs_df = filter_runs(all_df)

if runs_df.empty:
    st.info(
        "No running workouts found yet. Check your GARMIN path and click 'Refresh from FIT files'."
    )
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Runs", f"{kpi_total_runs(runs_df):,}")
col2.metric("Lifetime Distance", f"{kpi_lifetime_distance_km(runs_df):,.1f} km")
col3.metric("Weekly Mileage", f"{weekly_mileage_km(runs_df):,.1f} km")
col4.metric("7d vs 28d Load Ratio", f"{training_load_ratio(runs_df):.2f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Monthly Mileage Trend")
    monthly_df = monthly_mileage(runs_df)
    fig_monthly = px.line(monthly_df, x="month", y="distance_km", markers=True)
    fig_monthly.update_layout(xaxis_title="Month", yaxis_title="Distance (km)")
    st.plotly_chart(fig_monthly, use_container_width=True)

with right:
    st.subheader("Pace vs Heart Rate")
    scatter_df = runs_df.dropna(subset=["avg_pace_min_per_km", "avg_hr"])
    fig_scatter = px.scatter(
        scatter_df,
        x="avg_hr",
        y="avg_pace_min_per_km",
        hover_data=["workout_date", "distance_km", "duration_min"],
        labels={"avg_hr": "Average HR", "avg_pace_min_per_km": "Pace (min/km)"},
    )
    fig_scatter.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_scatter, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.subheader("Cadence Trend Over Time")
    cadence_df = runs_df.dropna(subset=["avg_cadence"])
    fig_cadence = px.line(
        cadence_df,
        x="workout_date",
        y="avg_cadence",
        markers=True,
        labels={"workout_date": "Date", "avg_cadence": "Average Cadence"},
    )
    st.plotly_chart(fig_cadence, use_container_width=True)

with right2:
    st.subheader("Distance Per Run Over Time")
    fig_distance = px.bar(
        runs_df,
        x="workout_date",
        y="distance_km",
        labels={"workout_date": "Date", "distance_km": "Distance (km)"},
    )
    st.plotly_chart(fig_distance, use_container_width=True)

st.divider()
st.subheader("Run Table")
display_df = runs_df[
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
    ]
].copy()

display_df["workout_date"] = display_df["workout_date"].dt.date

display_df["avg_pace_min_per_km"] = display_df["avg_pace_min_per_km"].apply(pace_label)

display_df.rename(
    columns={
        "workout_date": "Date",
        "distance_km": "Distance (km)",
        "duration_min": "Duration (min)",
        "avg_hr": "Avg HR",
        "max_hr": "Max HR",
        "avg_cadence": "Avg Cadence",
        "avg_pace_min_per_km": "Avg Pace",
        "hr_efficiency": "HR Efficiency (pace/HR)",
        "calories": "Calories",
        "avg_temperature": "Avg Temperature",
    },
    inplace=True,
)

st.dataframe(display_df.sort_values("Date", ascending=False), use_container_width=True)

with st.expander("Future Upgrade Ideas"):
    st.markdown(
        """
1. Sleep vs Performance:
   - Join daily sleep score and duration from `/GARMIN/Sleep/` with next-day run pace.
   - Add chart: sleep score vs next-day HR Efficiency.

2. HRV Fatigue Tracking:
   - Parse `/GARMIN/HRVStatus/` and compare HRV baseline changes with weekly training load.
   - Add readiness indicator using HRV trend + acute/chronic load ratio.
"""
    )

st.caption(f"SQLite DB: {DB_PATH}")
st.caption(f"Ingestion errors (if any): {ERROR_LOG_PATH}")
