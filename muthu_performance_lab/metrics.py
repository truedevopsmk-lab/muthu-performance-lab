from __future__ import annotations

from datetime import date, timedelta

import pandas as pd


RUN_SPORTS = {"running"}


def load_workouts_df(conn) -> pd.DataFrame:
    query = "SELECT * FROM workouts ORDER BY workout_date"
    df = pd.read_sql_query(query, conn)

    if df.empty:
        return df

    df["workout_date"] = pd.to_datetime(df["workout_date"], errors="coerce")
    df["is_run"] = df["sport"].str.lower().isin(RUN_SPORTS)

    # HR Efficiency Score requested: pace ÷ avg_hr.
    df["hr_efficiency"] = df["avg_pace_min_per_km"] / df["avg_hr"]

    return df


def filter_runs(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    runs = df[df["is_run"]].copy()
    runs = runs.dropna(subset=["workout_date"])  # Keep charts stable.
    return runs


def kpi_total_runs(runs_df: pd.DataFrame) -> int:
    return int(len(runs_df))


def kpi_lifetime_distance_km(runs_df: pd.DataFrame) -> float:
    return float(runs_df["distance_km"].fillna(0).sum())


def monthly_mileage(runs_df: pd.DataFrame) -> pd.DataFrame:
    if runs_df.empty:
        return pd.DataFrame(columns=["month", "distance_km"])

    monthly = (
        runs_df.assign(month=runs_df["workout_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["distance_km"]
        .sum()
    )
    return monthly


def weekly_mileage_km(runs_df: pd.DataFrame) -> float:
    if runs_df.empty:
        return 0.0

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_start_ts = pd.Timestamp(week_start)

    week_df = runs_df[runs_df["workout_date"] >= week_start_ts]
    return float(week_df["distance_km"].fillna(0).sum())


def training_load_ratio(runs_df: pd.DataFrame) -> float:
    """
    Acute:Chronic ratio (distance-based)
    = load in last 7 days / (load in last 28 days / 4).
    """
    if runs_df.empty:
        return 0.0

    latest_date = runs_df["workout_date"].max()
    if pd.isna(latest_date):
        return 0.0

    d7_start = latest_date - pd.Timedelta(days=7)
    d28_start = latest_date - pd.Timedelta(days=28)

    load_7 = runs_df[runs_df["workout_date"] > d7_start]["distance_km"].fillna(0).sum()
    load_28 = runs_df[runs_df["workout_date"] > d28_start]["distance_km"].fillna(0).sum()

    if load_28 <= 0:
        return 0.0

    chronic_weekly_avg = load_28 / 4.0
    if chronic_weekly_avg <= 0:
        return 0.0

    return float(load_7 / chronic_weekly_avg)
