
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "fitness_daily_master.csv"
)
DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "fitness_analytics.db"
)


NUMERIC_COLUMNS = [
    "TotalSteps",
    "TotalDistance",
    "TrackerDistance",
    "Calories",
    "VeryActiveMinutes",
    "FairlyActiveMinutes",
    "LightlyActiveMinutes",
    "SedentaryMinutes",
    "Total_Active_Minutes",
    "Sleep_Minutes",
    "Time_In_Bed_Minutes",
    "Sleep_Efficiency_Pct",
    "HeartRate_Avg",
    "HeartRate_Min",
    "HeartRate_Max",
    "HeartRate_Median",
    "BMI",
    "Weight_Kg",
]


@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH
    )

    if "Date" not in df.columns:
        raise ValueError(
            "Dataset must contain a Date column."
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    if "Total_Active_Minutes" not in df.columns:
        active = [
            c
            for c in [
                "VeryActiveMinutes",
                "FairlyActiveMinutes",
                "LightlyActiveMinutes",
            ]
            if c in df.columns
        ]

        if active:
            df["Total_Active_Minutes"] = (
                df[active]
                .fillna(0)
                .sum(axis=1)
            )

    if "Day_Of_Week" not in df.columns:
        df["Day_Of_Week"] = (
            df["Date"].dt.day_name()
        )

    if "Is_Weekend" not in df.columns:
        df["Is_Weekend"] = (
            df["Date"].dt.dayofweek >= 5
        )

    # Binary targets must remain unknown when the source
    # measurement needed to define them is missing.
    if (
        "Meets_10k_Steps" not in df.columns
        and "TotalSteps" in df.columns
    ):
        steps = pd.to_numeric(
            df["TotalSteps"],
            errors="coerce",
        )

        df["Meets_10k_Steps"] = (
            (steps >= 10000)
            .where(steps.notna())
        )

    if (
        "Sleep_7h_Target" not in df.columns
        and "Sleep_Minutes" in df.columns
    ):
        sleep = pd.to_numeric(
            df["Sleep_Minutes"],
            errors="coerce",
        )

        df["Sleep_7h_Target"] = (
            (sleep >= 420)
            .where(sleep.notna())
        )

    return (
        df
        .sort_values(
            ["Date", "Id"]
        )
        .reset_index(drop=True)
    )


def apply_filters(
    df,
    start_date,
    end_date,
    participants=None,
    day_types=None,
):
    out = df[
        (df["Date"].dt.date >= start_date)
        & (df["Date"].dt.date <= end_date)
    ].copy()

    if participants:
        out = out[
            out["Id"].isin(
                participants
            )
        ]

    if day_types and len(day_types) < 2:
        want_weekend = (
            "Weekend" in day_types
        )

        out = out[
            out["Is_Weekend"]
            == want_weekend
        ]

    return out


def activity_groups(
    df,
):
    work = df.dropna(
        subset=[
            "TotalSteps",
            "Calories",
        ]
    ).copy()

    if work.empty:
        return work

    work["Activity_Level"] = pd.qcut(
        work["TotalSteps"],
        q=3,
        labels=[
            "Low Activity",
            "Moderate Activity",
            "High Activity",
        ],
        duplicates="drop",
    )

    return work


def ensure_database(
    df,
):
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(
        DB_PATH
    ) as conn:

        df.to_sql(
            "fitness_daily",
            conn,
            if_exists="replace",
            index=False,
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS "
            "idx_fitness_date "
            "ON fitness_daily(Date)"
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS "
            "idx_fitness_id "
            "ON fitness_daily(Id)"
        )

        conn.commit()

    return DB_PATH


def fmt(
    value,
    decimals=0,
):
    if pd.isna(value):
        return "—"

    return f"{value:,.{decimals}f}"
