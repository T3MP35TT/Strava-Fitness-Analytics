"""
Generate participant-level next-day predictions from persisted model artifacts.

Run from the project root:

    python scripts/run_predictive_predictions.py

The script:
- runs the predictive data-quality gate first
- reads the canonical fitness master dataset
- loads the persisted Calories, 10K Steps, and 7-Hour Sleep models
- selects each participant's latest usable observation
- builds the same forecast input structure used by the Predictive Insights page
- generates one prediction record per participant
- writes the prediction store to data/processed/predictions.csv

Routine predictions are blocked when the data-quality gate fails.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data import load_data
from utils.data_quality import (
    enforce_quality_gate,
    run_quality_gate,
)
from utils.predictive_registry import (
    TARGET_REGISTRY,
    feature_columns,
)


MODEL_ROOT = (
    PROJECT_ROOT
    / "models"
    / "predictive_models"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "predictions.csv"
)

MODEL_KEYS = tuple(
    TARGET_REGISTRY.keys()
)

MODEL_FILES = {
    key: {
        "model": (
            MODEL_ROOT
            / key
            / "model.joblib"
        ),
        "metadata": (
            MODEL_ROOT
            / key
            / "metadata.json"
        ),
    }
    for key in MODEL_KEYS
}


def load_model_bundle(
    key: str,
) -> dict:
    paths = MODEL_FILES[key]

    if not paths["model"].exists():
        raise FileNotFoundError(
            f"Model artifact not found for {key}: "
            f"{paths['model']}"
        )

    if not paths["metadata"].exists():
        raise FileNotFoundError(
            f"Model metadata not found for {key}: "
            f"{paths['metadata']}"
        )

    model = joblib.load(
        paths["model"]
    )

    metadata = json.loads(
        paths["metadata"].read_text(
            encoding="utf-8"
        )
    )

    return {
        "model": model,
        "metadata": metadata,
    }


def load_all_bundles() -> dict[str, dict]:
    return {
        key: load_model_bundle(
            key
        )
        for key in MODEL_KEYS
    }


def validate_source(
    df: pd.DataFrame,
) -> pd.DataFrame:

    output = df.copy()

    if "Id" not in output.columns:
        raise ValueError(
            "Canonical dataset is missing Id."
        )

    if "Date" not in output.columns:
        raise ValueError(
            "Canonical dataset is missing Date."
        )

    output["Date"] = pd.to_datetime(
        output["Date"],
        errors="coerce",
    )

    output["Id"] = (
        output["Id"].astype("string")
    )

    output = output.dropna(
        subset=[
            "Id",
            "Date",
        ]
    ).copy()

    if output.empty:
        raise ValueError(
            "Canonical dataset contains no usable Id/Date rows."
        )

    return (
        output
        .sort_values(
            ["Id", "Date"]
        )
        .reset_index(drop=True)
    )


def is_meaningful_observation(
    row: pd.Series,
) -> bool:

    signal_columns = [
        "TotalSteps",
        "Calories",
        "Total_Active_Minutes",
        "Sleep_Minutes",
    ]

    values = []

    for column in signal_columns:
        if column not in row.index:
            continue

        value = pd.to_numeric(
            pd.Series(
                [row[column]]
            ),
            errors="coerce",
        ).iloc[0]

        if pd.notna(value):
            values.append(
                float(value)
            )

    if not values:
        return False

    return any(
        value > 0
        for value in values
    )


def latest_usable_observation(
    participant_df: pd.DataFrame,
) -> pd.Series | None:

    ordered = (
        participant_df
        .sort_values("Date")
        .copy()
    )

    for _, row in ordered.iloc[::-1].iterrows():
        if is_meaningful_observation(row):
            return row

    return None


def feature_columns_for(
    bundle: dict,
) -> list[str]:

    metadata = bundle["metadata"]

    configured = metadata.get(
        "feature_columns"
    )

    if not configured:
        configured = metadata.get(
            "features"
        )

    if not configured:
        configured = feature_columns()

    return list(
        configured
    )


def build_forecast_row(
    latest_row: pd.Series,
    target_date: pd.Timestamp,
    model_features: list[str],
) -> pd.DataFrame:

    row: dict[str, float] = {}

    for feature in model_features:

        if feature.startswith(
            "Lag1_"
        ):
            source_column = (
                feature[len("Lag1_"):]
            )

            value = pd.to_numeric(
                pd.Series(
                    [latest_row.get(source_column)]
                ),
                errors="coerce",
            ).iloc[0]

            row[feature] = value

        elif feature == "Target_Day_Of_Week_Num":

            row[feature] = float(
                pd.Timestamp(
                    target_date
                ).dayofweek
            )

        elif feature == "Target_Is_Weekend":

            row[feature] = float(
                pd.Timestamp(
                    target_date
                ).dayofweek >= 5
            )

        else:

            value = pd.to_numeric(
                pd.Series(
                    [latest_row.get(feature)]
                ),
                errors="coerce",
            ).iloc[0]

            row[feature] = value

    return pd.DataFrame(
        [row],
        columns=model_features,
    )


def get_prediction(
    bundle: dict,
    feature_row: pd.DataFrame,
) -> tuple[float, float | None]:

    model = bundle["model"]

    prediction = model.predict(
        feature_row
    )[0]

    probability = None

    if hasattr(
        model,
        "predict_proba",
    ):

        probabilities = model.predict_proba(
            feature_row
        )[0]

        classes = getattr(
            model,
            "classes_",
            None,
        )

        if classes is not None:
            classes_list = list(
                classes
            )

            if 1 in classes_list:
                positive_index = (
                    classes_list.index(1)
                )

                probability = float(
                    probabilities[
                        positive_index
                    ]
                )
        elif len(probabilities) == 2:
            probability = float(
                probabilities[1]
            )

    return (
        float(prediction),
        probability,
    )


def generate_predictions(
    df: pd.DataFrame,
    bundles: dict[str, dict],
) -> pd.DataFrame:

    participants = sorted(
        df["Id"]
        .dropna()
        .unique()
        .tolist(),
        key=str,
    )

    rows: list[dict] = []

    prediction_timestamp = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    all_model_features = {
        key: feature_columns_for(bundle)
        for key, bundle in bundles.items()
    }

    for participant_id in participants:

        participant_df = df[
            df["Id"] == participant_id
        ].copy()

        latest = latest_usable_observation(
            participant_df
        )

        if latest is None:
            continue

        feature_date = pd.Timestamp(
            latest["Date"]
        )

        target_date = (
            feature_date
            + pd.Timedelta(days=1)
        )

        record = {
            "Id": participant_id,
            "Feature_Date": (
                feature_date.strftime(
                    "%Y-%m-%d"
                )
            ),
            "Target_Date": (
                target_date.strftime(
                    "%Y-%m-%d"
                )
            ),
            "Prediction_Timestamp": (
                prediction_timestamp
            ),
        }

        for key, bundle in bundles.items():

            model_features = (
                all_model_features[key]
            )

            feature_row = (
                build_forecast_row(
                    latest_row=latest,
                    target_date=target_date,
                    model_features=model_features,
                )
            )

            prediction, probability = (
                get_prediction(
                    bundle=bundle,
                    feature_row=feature_row,
                )
            )

            record[
                f"{key}_Prediction"
            ] = prediction

            if key == "activity_target":
                record[
                    "Steps_Positive_Probability"
                ] = probability

            if key == "sleep_target":
                record[
                    "Sleep_Positive_Probability"
                ] = probability

            version_column = (
                {
                    "calories":
                        "Model_Version_Calories",
                    "activity_target":
                        "Model_Version_ActivityTarget",
                    "sleep_target":
                        "Model_Version_SleepTarget",
                }
                [key]
            )

            record[
                version_column
            ] = bundle[
                "metadata"
            ].get(
                "model_version"
            )

        rows.append(
            record
        )

    if not rows:
        raise RuntimeError(
            "No participant predictions could be generated."
        )

    output = pd.DataFrame(
        rows
    )

    preferred_columns = [
        "Id",
        "Feature_Date",
        "Target_Date",
        "calories_Prediction",
        "activity_target_Prediction",
        "Steps_Positive_Probability",
        "sleep_target_Prediction",
        "Sleep_Positive_Probability",
        "Model_Version_Calories",
        "Model_Version_ActivityTarget",
        "Model_Version_SleepTarget",
        "Prediction_Timestamp",
    ]

    ordered_columns = [
        column
        for column in preferred_columns
        if column in output.columns
    ]

    remaining_columns = [
        column
        for column in output.columns
        if column not in ordered_columns
    ]

    return (
        output[
            ordered_columns
            + remaining_columns
        ]
        .sort_values(
            ["Target_Date", "Id"]
        )
        .reset_index(drop=True)
    )


def save_prediction_store(
    predictions: pd.DataFrame,
) -> None:

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = (
        OUTPUT_PATH.with_suffix(
            ".tmp"
        )
    )

    predictions.to_csv(
        temp_path,
        index=False,
    )

    temp_path.replace(
        OUTPUT_PATH
    )


def main() -> None:

    print(
        "Running predictive data-quality gate..."
    )

    quality_report = run_quality_gate(
        project_root=PROJECT_ROOT
    )

    enforce_quality_gate(
        quality_report
    )

    print(
        f"Quality gate: "
        f"{quality_report['overall_status']}"
    )

    if quality_report["overall_status"] == "WARN":
        print(
            "Quality gate passed with warnings. "
            "Routine prediction generation will continue."
        )

    print()
    print(
        "Loading canonical dataset..."
    )

    df = load_data()

    print(
        f"Rows available: {len(df):,}"
    )

    print(
        f"Participants available: "
        f"{df['Id'].nunique():,}"
    )

    print()
    print(
        "Loading persisted model artifacts..."
    )

    bundles = load_all_bundles()

    for key, bundle in bundles.items():
        metadata = bundle["metadata"]

        print(
            f"  {key}: "
            f"{metadata.get('algorithm', '—')} "
            f"| "
            f"{metadata.get('model_version', '—')}"
        )

    print()
    print(
        "Validating prediction inputs..."
    )

    df = validate_source(
        df
    )

    print(
        "Prediction inputs validated."
    )

    print()
    print(
        "Generating participant-level predictions..."
    )

    predictions = generate_predictions(
        df,
        bundles,
    )

    save_prediction_store(
        predictions
    )

    print()
    print("=" * 72)
    print(
        "PREDICTION STORE CREATED"
    )
    print("=" * 72)

    print(
        f"Prediction records: "
        f"{len(predictions):,}"
    )

    print(
        f"Participants predicted: "
        f"{predictions['Id'].nunique():,}"
    )

    print(
        f"Feature dates: "
        f"{predictions['Feature_Date'].min()} "
        f"→ "
        f"{predictions['Feature_Date'].max()}"
    )

    print(
        f"Target dates: "
        f"{predictions['Target_Date'].min()} "
        f"→ "
        f"{predictions['Target_Date'].max()}"
    )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )

    print()
    print(
        "Prediction generation completed successfully."
    )


if __name__ == "__main__":
    main()
