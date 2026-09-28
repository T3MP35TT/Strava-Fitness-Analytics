import pandas as pd

from utils.predictive_model import build_forecasting_table
from utils.predictive_registry import feature_columns


def make_sample_data(days=20, participants=15):
    dates = pd.date_range("2025-01-01", periods=days, freq="D")
    rows = []

    for participant in range(participants):
        for i, date in enumerate(dates):
            rows.append(
                {
                    "Id": participant + 1,
                    "Date": date,
                    "TotalSteps": 7000 + participant * 100 + i * 20,
                    "TotalDistance": 4.0 + i * 0.1,
                    "VeryActiveMinutes": 20 + participant,
                    "FairlyActiveMinutes": 30,
                    "LightlyActiveMinutes": 120,
                    "SedentaryMinutes": 700,
                    "Total_Active_Minutes": 170 + participant,
                    "Active_Minutes_Pct": 20.0,
                    "Very_Active_Pct": 2.0,
                    "METs_Avg": 1.8,
                    "METs_Max": 8.0,
                    "Hourly_Avg_Intensity": 4.0,
                    "Hourly_Steps_Avg": 300,
                    "Minute_Intensity_Avg": 2.0,
                    "Minute_Active_Step_Minutes": 150,
                    "HeartRate_Avg": 75,
                    "HeartRate_Median": 74,
                    "Sleep_Minutes": 420 + (participant % 3) * 10,
                    "Time_In_Bed_Minutes": 450,
                    "Sleep_Efficiency_Pct": 93,
                    "Weight_Kg": 70,
                    "BMI": 23,
                    "Calories": 1900 + participant * 10 + i * 4,
                    "Meets_10k_Steps": (7000 + participant * 100 + i * 20) >= 10000,
                    "Sleep_7h_Target": True,
                }
            )

    return pd.DataFrame(rows)


def test_forecasting_table_uses_next_day_targets():
    table = build_forecasting_table(make_sample_data())

    assert not table.empty
    assert "Target_Calories" in table.columns
    assert "Target_Meets_10k_Steps" in table.columns
    assert "Target_Sleep_7h_Target" in table.columns
    assert "Target_Date" in table.columns


def test_feature_registry_contains_only_lagged_measurements_and_calendar():
    features = feature_columns()

    assert all(
        feature.startswith("Lag1_") or feature.startswith("Target_")
        for feature in features
    )

    assert "Lag1_Calories" in features
    assert "Calories" not in features
    assert "Meets_10k_Steps" not in features
    assert "Sleep_7h_Target" not in features
