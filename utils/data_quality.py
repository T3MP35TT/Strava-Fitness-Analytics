"""
Production data-quality and prediction-contract validation.

This module validates the canonical fitness dataset before the
prediction pipeline is allowed to generate routine forecasts.

The validator:
- checks the canonical dataset schema
- validates Date and participant identifiers
- checks duplicate participant-days
- checks participant date continuity
- validates numeric model inputs
- checks missingness on model inputs
- validates classification targets and class balance
- validates persisted model artifacts against the registry contract
- writes a machine-readable quality report

The validator does not modify the canonical dataset.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from utils.predictive_registry import (
    BASE_FEATURES,
    TARGET_REGISTRY,
    feature_columns,
)


QUALITY_ROOT_NAME = "quality"

MISSING_WARNING_THRESHOLD = 0.10
MISSING_BLOCK_THRESHOLD = 0.40

# These fields are explicitly handled by the predictive model
# pipeline with median imputation. Their missingness is reported
# as a warning rather than treated as an immediate hard block.
IMPUTED_FEATURES = {
    "Sleep_Minutes",
    "Time_In_Bed_Minutes",
    "Sleep_Efficiency_Pct",
}

IMPUTED_FEATURE_WARNING_THRESHOLD = 0.50
IMPUTED_FEATURE_BLOCK_THRESHOLD = 0.80

DATE_GAP_WARNING_RATE = 0.05

NON_NEGATIVE_COLUMNS = [
    "TotalSteps",
    "TotalDistance",
    "TrackerDistance",
    "Calories",
    "VeryActiveMinutes",
    "FairlyActiveMinutes",
    "LightlyActiveMinutes",
    "Total_Active_Minutes",
    "Sleep_Minutes",
    "Time_In_Bed_Minutes",
    "METs_Avg",
    "METs_Max",
    "Hourly_Avg_Intensity",
    "Hourly_Steps_Avg",
    "Minute_Intensity_Avg",
    "Minute_Active_Step_Minutes",
]

PERCENT_COLUMNS = [
    "Active_Minutes_Pct",
    "Very_Active_Pct",
    "Sleep_Efficiency_Pct",
]

CLASSIFICATION_TARGETS = {
    "Meets_10k_Steps": "activity_target",
    "Sleep_7h_Target": "sleep_target",
}


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    status: str,
    severity: str,
    value: Any,
    threshold: Any,
    detail: str,
) -> None:
    checks.append(
        {
            "name": name,
            "status": status,
            "severity": severity,
            "value": value,
            "threshold": threshold,
            "detail": detail,
        }
    )


def normalize_bool_series(
    series: pd.Series,
) -> pd.Series:
    mapping = {
        True: 1,
        False: 0,
        1: 1,
        0: 0,
        "True": 1,
        "False": 0,
        "true": 1,
        "false": 0,
        "TRUE": 1,
        "FALSE": 0,
        "1": 1,
        "0": 0,
    }

    return series.map(mapping)


def prepare_source(
    df: pd.DataFrame,
) -> pd.DataFrame:
    output = df.copy()

    if "Total_Active_Minutes" not in output.columns:
        activity_parts = [
            column
            for column in [
                "VeryActiveMinutes",
                "FairlyActiveMinutes",
                "LightlyActiveMinutes",
            ]
            if column in output.columns
        ]

        if activity_parts:
            output["Total_Active_Minutes"] = (
                output[activity_parts]
                .apply(
                    pd.to_numeric,
                    errors="coerce",
                )
                .fillna(0)
                .sum(axis=1)
            )

    if (
        "Meets_10k_Steps" not in output.columns
        and "TotalSteps" in output.columns
    ):
        steps = pd.to_numeric(
            output["TotalSteps"],
            errors="coerce",
        )

        output["Meets_10k_Steps"] = (
            steps >= 10000
        )

    if (
        "Sleep_7h_Target" not in output.columns
        and "Sleep_Minutes" in output.columns
    ):
        sleep = pd.to_numeric(
            output["Sleep_Minutes"],
            errors="coerce",
        )

        output["Sleep_7h_Target"] = (
            sleep >= 420
        )

    return output


def raw_required_columns() -> list[str]:
    required = {
        "Id",
        "Date",
    }

    for feature in feature_columns():
        if feature.startswith("Lag1_"):
            required.add(
                feature[len("Lag1_"):]
            )

    for spec in TARGET_REGISTRY.values():
        required.add(
            spec.target
        )

    return sorted(required)


def validate_model_contract(
    project_root: Path,
    checks: list[dict[str, Any]],
) -> None:
    model_root = (
        project_root
        / "models"
        / "predictive_models"
    )

    for key, spec in TARGET_REGISTRY.items():

        model_path = (
            model_root
            / key
            / "model.joblib"
        )

        metadata_path = (
            model_root
            / key
            / "metadata.json"
        )

        if not model_path.exists():
            add_check(
                checks,
                name=f"artifact:{key}",
                status="FAIL",
                severity="BLOCK",
                value=str(model_path),
                threshold="file exists",
                detail="Persisted model artifact is missing.",
            )
            continue

        if not metadata_path.exists():
            add_check(
                checks,
                name=f"metadata:{key}",
                status="FAIL",
                severity="BLOCK",
                value=str(metadata_path),
                threshold="file exists",
                detail="Persisted model metadata is missing.",
            )
            continue

        try:
            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception as exc:
            add_check(
                checks,
                name=f"metadata_parse:{key}",
                status="FAIL",
                severity="BLOCK",
                value=str(exc),
                threshold="valid JSON",
                detail="Model metadata could not be parsed.",
            )
            continue

        registry_features = list(
            spec.feature_columns
        )

        artifact_features = list(
            metadata.get(
                "feature_columns",
                metadata.get(
                    "features",
                    [],
                ),
            )
        )

        contract_matches = (
            registry_features
            == artifact_features
        )

        add_check(
            checks,
            name=f"feature_contract:{key}",
            status=(
                "PASS"
                if contract_matches
                else "FAIL"
            ),
            severity=(
                "INFO"
                if contract_matches
                else "BLOCK"
            ),
            value=artifact_features,
            threshold=registry_features,
            detail=(
                "Persisted artifact feature contract matches "
                "the predictive registry."
                if contract_matches
                else
                "Persisted artifact feature contract differs "
                "from the predictive registry."
            ),
        )

        target_matches = (
            metadata.get("target")
            == spec.target
        )

        add_check(
            checks,
            name=f"target_contract:{key}",
            status=(
                "PASS"
                if target_matches
                else "FAIL"
            ),
            severity=(
                "INFO"
                if target_matches
                else "BLOCK"
            ),
            value=metadata.get("target"),
            threshold=spec.target,
            detail=(
                "Persisted target matches the registry."
                if target_matches
                else
                "Persisted target differs from the registry."
            ),
        )

        try:
            joblib.load(
                model_path
            )

            artifact_load_status = "PASS"
            artifact_load_severity = "INFO"
            artifact_detail = (
                "Persisted model artifact loaded successfully."
            )

        except Exception as exc:
            artifact_load_status = "FAIL"
            artifact_load_severity = "BLOCK"
            artifact_detail = (
                f"Persisted model could not be loaded: {exc}"
            )

        add_check(
            checks,
            name=f"artifact_load:{key}",
            status=artifact_load_status,
            severity=artifact_load_severity,
            value=str(model_path),
            threshold="loadable joblib",
            detail=artifact_detail,
        )


def validate_dataset(
    df: pd.DataFrame,
    project_root: Path,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    source = prepare_source(
        df
    )

    source_rows = int(
        len(source)
    )

    participant_count = int(
        source["Id"].nunique()
        if "Id" in source.columns
        else 0
    )

    # --------------------------------------------------------
    # Dataset presence
    # --------------------------------------------------------

    add_check(
        checks,
        name="dataset_non_empty",
        status=(
            "PASS"
            if source_rows > 0
            else "FAIL"
        ),
        severity=(
            "INFO"
            if source_rows > 0
            else "BLOCK"
        ),
        value=source_rows,
        threshold="> 0",
        detail=(
            "Canonical dataset contains usable rows."
            if source_rows > 0
            else
            "Canonical dataset is empty."
        ),
    )

    # --------------------------------------------------------
    # Schema
    # --------------------------------------------------------

    required_columns = raw_required_columns()

    missing_columns = [
        column
        for column in required_columns
        if column not in source.columns
    ]

    add_check(
        checks,
        name="required_schema",
        status=(
            "PASS"
            if not missing_columns
            else "FAIL"
        ),
        severity=(
            "INFO"
            if not missing_columns
            else "BLOCK"
        ),
        value=missing_columns,
        threshold="all required columns present",
        detail=(
            "All model input and target columns are present."
            if not missing_columns
            else
            "Required columns are missing: "
            + ", ".join(missing_columns)
        ),
    )

    if "Date" not in source.columns:
        return build_report(
            source=source,
            checks=checks,
            project_root=project_root,
        )

    # --------------------------------------------------------
    # Date / participant identifiers
    # --------------------------------------------------------

    parsed_dates = pd.to_datetime(
        source["Date"],
        errors="coerce",
    )

    invalid_dates = int(
        parsed_dates.isna().sum()
    )

    add_check(
        checks,
        name="valid_dates",
        status=(
            "PASS"
            if invalid_dates == 0
            else "FAIL"
        ),
        severity=(
            "INFO"
            if invalid_dates == 0
            else "BLOCK"
        ),
        value=invalid_dates,
        threshold=0,
        detail=(
            "All Date values are parseable."
            if invalid_dates == 0
            else
            f"{invalid_dates:,} Date values could not be parsed."
        ),
    )

    source["Date"] = parsed_dates

    missing_ids = int(
        source["Id"].isna().sum()
        if "Id" in source.columns
        else source_rows
    )

    empty_ids = int(
        (
            source["Id"]
            .astype("string")
            .str.strip()
            .eq("")
            .sum()
        )
        if "Id" in source.columns
        else 0
    )

    invalid_id_count = (
        missing_ids
        + empty_ids
    )

    add_check(
        checks,
        name="valid_participant_ids",
        status=(
            "PASS"
            if invalid_id_count == 0
            else "FAIL"
        ),
        severity=(
            "INFO"
            if invalid_id_count == 0
            else "BLOCK"
        ),
        value=invalid_id_count,
        threshold=0,
        detail=(
            "All participant identifiers are present."
            if invalid_id_count == 0
            else
            f"{invalid_id_count:,} participant identifiers are missing or empty."
        ),
    )

    # --------------------------------------------------------
    # Duplicate participant-days
    # --------------------------------------------------------

    duplicate_rows = 0

    if {
        "Id",
        "Date",
    }.issubset(source.columns):

        duplicate_mask = source.duplicated(
            subset=[
                "Id",
                "Date",
            ],
            keep=False,
        )

        duplicate_rows = int(
            duplicate_mask.sum()
        )

    add_check(
        checks,
        name="participant_day_duplicates",
        status=(
            "PASS"
            if duplicate_rows == 0
            else "FAIL"
        ),
        severity=(
            "INFO"
            if duplicate_rows == 0
            else "BLOCK"
        ),
        value=duplicate_rows,
        threshold=0,
        detail=(
            "No duplicate participant-day records were found."
            if duplicate_rows == 0
            else
            f"{duplicate_rows:,} rows belong to duplicate participant-day keys."
        ),
    )

    # --------------------------------------------------------
    # Date horizon
    # --------------------------------------------------------

    today_utc = pd.Timestamp.now(
        tz="UTC"
    ).tz_localize(None)

    future_rows = int(
        (
            source["Date"]
            > today_utc.normalize()
        ).sum()
    )

    add_check(
        checks,
        name="future_dates",
        status=(
            "PASS"
            if future_rows == 0
            else "WARN"
        ),
        severity=(
            "INFO"
            if future_rows == 0
            else "WARN"
        ),
        value=future_rows,
        threshold=0,
        detail=(
            "No future-dated observations were found."
            if future_rows == 0
            else
            f"{future_rows:,} observations are dated in the future."
        ),
    )

    # --------------------------------------------------------
    # Participant date continuity
    # --------------------------------------------------------

    transitions = 0
    gap_count = 0

    if {
        "Id",
        "Date",
    }.issubset(source.columns):

        ordered = (
            source[
                ["Id", "Date"]
            ]
            .dropna()
            .sort_values(
                ["Id", "Date"]
            )
            .drop_duplicates(
                ["Id", "Date"]
            )
        )

        day_gaps = (
            ordered
            .groupby("Id")["Date"]
            .diff()
            .dt.days
            .dropna()
        )

        transitions = int(
            len(day_gaps)
        )

        gap_count = int(
            (day_gaps != 1).sum()
        )

    gap_rate = (
        gap_count / transitions
        if transitions
        else 0.0
    )

    if gap_count == 0:
        gap_status = "PASS"
        gap_severity = "INFO"
        gap_detail = (
            "Participant observations are consecutive across "
            "all observed transitions."
        )

    elif gap_rate <= DATE_GAP_WARNING_RATE:
        gap_status = "WARN"
        gap_severity = "WARN"
        gap_detail = (
            f"{gap_count:,} non-consecutive participant-date "
            f"transitions were found ({gap_rate:.1%})."
        )

    else:
        gap_status = "FAIL"
        gap_severity = "BLOCK"
        gap_detail = (
            f"{gap_count:,} non-consecutive participant-date "
            f"transitions were found ({gap_rate:.1%}), exceeding "
            f"the {DATE_GAP_WARNING_RATE:.1%} warning threshold."
        )

    add_check(
        checks,
        name="participant_date_continuity",
        status=gap_status,
        severity=gap_severity,
        value={
            "transitions": transitions,
            "gaps": gap_count,
            "gap_rate": gap_rate,
        },
        threshold={
            "warning_rate": DATE_GAP_WARNING_RATE
        },
        detail=gap_detail,
    )

    # --------------------------------------------------------
    # Numeric inputs
    # --------------------------------------------------------

    numeric_columns = [
        column
        for column in (
            BASE_FEATURES
            + [
                "TotalDistance",
                "TrackerDistance",
                "Sleep_Minutes",
                "Time_In_Bed_Minutes",
                "Sleep_Efficiency_Pct",
            ]
        )
        if column in source.columns
    ]

    for column in sorted(
        set(numeric_columns)
    ):

        numeric = pd.to_numeric(
            source[column],
            errors="coerce",
        )

        non_numeric_mask = (
            source[column].notna()
            & numeric.isna()
        )

        non_numeric_count = int(
            non_numeric_mask.sum()
        )

        finite_mask = np.isfinite(
            numeric.fillna(0)
            .to_numpy()
        )

        non_finite_count = int(
            (~finite_mask).sum()
        )

        if non_numeric_count or non_finite_count:
            add_check(
                checks,
                name=f"numeric_validity:{column}",
                status="FAIL",
                severity="BLOCK",
                value={
                    "non_numeric": non_numeric_count,
                    "non_finite": non_finite_count,
                },
                threshold=0,
                detail=(
                    f"{column} contains non-numeric or non-finite "
                    "values in model-relevant source data."
                ),
            )
        else:
            add_check(
                checks,
                name=f"numeric_validity:{column}",
                status="PASS",
                severity="INFO",
                value=0,
                threshold=0,
                detail=(
                    f"{column} is numerically parseable."
                ),
            )

    # --------------------------------------------------------
    # Missingness on model inputs
    # --------------------------------------------------------

    for column in sorted(
        set(
            [
                feature[len("Lag1_"):]
                for feature in feature_columns()
                if feature.startswith("Lag1_")
            ]
        )
    ):

        if column not in source.columns:
            continue

        missing_rate = float(
            source[column]
            .isna()
            .mean()
        )

        if column in IMPUTED_FEATURES:
            if missing_rate >= IMPUTED_FEATURE_BLOCK_THRESHOLD:
                status = "FAIL"
                severity = "BLOCK"
            elif missing_rate >= IMPUTED_FEATURE_WARNING_THRESHOLD:
                status = "WARN"
                severity = "WARN"
            else:
                status = "PASS"
                severity = "INFO"
        else:
            if missing_rate >= MISSING_BLOCK_THRESHOLD:
                status = "FAIL"
                severity = "BLOCK"
            elif missing_rate >= MISSING_WARNING_THRESHOLD:
                status = "WARN"
                severity = "WARN"
            else:
                status = "PASS"
                severity = "INFO"

        add_check(
            checks,
            name=f"missingness:{column}",
            status=status,
            severity=severity,
            value=missing_rate,
            threshold={
                "warning": MISSING_WARNING_THRESHOLD,
                "block": MISSING_BLOCK_THRESHOLD,
            },
            detail=(
                f"{column} missingness is {missing_rate:.1%}."
                + (
                    " The model pipeline handles this field with "
                    "median imputation."
                    if column in IMPUTED_FEATURES
                    else ""
                )
            ),
        )

    # --------------------------------------------------------
    # Basic value bounds
    # --------------------------------------------------------

    for column in NON_NEGATIVE_COLUMNS:
        if column not in source.columns:
            continue

        numeric = pd.to_numeric(
            source[column],
            errors="coerce",
        )

        negative_count = int(
            (numeric < 0)
            .fillna(False)
            .sum()
        )

        add_check(
            checks,
            name=f"non_negative:{column}",
            status=(
                "PASS"
                if negative_count == 0
                else "FAIL"
            ),
            severity=(
                "INFO"
                if negative_count == 0
                else "BLOCK"
            ),
            value=negative_count,
            threshold=0,
            detail=(
                f"{column} contains no negative values."
                if negative_count == 0
                else
                f"{column} contains {negative_count:,} negative values."
            ),
        )

    for column in PERCENT_COLUMNS:
        if column not in source.columns:
            continue

        numeric = pd.to_numeric(
            source[column],
            errors="coerce",
        )

        invalid_count = int(
            (
                (numeric < 0)
                | (numeric > 100)
            )
            .fillna(False)
            .sum()
        )

        add_check(
            checks,
            name=f"percent_range:{column}",
            status=(
                "PASS"
                if invalid_count == 0
                else "FAIL"
            ),
            severity=(
                "INFO"
                if invalid_count == 0
                else "BLOCK"
            ),
            value=invalid_count,
            threshold="[0, 100]",
            detail=(
                f"{column} is within the expected percentage range."
                if invalid_count == 0
                else
                f"{column} contains {invalid_count:,} values outside [0, 100]."
            ),
        )

    # --------------------------------------------------------
    # Classification targets / class balance
    # --------------------------------------------------------

    for target_column, key in CLASSIFICATION_TARGETS.items():

        if target_column not in source.columns:
            continue

        normalized = normalize_bool_series(
            source[target_column]
        )

        missing_target_count = int(
            normalized.isna().sum()
        )

        if target_column == "Sleep_7h_Target" and "Sleep_Minutes" in source.columns:
            sleep_missing = (
                pd.to_numeric(
                    source["Sleep_Minutes"],
                    errors="coerce",
                ).isna()
            )

            invalid_count = int(
                (
                    normalized.isna()
                    & ~sleep_missing
                ).sum()
            )

            target_missing_is_expected = (
                missing_target_count
                == int(sleep_missing.sum())
            )
        else:
            invalid_count = missing_target_count
            target_missing_is_expected = (
                missing_target_count == 0
            )

        add_check(
            checks,
            name=f"class_values:{key}",
            status=(
                "PASS"
                if invalid_count == 0
                else "FAIL"
            ),
            severity=(
                "INFO"
                if invalid_count == 0
                else "BLOCK"
            ),
            value={
                "invalid": invalid_count,
                "unknown": missing_target_count,
            },
            threshold="known target values are binary 0/1",
            detail=(
                (
                    f"{target_column} contains valid binary classes; "
                    f"{missing_target_count:,} observations are unknown."
                )
                if invalid_count == 0
                else
                f"{target_column} contains {invalid_count:,} invalid class values."
            ),
        )

        positive_count = int(
            (normalized == 1)
            .sum()
        )

        negative_count = int(
            (normalized == 0)
            .sum()
        )

        spec = TARGET_REGISTRY[
            key
        ]

        minimum_positive = int(
            spec.minimum_positive_class
        )

        minimum_negative = int(
            spec.minimum_negative_class
        )

        class_balance_ok = (
            positive_count
            >= minimum_positive
            and negative_count
            >= minimum_negative
        )

        add_check(
            checks,
            name=f"class_balance:{key}",
            status=(
                "PASS"
                if class_balance_ok
                else "FAIL"
            ),
            severity=(
                "INFO"
                if class_balance_ok
                else "BLOCK"
            ),
            value={
                "positive": positive_count,
                "negative": negative_count,
                "unknown": missing_target_count,
            },
            threshold={
                "minimum_positive": minimum_positive,
                "minimum_negative": minimum_negative,
            },
            detail=(
                f"{target_column} has {positive_count:,} positive, "
                f"{negative_count:,} negative, and "
                f"{missing_target_count:,} unknown observations."
                if class_balance_ok
                else
                f"{target_column} does not meet the configured "
                f"class-balance minimums among known labels."
            ),
        )

    return build_report(
        source=source,
        checks=checks,
        project_root=project_root,
    )


def build_report(
    *,
    source: pd.DataFrame,
    checks: list[dict[str, Any]],
    project_root: Path,
) -> dict[str, Any]:

    validate_model_contract(
        project_root,
        checks,
    )

    failures = [
        check
        for check in checks
        if check["status"] == "FAIL"
    ]

    warnings = [
        check
        for check in checks
        if check["status"] == "WARN"
    ]

    if failures:
        overall_status = "FAIL"
    elif warnings:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    date_series = (
        source["Date"].dropna()
        if "Date" in source.columns
        else pd.Series(dtype="datetime64[ns]")
    )

    dataset_path = (
        project_root
        / "data"
        / "processed"
        / "fitness_daily_master.csv"
    )

    report = {
        "schema_version": 1,
        "checked_at_utc": utc_now_iso(),
        "overall_status": overall_status,
        "summary": {
            "rows": int(len(source)),
            "participants": int(
                source["Id"].nunique()
                if "Id" in source.columns
                else 0
            ),
            "checks": int(len(checks)),
            "passed": int(
                sum(
                    check["status"] == "PASS"
                    for check in checks
                )
            ),
            "warnings": int(len(warnings)),
            "failures": int(len(failures)),
        },
        "date_range": {
            "start": (
                date_series.min().strftime("%Y-%m-%d")
                if not date_series.empty
                else None
            ),
            "end": (
                date_series.max().strftime("%Y-%m-%d")
                if not date_series.empty
                else None
            ),
        },
        "dataset": {
            "path": str(dataset_path),
            "sha256": (
                sha256_file(dataset_path)
                if dataset_path.exists()
                else None
            ),
        },
        "checks": checks,
    }

    return report


def write_report(
    report: dict[str, Any],
    project_root: Path,
) -> Path:

    quality_root = (
        project_root
        / "data"
        / QUALITY_ROOT_NAME
    )

    quality_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        quality_root
        / "data_quality_report.json"
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_path


def run_quality_gate(
    project_root: Path,
    source_path: Path | None = None,
) -> dict[str, Any]:

    if source_path is None:
        source_path = (
            project_root
            / "data"
            / "processed"
            / "fitness_daily_master.csv"
        )

    if not source_path.exists():
        report = {
            "schema_version": 1,
            "checked_at_utc": utc_now_iso(),
            "overall_status": "FAIL",
            "summary": {
                "rows": 0,
                "participants": 0,
                "checks": 1,
                "passed": 0,
                "warnings": 0,
                "failures": 1,
            },
            "date_range": {
                "start": None,
                "end": None,
            },
            "dataset": {
                "path": str(source_path),
                "sha256": None,
            },
            "checks": [
                {
                    "name": "dataset_file",
                    "status": "FAIL",
                    "severity": "BLOCK",
                    "value": str(source_path),
                    "threshold": "file exists",
                    "detail": "Canonical dataset file was not found.",
                }
            ],
        }

        write_report(
            report,
            project_root,
        )

        return report

    try:
        df = pd.read_csv(
            source_path
        )
    except Exception as exc:
        report = {
            "schema_version": 1,
            "checked_at_utc": utc_now_iso(),
            "overall_status": "FAIL",
            "summary": {
                "rows": 0,
                "participants": 0,
                "checks": 1,
                "passed": 0,
                "warnings": 0,
                "failures": 1,
            },
            "date_range": {
                "start": None,
                "end": None,
            },
            "dataset": {
                "path": str(source_path),
                "sha256": sha256_file(
                    source_path
                ),
            },
            "checks": [
                {
                    "name": "dataset_read",
                    "status": "FAIL",
                    "severity": "BLOCK",
                    "value": str(exc),
                    "threshold": "readable CSV",
                    "detail": "Canonical dataset could not be read.",
                }
            ],
        }

        write_report(
            report,
            project_root,
        )

        return report

    report = validate_dataset(
        df,
        project_root,
    )

    report["dataset"]["path"] = str(
        source_path
    )

    report["dataset"]["sha256"] = (
        sha256_file(source_path)
    )

    write_report(
        report,
        project_root,
    )

    return report


def print_report(
    report: dict[str, Any],
    report_path: Path,
) -> None:

    summary = report["summary"]

    print()
    print("=" * 72)
    print("PREDICTIVE DATA QUALITY GATE")
    print("=" * 72)

    print(
        f"Overall status: {report['overall_status']}"
    )

    print(
        f"Rows: {summary['rows']:,}"
    )

    print(
        f"Participants: {summary['participants']:,}"
    )

    print(
        f"Checks: {summary['checks']:,}"
    )

    print(
        f"Passed: {summary['passed']:,}"
    )

    print(
        f"Warnings: {summary['warnings']:,}"
    )

    print(
        f"Failures: {summary['failures']:,}"
    )

    print()
    print("CHECK RESULTS")
    print("-" * 72)

    for check in report["checks"]:
        print(
            f"[{check['status']:<4}] "
            f"{check['name']}"
        )

        if check["status"] != "PASS":
            print(
                f"       {check['detail']}"
            )

    print()
    print(
        f"Quality report: {report_path}"
    )


def enforce_quality_gate(
    report: dict[str, Any],
) -> None:

    if report["overall_status"] == "FAIL":
        raise RuntimeError(
            "Predictive data-quality gate failed. "
            "Routine prediction generation was blocked."
        )
