"""
Predictive target and feature registry for the Strava Fitness App.

The predictive system intentionally uses features that are consistently
available in the canonical fitness dataset.

Excluded because they are too sparse/inconsistently recorded:
- HeartRate_Avg
- HeartRate_Median
- Weight_Kg
- BMI
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ProblemType = Literal[
    "regression",
    "classification",
]


# ============================================================
# BASE FEATURES
# ============================================================

BASE_FEATURES = [
    "TotalSteps",
    "TotalDistance",
    "VeryActiveMinutes",
    "FairlyActiveMinutes",
    "LightlyActiveMinutes",
    "SedentaryMinutes",
    "Total_Active_Minutes",
    "Active_Minutes_Pct",
    "Very_Active_Pct",
    "METs_Avg",
    "METs_Max",
    "Hourly_Avg_Intensity",
    "Hourly_Steps_Avg",
    "Minute_Intensity_Avg",
    "Minute_Active_Step_Minutes",
    "Sleep_Minutes",
    "Time_In_Bed_Minutes",
    "Sleep_Efficiency_Pct",
    "Calories",
]


# ============================================================
# CALENDAR FEATURES
# ============================================================

CALENDAR_FEATURES = [
    "Target_Day_Of_Week_Num",
    "Target_Is_Weekend",
]


# ============================================================
# EXCLUDED FEATURES
# ============================================================

EXCLUDED_SPARSE_FEATURES = {
    "HeartRate_Avg",
    "HeartRate_Median",
    "Weight_Kg",
    "BMI",
}


# ============================================================
# LEAKAGE COLUMNS
# ============================================================

LEAKAGE_COLUMNS = {
    "Calories",
    "Hourly_Calories_Total",
    "Hourly_Calories_Avg",
    "Minute_Calories_Total",
    "Minute_Calories_Avg",
    "Meets_10k_Steps",
    "Sleep_7h_Target",
}


# ============================================================
# TARGET SPECIFICATION
# ============================================================

@dataclass(frozen=True)
class TargetSpec:

    key: str

    display_name: str

    question: str

    target: str

    target_type: ProblemType

    feature_columns: tuple[str, ...]

    forecast_horizon: str

    minimum_rows: int

    minimum_positive_class: int | None = None

    minimum_negative_class: int | None = None


# ============================================================
# MODEL FEATURES
# ============================================================

def feature_columns() -> list[str]:
    """
    Return the complete model feature list.

    Every raw feature is represented as a lag-1 feature,
    followed by target-day calendar features.
    """

    return [
        *[
            f"Lag1_{column}"
            for column in BASE_FEATURES
            if column not in EXCLUDED_SPARSE_FEATURES
        ],
        *CALENDAR_FEATURES,
    ]


MODEL_FEATURE_COLUMNS = tuple(
    feature_columns()
)


# ============================================================
# TARGET REGISTRY
# ============================================================

TARGET_REGISTRY: dict[str, TargetSpec] = {

    "calories": TargetSpec(

        key="calories",

        display_name=(
            "Next-Day Calorie Expenditure"
        ),

        question=(
            "How many calories is this participant "
            "likely to expend tomorrow?"
        ),

        target="Calories",

        target_type="regression",

        feature_columns=MODEL_FEATURE_COLUMNS,

        forecast_horizon=(
            "next participant-day"
        ),

        minimum_rows=100,

    ),

    "activity_target": TargetSpec(

        key="activity_target",

        display_name=(
            "Next-Day 10K Step Target"
        ),

        question=(
            "Is this participant likely to reach "
            "10,000 steps tomorrow?"
        ),

        target="Meets_10k_Steps",

        target_type="classification",

        feature_columns=MODEL_FEATURE_COLUMNS,

        forecast_horizon=(
            "next participant-day"
        ),

        minimum_rows=100,

        minimum_positive_class=40,

        minimum_negative_class=40,

    ),

    "sleep_target": TargetSpec(

        key="sleep_target",

        display_name=(
            "Next-Day 7-Hour Sleep Target"
        ),

        question=(
            "Is this participant likely to achieve "
            "at least 7 hours of sleep tomorrow?"
        ),

        target="Sleep_7h_Target",

        target_type="classification",

        feature_columns=MODEL_FEATURE_COLUMNS,

        forecast_horizon=(
            "next participant-day"
        ),

        minimum_rows=100,

        minimum_positive_class=30,

        minimum_negative_class=30,

    ),
}


# ============================================================
# TARGET LOOKUP
# ============================================================

def get_target_spec(
    key: str,
) -> TargetSpec:

    try:

        return TARGET_REGISTRY[key]

    except KeyError as exc:

        raise KeyError(
            f"Unknown predictive target '{key}'. "
            f"Available targets: "
            f"{', '.join(TARGET_REGISTRY)}"
        ) from exc