"""
Multi-target predictive modeling utilities.

The module provides:
- participant-level next-day forecasting
- regression and classification targets
- leakage-safe lagged features
- chronological holdout validation
- rolling time validation
- participant holdout validation
- walk-forward backtesting
- model selection
- artifact persistence

The predictive outputs are analytical forecasts, not causal or medical claims.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from utils.predictive_registry import (
    BASE_FEATURES,
    TARGET_REGISTRY,
    CALENDAR_FEATURES,
    TargetSpec,
    feature_columns,
)

try:
    from utils.predictive_registry import LEAKAGE_COLUMNS
except ImportError:
    LEAKAGE_COLUMNS = {
        "Calories",
        "Hourly_Calories_Total",
        "Hourly_Calories_Avg",
        "Minute_Calories_Total",
        "Minute_Calories_Avg",
        "Meets_10k_Steps",
        "Sleep_7h_Target",
    }


RANDOM_STATE = 42
HOLDOUT_FRACTION = 0.20
MAX_WALK_FORWARD_ROWS = 100
MIN_WALK_FORWARD_TRAIN = 50
ROLLING_FOLDS = 5


# ============================================================
# General helpers
# ============================================================


def _get(spec: Any, name: str, default=None):
    if isinstance(spec, dict):
        return spec.get(name, default)
    return getattr(spec, name, default)


def _target_type(spec: Any) -> str:
    value = _get(spec, "target_type")
    if value is None:
        value = _get(spec, "problem_type")
    if value is None:
        value = _get(spec, "type", "regression")
    value = str(value).strip().lower()
    if value not in {"regression", "classification"}:
        raise ValueError(f"Unsupported target type: {value}")
    return value


def _as_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype("boolean")

    normalized = (
        series.astype("string")
        .str.strip()
        .str.lower()
    )

    return normalized.map(
        {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "yes": True,
            "no": False,
        }
    ).astype("boolean")


def _normalise_source(df: pd.DataFrame) -> pd.DataFrame:
    required = {"Id", "Date"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(
            "Master dataset is missing required columns: "
            + ", ".join(missing)
        )

    work = df.copy()
    work["Date"] = pd.to_datetime(work["Date"], errors="coerce")
    work["Id"] = work["Id"].astype("string")

    for column in BASE_FEATURES:
        if column in work.columns:
            work[column] = _as_numeric(work[column])

    for column in ["Calories", "TotalSteps", "Sleep_Minutes"]:
        if column in work.columns:
            work[column] = _as_numeric(work[column])

    for column in ["Meets_10k_Steps", "Sleep_7h_Target"]:
        if column in work.columns:
            work[column] = _as_bool(work[column])

    work = (
        work
        .dropna(subset=["Id", "Date"])
        .sort_values(["Id", "Date"])
        .reset_index(drop=True)
    )

    if work.empty:
        raise ValueError("The dataset contains no valid Id/Date rows.")

    return work


def _prepare_features_for_model(
    train: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert model inputs to numeric and impute using training statistics only.

    A deterministic zero fallback is used only when a configured feature is
    entirely missing in the training partition. This prevents an all-null
    feature from causing a model candidate to fail.
    """
    X_train = train.reindex(columns=features).copy()
    X_test = test.reindex(columns=features).copy()

    for column in features:
        X_train[column] = pd.to_numeric(X_train[column], errors="coerce")
        X_test[column] = pd.to_numeric(X_test[column], errors="coerce")

    medians = X_train.median(numeric_only=True)

    for column in features:
        median = medians.get(column, np.nan)
        if pd.isna(median):
            median = 0.0
        X_train[column] = X_train[column].fillna(float(median))
        X_test[column] = X_test[column].fillna(float(median))

    return X_train.astype(float), X_test.astype(float)


def _build_pipeline(model: Any, scale: bool = False) -> Pipeline:
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", model))
    return Pipeline(steps)


# ============================================================
# Feature engineering
# ============================================================


def create_modeling_features(
    df: pd.DataFrame,
    features: list[str],
) -> pd.DataFrame:
    """
    Create features available at the end of the current feature day.

    The target is the following day, so the current-day source measurement is
    a one-day lag relative to the target date. Therefore Lag1_* is intentionally
    aligned to the current participant-day rather than shifted an additional day.

    Calendar features describe the target day.
    """
    working = _normalise_source(df)

    grouped = working.groupby("Id", sort=False)

    for feature in features:
        if not feature.startswith("Lag1_"):
            continue

        source_column = feature[len("Lag1_"):]

        if source_column in working.columns:
            # Current feature-day value = lag-1 relative to target day.
            working[feature] = grouped[source_column].shift(0)
        else:
            working[feature] = np.nan

    # These are calculated later against Target_Date in the next-day table.
    # Keep placeholders here so the feature frame always has the full schema.
    if "Target_Day_Of_Week_Num" in features:
        working["Target_Day_Of_Week_Num"] = np.nan

    if "Target_Is_Weekend" in features:
        working["Target_Is_Weekend"] = np.nan

    return working


def build_next_day_dataset(
    df: pd.DataFrame,
    target: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    """
    Build participant-level next-day observations.

    One row means:
        Feature_Date = observed day t
        Target_Date  = observed day t+1
        Features      = values available on day t
        Target_Value  = target observed on day t+1
    """
    working = create_modeling_features(df, feature_columns)

    if target not in working.columns:
        raise ValueError(f"Target column not found: {target}")

    grouped = working.groupby("Id", sort=False)

    working["Feature_Date"] = working["Date"]
    working["Target_Date"] = grouped["Date"].shift(-1)
    working["Date_Gap"] = (
        working["Target_Date"] - working["Feature_Date"]
    ).dt.days
    working["Target_Value"] = grouped[target].shift(-1)

    # Only true next-calendar-day observations qualify.
    working = working[working["Date_Gap"] == 1].copy()

    if working.empty:
        return working.reset_index(drop=True)

    # Calendar values describe the target date.
    if "Target_Day_Of_Week_Num" in feature_columns:
        working["Target_Day_Of_Week_Num"] = (
            working["Target_Date"].dt.dayofweek + 1
        ).astype(float)

    if "Target_Is_Weekend" in feature_columns:
        working["Target_Is_Weekend"] = (
            working["Target_Date"].dt.dayofweek >= 5
        ).astype(float)

    # Force every model feature to numeric.
    for feature in feature_columns:
        if feature not in working.columns:
            working[feature] = np.nan
        working[feature] = pd.to_numeric(
            working[feature],
            errors="coerce",
        )

    # Classification flags are explicitly represented as 0/1 integers.
    if target in {"Meets_10k_Steps", "Sleep_7h_Target"}:
        raw_target = _as_bool(working["Target_Value"])
        numeric_target = raw_target.map(
            {True: 1, False: 0}
        )
        numeric_target = pd.to_numeric(
            numeric_target,
            errors="coerce",
        )
        working["Target_Value"] = numeric_target
    else:
        working["Target_Value"] = pd.to_numeric(
            working["Target_Value"],
            errors="coerce",
        )

    # Target rows must exist; feature missingness is handled during fitting.
    working = working.dropna(subset=["Target_Value"]).copy()

    return (
        working
        .sort_values(["Target_Date", "Id"])
        .reset_index(drop=True)
    )


def build_modeling_table(
    df: pd.DataFrame,
    target: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Backward-compatible alias for build_next_day_dataset."""
    return build_next_day_dataset(
        df=df,
        target=target,
        feature_columns=feature_columns,
    )


# ============================================================
# Backward-compatible forecasting table
# ============================================================


def build_forecasting_table(
    df: pd.DataFrame,
    target: str | None = None,
    feature_columns: list[str] | None = None,
    features: list[str] | None = None,
) -> pd.DataFrame:
    """
    Build a participant-level next-day table with standard target columns.

    This retains the names used by the project's tests and dashboard code.
    """
    work = _normalise_source(df)

    if feature_columns is None:
        feature_columns = features

    if feature_columns is None:
        excluded = {
            "Date",
            "Target_Calories",
            "Target_Steps",
            "Target_Meets_10k_Steps",
            "Target_Sleep_7h",
            "Target_Sleep_7h_Target",
            "Target_Value",
            "Feature_Date",
            "Target_Date",
            "Date_Gap",
            "Id",
        }
        feature_columns = [
            c for c in work.columns
            if c not in excluded
        ]

    grouped = work.groupby("Id", sort=False)
    work["Feature_Date"] = work["Date"]
    work["Target_Date"] = grouped["Date"].shift(-1)
    work["Date_Gap"] = (
        work["Target_Date"] - work["Feature_Date"]
    ).dt.days

    work = work[work["Date_Gap"] == 1].copy()

    if work.empty:
        return work.reset_index(drop=True)

    grouped = work.groupby("Id", sort=False)

    if "Calories" in work.columns:
        work["Target_Calories"] = grouped["Calories"].shift(-1)

    if "TotalSteps" in work.columns:
        work["Target_Steps"] = grouped["TotalSteps"].shift(-1)

    if "Meets_10k_Steps" in work.columns:
        work["Target_Meets_10k_Steps"] = (
            grouped["Meets_10k_Steps"]
            .shift(-1)
            .map({True: 1, False: 0})
        )

    if "Sleep_7h_Target" in work.columns:
        work["Target_Sleep_7h_Target"] = (
            grouped["Sleep_7h_Target"]
            .shift(-1)
            .map({True: 1, False: 0})
        )
        work["Target_Sleep_7h"] = work["Target_Sleep_7h_Target"]

    if target is not None:
        if target not in work.columns and target not in df.columns:
            raise ValueError(f"Target column not found: {target}")

        original = _normalise_source(df)
        original["Target_Value"] = (
            original
            .groupby("Id", sort=False)[target]
            .shift(-1)
        )
        original["Feature_Date"] = original["Date"]
        original["Target_Date"] = (
            original
            .groupby("Id", sort=False)["Date"]
            .shift(-1)
        )
        original["Date_Gap"] = (
            original["Target_Date"] - original["Feature_Date"]
        ).dt.days

        target_values = original[
            ["Id", "Feature_Date", "Target_Date", "Date_Gap", "Target_Value"]
        ]

        work = work.drop(columns=["Target_Value"], errors="ignore")
        work = work.merge(
            target_values,
            on=["Id", "Feature_Date", "Target_Date", "Date_Gap"],
            how="left",
        )

        if target in {"Meets_10k_Steps", "Sleep_7h_Target"}:
            work["Target_Value"] = (
                _as_bool(work["Target_Value"])
                .map({True: 1, False: 0})
            )
        else:
            work["Target_Value"] = pd.to_numeric(
                work["Target_Value"],
                errors="coerce",
            )
    elif "Target_Calories" in work.columns:
        work["Target_Value"] = pd.to_numeric(
            work["Target_Calories"],
            errors="coerce",
        )

    for column in feature_columns:
        if column in work.columns:
            work[column] = pd.to_numeric(
                work[column],
                errors="coerce",
            )

    return work.reset_index(drop=True)


# ============================================================
# Model candidates
# ============================================================


def _regression_candidates() -> dict[str, Pipeline]:
    return {
        "Linear Regression": _build_pipeline(
            LinearRegression(),
            scale=True,
        ),
        "Random Forest": _build_pipeline(
            RandomForestRegressor(
                n_estimators=150,
                max_depth=10,
                min_samples_leaf=3,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )
        ),
    }


def _classification_candidates() -> dict[str, Pipeline]:
    return {
        "Logistic Regression": _build_pipeline(
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
            scale=True,
        ),
        "Random Forest": _build_pipeline(
            RandomForestClassifier(
                n_estimators=150,
                max_depth=10,
                min_samples_leaf=3,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )
        ),
    }


def _make_single_model(
    algorithm: str,
    target_type: str,
) -> Pipeline:
    if target_type == "regression":
        if algorithm == "Linear Regression":
            return _build_pipeline(LinearRegression(), scale=True)
        return _build_pipeline(
            RandomForestRegressor(
                n_estimators=75,
                max_depth=10,
                min_samples_leaf=3,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )
        )

    if algorithm == "Logistic Regression":
        return _build_pipeline(
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
            scale=True,
        )

    return _build_pipeline(
        RandomForestClassifier(
            n_estimators=75,
            max_depth=10,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
    )


# ============================================================
# Metrics
# ============================================================


def _regression_metrics(
    y_true: pd.Series,
    prediction: np.ndarray,
) -> dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(y_true, prediction)),
        "RMSE": float(
            np.sqrt(mean_squared_error(y_true, prediction))
        ),
        "R2": float(r2_score(y_true, prediction)),
    }


def _classification_metrics(
    y_true: pd.Series,
    prediction: np.ndarray,
    probability: np.ndarray | None = None,
) -> dict[str, float]:
    result = {
        "Accuracy": float(accuracy_score(y_true, prediction)),
        "Precision": float(
            precision_score(y_true, prediction, zero_division=0)
        ),
        "Recall": float(
            recall_score(y_true, prediction, zero_division=0)
        ),
        "F1": float(
            f1_score(y_true, prediction, zero_division=0)
        ),
    }

    if (
        probability is not None
        and pd.Series(y_true).nunique(dropna=True) == 2
    ):
        try:
            result["ROC_AUC"] = float(
                roc_auc_score(y_true, probability)
            )
        except ValueError:
            result["ROC_AUC"] = float("nan")

    return result


def _evaluate_model(
    model: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
    target_type: str,
) -> tuple[dict[str, float], np.ndarray, np.ndarray | None]:
    prediction = model.predict(X)

    if target_type == "regression":
        return (
            _regression_metrics(y, prediction),
            prediction,
            None,
        )

    probability = None
    if hasattr(model, "predict_proba"):
        probability = model.predict_proba(X)[:, 1]

    return (
        _classification_metrics(
            y,
            prediction,
            probability,
        ),
        prediction,
        probability,
    )


# ============================================================
# Splits
# ============================================================


def chronological_split(
    data: pd.DataFrame,
    holdout_fraction: float = HOLDOUT_FRACTION,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if data.empty:
        raise ValueError("No forecasting rows available.")

    work = (
        data
        .sort_values(["Target_Date", "Id"])
        .reset_index(drop=True)
    )

    unique_dates = pd.to_datetime(
        work["Target_Date"],
        errors="coerce",
    ).dt.normalize().dropna().unique()
    unique_dates = np.sort(unique_dates)

    if len(unique_dates) < 5:
        raise ValueError(
            f"Only {len(unique_dates)} target dates are available; "
            "at least 5 are required."
        )

    holdout_dates = max(
        1,
        int(np.ceil(len(unique_dates) * holdout_fraction)),
    )
    split_index = len(unique_dates) - holdout_dates
    cutoff = unique_dates[split_index]

    train = work[
        pd.to_datetime(work["Target_Date"]).dt.normalize() < cutoff
    ].copy()
    holdout = work[
        pd.to_datetime(work["Target_Date"]).dt.normalize() >= cutoff
    ].copy()

    return train.reset_index(drop=True), holdout.reset_index(drop=True)


def _rolling_splits(data: pd.DataFrame, folds: int = ROLLING_FOLDS):
    dates = np.sort(
        pd.to_datetime(data["Target_Date"], errors="coerce")
        .dt.normalize()
        .dropna()
        .unique()
    )

    if len(dates) < 8:
        return []

    folds = min(folds, len(dates) - 1)
    initial_dates = max(4, len(dates) // (folds + 1))
    splits = []

    for fold in range(folds):
        train_end = initial_dates + fold * max(
            1,
            (len(dates) - initial_dates) // (folds + 1),
        )
        train_end = min(train_end, len(dates) - 1)
        test_end = min(
            train_end + max(1, (len(dates) - initial_dates) // (folds + 1)),
            len(dates),
        )

        train_dates = set(dates[:train_end])
        test_dates = set(dates[train_end:test_end])

        if not train_dates or not test_dates:
            continue

        train_mask = pd.to_datetime(data["Target_Date"]).dt.normalize().isin(
            train_dates
        )
        test_mask = pd.to_datetime(data["Target_Date"]).dt.normalize().isin(
            test_dates
        )

        train_idx = data.index[train_mask].to_numpy()
        test_idx = data.index[test_mask].to_numpy()

        if len(train_idx) > 0 and len(test_idx) > 0:
            splits.append((fold + 1, train_idx, test_idx))

    return splits


# ============================================================
# Validation evidence
# ============================================================


def rolling_time_validation(
    data: pd.DataFrame,
    feature_columns: list[str],
    target_type: str,
    algorithms: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []

    for fold, train_idx, test_idx in _rolling_splits(data):
        train = data.loc[train_idx].copy()
        test = data.loc[test_idx].copy()

        for algorithm in algorithms:
            if target_type == "regression":
                y_train = pd.to_numeric(
                    train["Target_Value"], errors="coerce"
                )
                y_test = pd.to_numeric(
                    test["Target_Value"], errors="coerce"
                )
            else:
                y_train = pd.to_numeric(
                    train["Target_Value"], errors="coerce"
                ).astype(int)
                y_test = pd.to_numeric(
                    test["Target_Value"], errors="coerce"
                ).astype(int)

            if target_type == "classification" and y_train.nunique() < 2:
                rows.append(
                    {
                        "Fold": fold,
                        "Algorithm": algorithm,
                        "Status": "Skipped - one training class",
                    }
                )
                continue

            model = _make_single_model(algorithm, target_type)

            X_train, X_test = _prepare_features_for_model(
                train,
                test,
                feature_columns,
            )

            try:
                model.fit(X_train, y_train)
                metrics, _, probability = _evaluate_model(
                    model,
                    X_test,
                    y_test,
                    target_type,
                )

                row = {
                    "Fold": fold,
                    "Algorithm": algorithm,
                    "Status": "OK",
                }
                row.update(metrics)
                rows.append(row)
            except Exception as exc:
                rows.append(
                    {
                        "Fold": fold,
                        "Algorithm": algorithm,
                        "Status": f"Failed: {exc}",
                    }
                )

    detail = pd.DataFrame(rows)

    if detail.empty:
        return detail, detail.copy()

    ok = detail[detail["Status"] == "OK"].copy()
    if ok.empty:
        return detail, ok

    numeric_columns = [
        c for c in ["MAE", "RMSE", "R2", "Accuracy", "Precision", "Recall", "F1", "ROC_AUC"]
        if c in ok.columns
    ]

    summary = (
        ok.groupby("Algorithm")[numeric_columns]
        .mean(numeric_only=True)
        .reset_index()
    )

    return detail, summary


def participant_holdout_validation(
    data: pd.DataFrame,
    feature_columns: list[str],
    target_type: str,
    algorithm: str,
) -> tuple[dict[str, float], dict[str, Any]]:
    """
    Validate the selected algorithm on participants excluded from training.
    """
    participants = sorted(
        data["Id"].astype("string").dropna().unique().tolist()
    )

    if len(participants) < 5:
        return {}, {
            "status": "Insufficient participants",
            "train_participants": len(participants),
            "test_participants": 0,
        }

    rng = np.random.default_rng(RANDOM_STATE)
    shuffled = np.array(participants, dtype=object)
    rng.shuffle(shuffled)

    test_count = max(1, int(np.ceil(len(shuffled) * 0.20)))
    test_participants = set(shuffled[:test_count].tolist())

    train = data[~data["Id"].isin(test_participants)].copy()
    test = data[data["Id"].isin(test_participants)].copy()

    if target_type == "classification":
        y_train = pd.to_numeric(train["Target_Value"], errors="coerce").astype(int)
        y_test = pd.to_numeric(test["Target_Value"], errors="coerce").astype(int)
        if y_train.nunique() < 2:
            return {}, {
                "status": "One training class",
                "train_participants": len(train["Id"].unique()),
                "test_participants": len(test["Id"].unique()),
            }
    else:
        y_train = pd.to_numeric(train["Target_Value"], errors="coerce")
        y_test = pd.to_numeric(test["Target_Value"], errors="coerce")

    X_train, X_test = _prepare_features_for_model(
        train,
        test,
        feature_columns,
    )

    model = _make_single_model(algorithm, target_type)

    try:
        model.fit(X_train, y_train)
        metrics, _, _ = _evaluate_model(
            model,
            X_test,
            y_test,
            target_type,
        )
        info = {
            "status": "OK",
            "train_participants": int(train["Id"].nunique()),
            "test_participants": int(test["Id"].nunique()),
        }
        return metrics, info
    except Exception as exc:
        return {}, {
            "status": f"Failed: {exc}",
            "train_participants": int(train["Id"].nunique()),
            "test_participants": int(test["Id"].nunique()),
        }


def walk_forward_backtest(
    data: pd.DataFrame,
    feature_columns: list[str],
    target_type: str,
    algorithm: str,
    min_train_rows: int = MIN_WALK_FORWARD_TRAIN,
    max_rows: int = MAX_WALK_FORWARD_ROWS,
) -> pd.DataFrame:
    work = (
        data
        .sort_values(["Target_Date", "Id"])
        .reset_index(drop=True)
    )

    if len(work) <= min_train_rows:
        return pd.DataFrame()

    start = max(
        min_train_rows,
        len(work) - max_rows,
    )

    rows: list[dict[str, Any]] = []

    for index in range(start, len(work)):
        train = work.iloc[:index].copy()
        test = work.iloc[[index]].copy()

        if target_type == "classification":
            y_train = pd.to_numeric(
                train["Target_Value"], errors="coerce"
            ).astype(int)
            y_test = pd.to_numeric(
                test["Target_Value"], errors="coerce"
            ).astype(int)

            if y_train.nunique() < 2:
                continue
        else:
            y_train = pd.to_numeric(
                train["Target_Value"], errors="coerce"
            )
            y_test = pd.to_numeric(
                test["Target_Value"], errors="coerce"
            )

        X_train, X_test = _prepare_features_for_model(
            train,
            test,
            feature_columns,
        )

        model = _make_single_model(algorithm, target_type)

        try:
            model.fit(X_train, y_train)
            prediction = model.predict(X_test)[0]

            row = {
                "Id": test.iloc[0]["Id"],
                "Feature_Date": test.iloc[0]["Feature_Date"],
                "Target_Date": test.iloc[0]["Target_Date"],
                "Actual": test.iloc[0]["Target_Value"],
                "Prediction": prediction,
                "Predicted": prediction,
            }

            if target_type == "classification":
                probability = model.predict_proba(X_test)[0, 1]
                row["Positive_Probability"] = float(probability)
                row["Probability_Positive"] = float(probability)

            rows.append(row)
        except Exception:
            continue

    return pd.DataFrame(rows)


# ============================================================
# Training
# ============================================================


def train_target(
    df: pd.DataFrame,
    spec: TargetSpec,
) -> dict[str, Any]:
    target = _get(spec, "target")
    if target is None:
        target = _get(spec, "target_column")

    target_type = _target_type(spec)

    feature_list = _get(spec, "feature_columns")
    if feature_list is None:
        feature_list = _get(spec, "features")
    if feature_list is None:
        feature_list = feature_columns()
    feature_list = list(feature_list)

    key = _get(spec, "key", target)
    display_name = _get(spec, "display_name", str(target))
    question = _get(spec, "question", "")
    forecast_horizon = _get(
        spec,
        "forecast_horizon",
        "next participant-day",
    )
    minimum_rows = int(
        _get(spec, "minimum_rows", 100)
    )

    if not target:
        raise ValueError("Target specification is missing target.")

    if not feature_list:
        raise ValueError(
            f"No feature columns configured for {target}."
        )

    forbidden = set(LEAKAGE_COLUMNS).intersection(feature_list)
    if forbidden:
        raise ValueError(
            "Leakage columns entered feature set: "
            + ", ".join(sorted(forbidden))
        )

    data = build_next_day_dataset(
        df=df,
        target=target,
        feature_columns=feature_list,
    )

    if data.empty:
        raise ValueError(
            f"No valid next-day observations available for {target}."
        )

    train, holdout = chronological_split(
        data,
        holdout_fraction=HOLDOUT_FRACTION,
    )

    if len(train) < minimum_rows:
        raise ValueError(
            f"{display_name}: only {len(train):,} training rows are "
            f"available; minimum is {minimum_rows:,}."
        )

    # --------------------------------------------------------
    # Classification governance checks
    # --------------------------------------------------------

    if target_type == "classification":
        y_train_check = pd.to_numeric(
            train["Target_Value"], errors="coerce"
        ).astype(int)
        y_holdout_check = pd.to_numeric(
            holdout["Target_Value"], errors="coerce"
        ).astype(int)

        if y_train_check.nunique() < 2:
            raise ValueError(
                f"{display_name}: training target contains only one class."
            )

        positive_required = _get(
            spec,
            "minimum_positive_class",
            None,
        )
        negative_required = _get(
            spec,
            "minimum_negative_class",
            None,
        )

        counts = y_train_check.value_counts()
        positive_count = int(counts.get(1, 0))
        negative_count = int(counts.get(0, 0))

        if (
            positive_required is not None
            and positive_count < int(positive_required)
        ):
            raise ValueError(
                f"{display_name}: only {positive_count} positive training "
                f"examples; minimum is {int(positive_required)}."
            )

        if (
            negative_required is not None
            and negative_count < int(negative_required)
        ):
            raise ValueError(
                f"{display_name}: only {negative_count} negative training "
                f"examples; minimum is {int(negative_required)}."
            )

        # A one-class holdout is valid for accuracy/F1/precision/recall;
        # ROC-AUC is simply omitted by _classification_metrics.
        _ = y_holdout_check

    # --------------------------------------------------------
    # Prepare model partitions
    # --------------------------------------------------------

    X_train, X_holdout = _prepare_features_for_model(
        train,
        holdout,
        feature_list,
    )

    if target_type == "classification":
        y_train = pd.to_numeric(
            train["Target_Value"], errors="coerce"
        ).astype(int)
        y_holdout = pd.to_numeric(
            holdout["Target_Value"], errors="coerce"
        ).astype(int)
        candidates = _classification_candidates()
    else:
        y_train = pd.to_numeric(
            train["Target_Value"], errors="coerce"
        )
        y_holdout = pd.to_numeric(
            holdout["Target_Value"], errors="coerce"
        )
        candidates = _regression_candidates()

    # --------------------------------------------------------
    # Candidate selection on chronological holdout
    # --------------------------------------------------------

    evaluations: list[dict[str, Any]] = []
    fitted_candidates: dict[str, Pipeline] = {}

    for algorithm, candidate in candidates.items():
        print(f"  Evaluating {algorithm}...")
        try:
            candidate.fit(X_train, y_train)
            metrics, _, _ = _evaluate_model(
                candidate,
                X_holdout,
                y_holdout,
                target_type,
            )
            evaluations.append(
                {
                    "algorithm": algorithm,
                    "metrics": metrics,
                    "status": "OK",
                }
            )
            fitted_candidates[algorithm] = candidate
        except Exception as exc:
            evaluations.append(
                {
                    "algorithm": algorithm,
                    "metrics": {},
                    "status": f"Failed: {exc}",
                    "error": str(exc),
                }
            )

    valid = [
        item for item in evaluations
        if item.get("status") == "OK"
    ]

    if not valid:
        details = "; ".join(
            f"{item['algorithm']}: {item.get('error', 'unknown error')}"
            for item in evaluations
        )
        raise RuntimeError(
            f"No candidate model could be trained for {target}. "
            f"Details: {details}"
        )

    if target_type == "regression":
        selected = min(
            valid,
            key=lambda item: item["metrics"].get("MAE", np.inf),
        )
    else:
        selected = max(
            valid,
            key=lambda item: item["metrics"].get("F1", -np.inf),
        )

    selected_algorithm = selected["algorithm"]

    # Refit the selected production model on ALL forecasting rows after
    # evaluating it on the chronological holdout.
    production_model = _make_single_model(
        selected_algorithm,
        target_type,
    )

    X_all, _ = _prepare_features_for_model(
        data,
        data.iloc[0:0].copy(),
        feature_list,
    )

    if target_type == "classification":
        y_all = pd.to_numeric(
            data["Target_Value"], errors="coerce"
        ).astype(int)
    else:
        y_all = pd.to_numeric(
            data["Target_Value"], errors="coerce"
        )

    production_model.fit(X_all, y_all)

    # Holdout predictions are generated with the selected holdout-fitted model.
    selected_holdout_model = fitted_candidates[selected_algorithm]
    selected_holdout_prediction = selected_holdout_model.predict(X_holdout)

    holdout_predictions = holdout[
        [
            "Id",
            "Feature_Date",
            "Target_Date",
            "Target_Value",
        ]
    ].copy()
    holdout_predictions["Actual"] = holdout_predictions.pop(
        "Target_Value"
    )
    holdout_predictions["Prediction"] = selected_holdout_prediction
    holdout_predictions["Predicted"] = selected_holdout_prediction

    if target_type == "classification":
        selected_probability = (
            selected_holdout_model
            .predict_proba(X_holdout)[:, 1]
        )
        holdout_predictions["Positive_Probability"] = selected_probability
        holdout_predictions["Probability_Positive"] = selected_probability

    # --------------------------------------------------------
    # Rolling validation evidence
    # --------------------------------------------------------

    rolling_detail, rolling_summary = rolling_time_validation(
        data=data,
        feature_columns=feature_list,
        target_type=target_type,
        algorithms=list(candidates.keys()),
    )

    # --------------------------------------------------------
    # Participant holdout evidence
    # --------------------------------------------------------

    participant_metrics, participant_info = participant_holdout_validation(
        data=data,
        feature_columns=feature_list,
        target_type=target_type,
        algorithm=selected_algorithm,
    )

    # --------------------------------------------------------
    # Walk-forward evidence
    # --------------------------------------------------------

    backtest = walk_forward_backtest(
        data=data,
        feature_columns=feature_list,
        target_type=target_type,
        algorithm=selected_algorithm,
        min_train_rows=min(
            MIN_WALK_FORWARD_TRAIN,
            max(20, len(train) // 3),
        ),
    )

    if not backtest.empty:
        if target_type == "regression":
            backtest_metrics = _regression_metrics(
                backtest["Actual"],
                backtest["Prediction"].to_numpy(),
            )
        else:
            backtest_metrics = _classification_metrics(
                backtest["Actual"].astype(int),
                backtest["Prediction"].astype(int).to_numpy(),
                backtest.get("Positive_Probability", pd.Series(dtype=float)).to_numpy()
                if "Positive_Probability" in backtest.columns
                else None,
            )
        backtest_start = str(
            pd.to_datetime(backtest["Target_Date"]).min().date()
        )
        backtest_end = str(
            pd.to_datetime(backtest["Target_Date"]).max().date()
        )
    else:
        backtest_metrics = {}
        backtest_start = "N/A"
        backtest_end = "N/A"

    # --------------------------------------------------------
    # Training metadata
    # --------------------------------------------------------

    now = datetime.now(timezone.utc)
    model_version = (
        f"{key}-{now:%Y%m%d-%H%M%S}"
    )

    rolling_detail_records = (
        rolling_detail.to_dict(orient="records")
        if not rolling_detail.empty
        else []
    )
    rolling_summary_records = (
        rolling_summary.to_dict(orient="records")
        if not rolling_summary.empty
        else []
    )

    selected_metrics = selected["metrics"]

    metadata = {
        "schema_version": 2,
        "model_version": model_version,
        "target_key": key,
        "display_name": display_name,
        "question": question,
        "target": target,
        "target_type": target_type,
        "problem_type": target_type,
        "algorithm": selected_algorithm,
        "forecast_horizon": forecast_horizon,
        "feature_policy": "current participant-day measurements as one-day lag to target",
        "feature_columns": feature_list,
        "features": feature_list,
        "leakage_columns_excluded": sorted(
            set(LEAKAGE_COLUMNS)
        ),
        "source_rows": int(len(df)),
        "forecast_rows": int(len(data)),
        "training_rows": int(len(train)),
        "holdout_rows": int(len(holdout)),
        "training_start": str(
            pd.to_datetime(train["Target_Date"]).min().date()
        ),
        "training_end": str(
            pd.to_datetime(train["Target_Date"]).max().date()
        ),
        "holdout_start": str(
            pd.to_datetime(holdout["Target_Date"]).min().date()
        ),
        "holdout_end": str(
            pd.to_datetime(holdout["Target_Date"]).max().date()
        ),
        "holdout_target_start": str(
            pd.to_datetime(holdout["Target_Date"]).min().date()
        ),
        "holdout_target_end": str(
            pd.to_datetime(holdout["Target_Date"]).max().date()
        ),
        "selected_metrics": selected_metrics,
        "selected_holdout_metrics": selected_metrics,
        "candidate_metrics": {
            item["algorithm"]: item.get("metrics", {})
            for item in evaluations
        },
        "model_comparison": evaluations,
        "candidate_evaluations": evaluations,
        "backtest_rows": int(len(backtest)),
        "backtest_start": backtest_start,
        "backtest_end": backtest_end,
        "backtest_method": "expanding-window walk-forward",
        "backtest_metrics": backtest_metrics,
        "rolling_validation": rolling_detail_records,
        "rolling_validation_folds": rolling_summary_records,
        "participant_holdout_metrics": participant_metrics,
        "participant_holdout_algorithm": selected_algorithm,
        "participant_holdout_train_participants": participant_info.get(
            "train_participants"
        ),
        "participant_holdout_test_participants": participant_info.get(
            "test_participants"
        ),
        "participant_holdout_status": participant_info.get(
            "status", "Unknown"
        ),
        "target_distribution_training": (
            {
                str(k): int(v)
                for k, v in train["Target_Value"]
                .value_counts(dropna=False)
                .items()
            }
            if target_type == "classification"
            else {
                "min": float(train["Target_Value"].min()),
                "max": float(train["Target_Value"].max()),
                "mean": float(train["Target_Value"].mean()),
            }
        ),
        "approval_status": "shadow",
        "selection_method": "chronological holdout primary metric",
        "production_fit": "refit on all available next-day observations",
        "created_at": now.isoformat(),
    }

    return {
        "model": production_model,
        "metadata": metadata,
        "holdout_predictions": holdout_predictions,
        "backtest_predictions": backtest,
        "forecasting_table": data,
        "rolling_validation": rolling_detail,
        "rolling_validation_summary": rolling_summary,
        "participant_holdout_metrics": participant_metrics,
    }


# ============================================================
# Persistence
# ============================================================


def save_target_bundle(
    result: dict[str, Any],
    model_root: str | Path,
) -> Path:
    metadata = result["metadata"]
    model_root = Path(model_root)
    target_key = metadata["target_key"]
    target_dir = model_root / target_key
    target_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = target_dir / "model.joblib"
    metadata_path = target_dir / "metadata.json"
    holdout_path = target_dir / "holdout_predictions.csv"
    backtest_path = target_dir / "walk_forward_predictions.csv"
    rolling_path = target_dir / "rolling_validation.csv"
    rolling_summary_path = target_dir / "rolling_validation_summary.csv"

    joblib.dump(result["model"], artifact_path)

    metadata_path.write_text(
        json.dumps(metadata, indent=2, default=str),
        encoding="utf-8",
    )

    result["holdout_predictions"].to_csv(
        holdout_path,
        index=False,
    )

    result["backtest_predictions"].to_csv(
        backtest_path,
        index=False,
    )

    rolling = result.get("rolling_validation")
    if isinstance(rolling, pd.DataFrame):
        rolling.to_csv(rolling_path, index=False)

    rolling_summary = result.get("rolling_validation_summary")
    if isinstance(rolling_summary, pd.DataFrame):
        rolling_summary.to_csv(
            rolling_summary_path,
            index=False,
        )

    metadata["holdout_predictions_path"] = str(holdout_path)
    metadata["backtest_predictions_path"] = str(backtest_path)
    metadata["rolling_validation_path"] = str(rolling_path)
    metadata["rolling_validation_summary_path"] = str(
        rolling_summary_path
    )

    metadata_path.write_text(
        json.dumps(metadata, indent=2, default=str),
        encoding="utf-8",
    )

    return artifact_path


def load_target_bundle(
    target_key: str,
    model_root: str | Path,
) -> dict[str, Any] | None:
    target_dir = Path(model_root) / target_key
    model_path = target_dir / "model.joblib"
    metadata_path = target_dir / "metadata.json"

    if not model_path.exists() or not metadata_path.exists():
        return None

    model = joblib.load(model_path)
    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )

    holdout_path = target_dir / "holdout_predictions.csv"
    backtest_path = target_dir / "walk_forward_predictions.csv"

    holdout = (
        pd.read_csv(holdout_path)
        if holdout_path.exists()
        else pd.DataFrame()
    )
    backtest = (
        pd.read_csv(backtest_path)
        if backtest_path.exists()
        else pd.DataFrame()
    )

    for frame in [holdout, backtest]:
        for column in ["Feature_Date", "Target_Date"]:
            if column in frame.columns:
                frame[column] = pd.to_datetime(
                    frame[column],
                    errors="coerce",
                )

    return {
        "model": model,
        "metadata": metadata,
        "holdout_predictions": holdout,
        "backtest_predictions": backtest,
    }


# ============================================================
# Prediction helpers
# ============================================================


def predict(
    model: Any,
    feature_frame: pd.DataFrame,
    feature_list: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray | None]:
    if feature_list is None:
        feature_list = list(feature_columns())

    X = feature_frame.reindex(columns=feature_list).copy()

    for column in feature_list:
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

    # The production artifact contains an imputer, so missing inputs can be
    # passed directly to the fitted pipeline.
    prediction = model.predict(X)

    probability = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X)
        if probabilities.shape[1] >= 2:
            probability = probabilities[:, 1]

    return prediction, probability


__all__ = [
    "BASE_FEATURES",
    "CALENDAR_FEATURES",
    "TARGET_REGISTRY",
    "build_forecasting_table",
    "build_next_day_dataset",
    "build_modeling_table",
    "create_modeling_features",
    "chronological_split",
    "rolling_time_validation",
    "participant_holdout_validation",
    "walk_forward_backtest",
    "train_target",
    "save_target_bundle",
    "load_target_bundle",
    "predict",
]
