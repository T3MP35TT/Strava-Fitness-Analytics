"""
Predictive model monitoring.

Run from the project root:

    python scripts/run_predictive_monitoring.py
    python scripts/run_predictive_monitoring.py --model calories
    python scripts/run_predictive_monitoring.py --model activity_target
    python scripts/run_predictive_monitoring.py --model sleep_target
    python scripts/run_predictive_monitoring.py --model all

The monitor evaluates the latest available next-day prediction and also
records the result in the predictive monitoring log.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "fitness_daily_master.csv"
)

MODEL_ROOT = (
    PROJECT_ROOT
    / "models"
    / "predictive_models"
)


MODEL_CONFIG = {
    "calories": {
        "directory": "calories",
        "target": "Calories",
        "target_type": "regression",
    },
    "activity_target": {
        "directory": "activity_target",
        "target": "Meets_10k_Steps",
        "target_type": "classification",
    },
    "sleep_target": {
        "directory": "sleep_target",
        "target": "Sleep_7h_Target",
        "target_type": "classification",
    },
}


# ============================================================
# Loading
# ============================================================

def load_data() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Canonical dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required = [
        "Id",
        "Date",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Canonical dataset is missing: "
            + ", ".join(missing)
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    df = (
        df.dropna(
            subset=[
                "Id",
                "Date",
            ]
        )
        .sort_values(
            [
                "Id",
                "Date",
            ]
        )
        .reset_index(drop=True)
    )

    return df


def load_artifact(model_name: str):
    config = MODEL_CONFIG[model_name]

    model_dir = (
        MODEL_ROOT
        / config["directory"]
    )

    model_path = (
        model_dir
        / "model.joblib"
    )

    metadata_path = (
        model_dir
        / "metadata.json"
    )

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Metadata not found: {metadata_path}"
        )

    model = joblib.load(
        model_path
    )

    with metadata_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(file)

    return (
        model,
        metadata,
        model_dir,
    )


# ============================================================
# Metadata helpers
# ============================================================

def get_feature_columns(
    metadata: dict,
) -> list[str]:

    candidates = [
        metadata.get(
            "feature_columns"
        ),
        metadata.get(
            "features"
        ),
        metadata.get(
            "model_config",
            {},
        ).get(
            "feature_columns"
        ),
    ]

    for features in candidates:

        if features:
            return list(features)

    raise ValueError(
        "Model metadata does not contain "
        "feature_columns."
    )


def get_model_version(
    metadata: dict,
) -> str:

    return str(
        metadata.get(
            "model_version",
            metadata.get(
                "version",
                "unknown",
            ),
        )
    )


def get_algorithm(
    metadata: dict,
) -> str:

    return str(
        metadata.get(
            "algorithm",
            "unknown",
        )
    )


# ============================================================
# Feature engineering
# ============================================================

def create_modeling_features(
    df: pd.DataFrame,
    features: list[str],
) -> pd.DataFrame:

    working = (
        df.copy()
        .sort_values(
            [
                "Id",
                "Date",
            ]
        )
        .reset_index(drop=True)
    )

    lag_prefix = "Lag1_"

    for feature in features:

        if not feature.startswith(
            lag_prefix
        ):
            continue

        source_column = feature[
            len(lag_prefix):
        ]

        if source_column in working.columns:

            working[feature] = (
                working
                .groupby("Id")[
                    source_column
                ]
                .shift(1)
            )

    if "Target_Day_Of_Week_Num" in features:

        working[
            "Target_Day_Of_Week_Num"
        ] = (
            working["Date"]
            .dt.dayofweek
            + 1
        )

    if "Target_Is_Weekend" in features:

        working[
            "Target_Is_Weekend"
        ] = (
            working["Date"]
            .dt.dayofweek
            >= 5
        ).astype(int)

    return working


# ============================================================
# Monitoring dataset
# ============================================================

def build_monitoring_dataset(
    df: pd.DataFrame,
    target: str,
    features: list[str],
) -> pd.DataFrame:

    working = create_modeling_features(
        df,
        features,
    )

    if target not in working.columns:
        raise ValueError(
            f"Target column not found: {target}"
        )

    working[target] = pd.to_numeric(
        working[target],
        errors="coerce",
    )

    working[
        "Target_Date"
    ] = (
        working
        .groupby("Id")["Date"]
        .shift(-1)
    )

    working[
        "Target_Value"
    ] = (
        working
        .groupby("Id")[target]
        .shift(-1)
    )

    working[
        "Feature_Date"
    ] = working["Date"]

    next_date = (
        working
        .groupby("Id")["Date"]
        .shift(-1)
    )

    working[
        "Date_Gap"
    ] = (
        next_date
        - working["Date"]
    ).dt.days

    working = working[
        working["Date_Gap"] == 1
    ].copy()

    missing_features = [
        feature
        for feature in features
        if feature not in working.columns
    ]

    if missing_features:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                missing_features
            )
        )

    for feature in features:

        working[feature] = pd.to_numeric(
            working[feature],
            errors="coerce",
        )

    working = working.dropna(
        subset=features
    )

    working = working.dropna(
        subset=[
            "Target_Value",
            "Target_Date",
        ]
    )

    return (
        working
        .sort_values(
            [
                "Target_Date",
                "Id",
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# Monitoring row
# ============================================================

def select_monitoring_row(
    dataset: pd.DataFrame,
    metadata: dict,
) -> pd.DataFrame:

    holdout_start = (
        metadata.get(
            "holdout_target_start"
        )
        or metadata.get(
            "holdout_start"
        )
    )

    holdout_end = (
        metadata.get(
            "holdout_target_end"
        )
        or metadata.get(
            "holdout_end"
        )
    )

    candidate = dataset.copy()

    if holdout_start:

        candidate = candidate[
            candidate["Target_Date"]
            >= pd.Timestamp(
                holdout_start
            )
        ]

    if holdout_end:

        candidate = candidate[
            candidate["Target_Date"]
            <= pd.Timestamp(
                holdout_end
            )
        ]

    if candidate.empty:
        candidate = dataset.copy()

    return (
        candidate
        .sort_values(
            [
                "Target_Date",
                "Id",
            ]
        )
        .tail(1)
        .copy()
    )


# ============================================================
# Prediction
# ============================================================

def predict(
    model,
    row: pd.DataFrame,
    features: list[str],
    target_type: str,
):

    X = row[features]

    if target_type == "classification":

        prediction = model.predict(
            X
        )[0]

        probability = None

        if hasattr(
            model,
            "predict_proba",
        ):

            probabilities = (
                model.predict_proba(X)
            )

            if (
                probabilities.ndim == 2
                and probabilities.shape[1] >= 2
            ):

                probability = float(
                    probabilities[0, 1]
                )

        return (
            int(prediction),
            probability,
        )

    prediction = float(
        model.predict(X)[0]
    )

    return (
        prediction,
        None,
    )


# ============================================================
# Evaluation
# ============================================================

def evaluate_regression(
    actual: float,
    predicted: float,
    metadata: dict,
):

    error = abs(
        actual - predicted
    )

    metrics = (
        metadata.get(
            "selected_holdout_metrics"
        )
        or metadata.get(
            "selected_metrics"
        )
        or {}
    )

    historical_mae = metrics.get(
        "MAE"
    )

    if historical_mae is None:
        return (
            "Review",
            error,
        )

    historical_mae = float(
        historical_mae
    )

    if historical_mae <= 0:
        return (
            "Review",
            error,
        )

    ratio = (
        error
        / historical_mae
    )

    if ratio <= 1.5:
        status = "Within historical error"

    elif ratio <= 2.0:
        status = "Watch"

    else:
        status = "Review"

    return (
        status,
        error,
    )


def evaluate_classification(
    actual,
    predicted,
    probability,
):

    actual = int(actual)
    predicted = int(predicted)

    status = (
        "Correct"
        if actual == predicted
        else "Review"
    )

    confidence = None

    if probability is not None:

        confidence = (
            probability
            if predicted == 1
            else 1.0 - probability
        )

    return (
        status,
        confidence,
    )


# ============================================================
# Input drift
# ============================================================

def calculate_drift(
    dataset: pd.DataFrame,
    row: pd.DataFrame,
    features: list[str],
):

    results = []

    for feature in features:

        if feature not in dataset.columns:
            continue

        values = pd.to_numeric(
            dataset[feature],
            errors="coerce",
        ).dropna()

        if len(values) < 5:
            continue

        current = float(
            row.iloc[0][feature]
        )

        mean = float(
            values.mean()
        )

        std = float(
            values.std()
        )

        if (
            std == 0
            or np.isnan(std)
        ):
            z_score = 0.0

        else:
            z_score = (
                current - mean
            ) / std

        results.append(
            {
                "feature": feature,
                "z_score": z_score,
                "abs_z_score": abs(
                    z_score
                ),
            }
        )

    if not results:

        return {
            "status": "NOT_AVAILABLE",
            "max_abs_z": np.nan,
        }

    max_abs_z = max(
        item["abs_z_score"]
        for item in results
    )

    if max_abs_z >= 5:
        status = "Input drift"

    elif max_abs_z >= 3:
        status = "Watch"

    else:
        status = (
            "Within historical range"
        )

    return {
        "status": status,
        "max_abs_z": float(
            max_abs_z
        ),
    }


# ============================================================
# Monitoring log
# ============================================================

def write_monitoring_log(
    event: dict,
):

    MODEL_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = (
        MODEL_ROOT
        / "monitoring_log.csv"
    )

    new_row = pd.DataFrame(
        [event]
    )

    if log_file.exists():

        existing = pd.read_csv(
            log_file
        )

        output = pd.concat(
            [
                existing,
                new_row,
            ],
            ignore_index=True,
        )

    else:

        output = new_row

    output.to_csv(
        log_file,
        index=False,
    )


# ============================================================
# Monitor one model
# ============================================================

def monitor_model(
    model_name: str,
    df: pd.DataFrame,
):

    config = MODEL_CONFIG[
        model_name
    ]

    model, metadata, model_dir = (
        load_artifact(
            model_name
        )
    )

    features = get_feature_columns(
        metadata
    )

    dataset = build_monitoring_dataset(
        df=df,
        target=config["target"],
        features=features,
    )

    if dataset.empty:
        raise RuntimeError(
            "No valid next-day monitoring "
            f"rows available for {model_name}."
        )

    row = select_monitoring_row(
        dataset,
        metadata,
    )

    prediction, probability = predict(
        model=model,
        row=row,
        features=features,
        target_type=config[
            "target_type"
        ],
    )

    actual = float(
        row.iloc[0]["Target_Value"]
    )

    if config["target_type"] == "regression":

        prediction_status, error = (
            evaluate_regression(
                actual,
                prediction,
                metadata,
            )
        )

    else:

        prediction_status, error = (
            evaluate_classification(
                actual,
                prediction,
                probability,
            )
        )

    drift = calculate_drift(
        dataset,
        row,
        features,
    )

    # Monitoring status is deliberately separate
    # from the dashboard prediction itself.
    #
    # A model can produce a prediction even when
    # monitoring recommends review.

    review_required = (
        prediction_status
        in [
            "Review",
            "REVIEW",
        ]
        or drift["status"]
        == "Input drift"
    )

    operational_status = (
        "REVIEW REQUIRED"
        if review_required
        else "MONITORING"
    )

    model_version = get_model_version(
        metadata
    )

    algorithm = get_algorithm(
        metadata
    )

    feature_date = row.iloc[0][
        "Feature_Date"
    ]

    target_date = row.iloc[0][
        "Target_Date"
    ]

    event = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "model_name": model_name,
        "model_version": model_version,
        "algorithm": algorithm,
        "model_path": str(
            model_dir
            / "model.joblib"
        ),
        "feature_date": feature_date.strftime(
            "%Y-%m-%d"
        ),
        "target_date": target_date.strftime(
            "%Y-%m-%d"
        ),
        "participant_id": str(
            row.iloc[0]["Id"]
        ),
        "prediction": float(
            prediction
        ),
        "actual": actual,
        "probability_positive": (
            None
            if probability is None
            else float(
                probability
            )
        ),
        "prediction_status": (
            prediction_status
        ),
        "error_or_confidence": (
            None
            if error is None
            else float(error)
        ),
        "drift_status": drift[
            "status"
        ],
        "max_abs_z": (
            None
            if np.isnan(
                drift["max_abs_z"]
            )
            else float(
                drift["max_abs_z"]
            )
        ),
        "operational_status": (
            operational_status
        ),
        "review_required": (
            review_required
        ),
    }

    write_monitoring_log(
        event
    )

    print()
    print("=" * 72)
    print(
        model_name.upper()
    )
    print("=" * 72)

    print(
        f"Model version: {model_version}"
    )

    print(
        f"Algorithm: {algorithm}"
    )

    print(
        f"Feature date: "
        f"{event['feature_date']}"
    )

    print(
        f"Target date: "
        f"{event['target_date']}"
    )

    print(
        f"Participant: "
        f"{event['participant_id']}"
    )

    if config["target_type"] == "regression":

        print(
            f"Predicted: "
            f"{event['prediction']:.2f}"
        )

        print(
            f"Actual: "
            f"{event['actual']:.2f}"
        )

    else:

        print(
            f"Predicted class: "
            f"{int(event['prediction'])}"
        )

        print(
            f"Actual class: "
            f"{int(event['actual'])}"
        )

        if probability is not None:

            print(
                f"Positive probability: "
                f"{probability:.4f}"
            )

    print(
        f"Prediction status: "
        f"{event['prediction_status']}"
    )

    print(
        f"Drift status: "
        f"{event['drift_status']}"
    )

    if event["max_abs_z"] is not None:

        print(
            f"Max drift: "
            f"{event['max_abs_z']:.2f}σ"
        )

    print(
        f"Operational status: "
        f"{event['operational_status']}"
    )

    if review_required:

        print()
        print(
            "ACTION: Model review/revalidation "
            "is required."
        )

    return event


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Monitor predictive models."
        )
    )

    parser.add_argument(
        "--model",
        choices=[
            "calories",
            "activity_target",
            "sleep_target",
            "all",
        ],
        default="all",
    )

    args = parser.parse_args()

    print(
        "Loading canonical dataset..."
    )

    df = load_data()

    print(
        f"Rows available: {len(df):,}"
    )

    if args.model == "all":

        model_names = list(
            MODEL_CONFIG.keys()
        )

    else:

        model_names = [
            args.model
        ]

    results = []

    for model_name in model_names:

        try:

            result = monitor_model(
                model_name,
                df,
            )

            results.append(
                result
            )

        except Exception as exc:

            print()
            print("=" * 72)
            print(
                f"{model_name.upper()} "
                "MONITORING FAILED"
            )
            print("=" * 72)

            print(
                f"Error: {exc}"
            )

    print()
    print("=" * 72)
    print(
        "MONITORING SUMMARY"
    )
    print("=" * 72)

    for result in results:

        print(
            f"{result['model_name']}: "
            f"{result['operational_status']} | "
            f"{result['prediction_status']} | "
            f"{result['drift_status']}"
        )

    print()
    print(
        "Monitoring log:"
    )

    print(
        MODEL_ROOT
        / "monitoring_log.csv"
    )


if __name__ == "__main__":
    main()