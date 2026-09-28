"""
Train the multi-target predictive system.

This script:

1. Loads the canonical master dataset.
2. Trains each registered predictive target.
3. Uses chronological train/holdout validation.
4. Selects the best validated model.
5. Generates walk-forward historical predictions.
6. Saves the selected model and metadata.

Run from the project root:

    python scripts/train_predictive_model.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from utils.predictive_model import (
    save_target_bundle,
    train_target,
)

from utils.predictive_registry import (
    TARGET_REGISTRY,
)


DATA_CANDIDATES = [
    PROJECT_ROOT
    / "data"
    / "processed"
    / "fitness_daily_master.csv",

    PROJECT_ROOT
    / "data"
    / "fitness_daily_master.csv",
]


MODEL_ROOT = (
    PROJECT_ROOT
    / "models"
    / "predictive_models"
)


# ============================================================
# Dataset
# ============================================================

def load_canonical_dataset() -> pd.DataFrame:
    """Load the canonical fitness dataset."""

    for path in DATA_CANDIDATES:

        if path.exists():

            print(
                f"Loading canonical dataset: {path}",
                flush=True,
            )

            return pd.read_csv(path)

    raise FileNotFoundError(
        "Canonical master dataset not found.\n\n"
        "Expected one of:\n"
        + "\n".join(
            str(path)
            for path in DATA_CANDIDATES
        )
    )


# ============================================================
# Output helpers
# ============================================================

def print_metric_summary(
    metadata: dict,
) -> None:
    """Print selected-model metrics."""

    metrics = metadata.get(
        "selected_metrics",
        {},
    )

    if not metrics:

        print(
            "Selected holdout metrics: unavailable",
            flush=True,
        )

        return

    print(
        "Selected holdout metrics:",
        flush=True,
    )

    for key, value in metrics.items():

        try:

            print(
                f"  {key}: {float(value):.4f}",
                flush=True,
            )

        except (
            TypeError,
            ValueError,
        ):

            print(
                f"  {key}: {value}",
                flush=True,
            )


def print_model_comparison(
    metadata: dict,
) -> None:
    """Print candidate-model comparison."""

    comparison = metadata.get(
        "model_comparison",
        metadata.get(
            "candidate_metrics",
            {},
        ),
    )

    if not comparison:
        return

    print()
    print(
        "MODEL COMPARISON",
        flush=True,
    )
    print(
        "----------------",
        flush=True,
    )

    if isinstance(
        comparison,
        dict,
    ):

        for name, metrics in comparison.items():

            if not isinstance(
                metrics,
                dict,
            ):

                print(
                    f"{name}: {metrics}",
                    flush=True,
                )

                continue

            metric_text = " | ".join(
                f"{key}={value:.4f}"
                for key, value in metrics.items()
                if isinstance(
                    value,
                    (int, float),
                )
            )

            print(
                f"{name}: {metric_text}",
                flush=True,
            )

        return

    for model_result in comparison:

        name = model_result.get(
            "algorithm",
            "Unknown",
        )

        metrics = model_result.get(
            "metrics",
            {},
        )

        metric_text = " | ".join(
            f"{key}={value:.4f}"
            for key, value in metrics.items()
            if isinstance(
                value,
                (int, float),
            )
        )

        print(
            f"{name}: {metric_text}",
            flush=True,
        )


def print_backtest_summary(
    metadata: dict,
) -> None:
    """Print walk-forward backtest information."""

    print()
    print(
        "WALK-FORWARD BACKTEST",
        flush=True,
    )
    print(
        "---------------------",
        flush=True,
    )

    print(
        f"Backtest rows: "
        f"{metadata.get('backtest_rows', 0):,}",
        flush=True,
    )

    print(
        "Backtest period: "
        f"{metadata.get('backtest_start', 'N/A')} → "
        f"{metadata.get('backtest_end', 'N/A')}",
        flush=True,
    )

    print(
        "Method: "
        f"{metadata.get('backtest_method', 'walk-forward')}",
        flush=True,
    )

    path = metadata.get(
        "backtest_predictions_path",
    )

    if path:

        print(
            f"Backtest predictions: {path}",
            flush=True,
        )


def print_result(
    result: dict,
) -> None:
    """Print one completed target."""

    metadata = result["metadata"]

    print()
    print(
        "=" * 72,
        flush=True,
    )

    print(
        metadata["display_name"].upper(),
        flush=True,
    )

    print(
        "=" * 72,
        flush=True,
    )

    print(
        f"Question: {metadata['question']}",
        flush=True,
    )

    print(
        f"Selected algorithm: "
        f"{metadata['algorithm']}",
        flush=True,
    )

    print(
        f"Forecast horizon: "
        f"{metadata['forecast_horizon']}",
        flush=True,
    )

    print()
    print(
        "DATA",
        flush=True,
    )

    print(
        "----",
        flush=True,
    )

    print(
        f"Source rows: "
        f"{metadata['source_rows']:,}",
        flush=True,
    )

    print(
        f"Forecast rows: "
        f"{metadata['forecast_rows']:,}",
        flush=True,
    )

    print(
        f"Training rows: "
        f"{metadata['training_rows']:,}",
        flush=True,
    )

    print(
        f"Holdout rows: "
        f"{metadata['holdout_rows']:,}",
        flush=True,
    )

    print(
        f"Training target period: "
        f"{metadata.get('training_start', 'N/A')} → "
        f"{metadata.get('training_end', 'N/A')}",
        flush=True,
    )

    print(
        f"Holdout target period: "
        f"{metadata.get('holdout_start', 'N/A')} → "
        f"{metadata.get('holdout_end', 'N/A')}",
        flush=True,
    )

    print_model_comparison(
        metadata,
    )

    print()
    print(
        "SELECTED MODEL",
        flush=True,
    )

    print(
        "--------------",
        flush=True,
    )

    print(
        f"Algorithm: "
        f"{metadata['algorithm']}",
        flush=True,
    )

    print_metric_summary(
        metadata,
    )

    print_backtest_summary(
        metadata,
    )

    print()
    print(
        "NEXT-DAY FORECAST",
        flush=True,
    )

    print(
        "-----------------",
        flush=True,
    )

    forecast = metadata.get(
        "latest_forecast",
    )

    if forecast:

        for key, value in forecast.items():

            print(
                f"{key}: {value}",
                flush=True,
            )

    else:

        print(
            "Latest forecast will be generated "
            "by the prediction layer.",
            flush=True,
        )

    print()
    print(
        "Approval status: shadow",
        flush=True,
    )

    print(
        "Note: shadow refers to the model lifecycle state. "
        "The dashboard may use the model for analytical "
        "forecasting, but the artifact is not represented "
        "as an autonomous clinical or operational decision system.",
        flush=True,
    )


# ============================================================
# Target validation
# ============================================================

def validate_target_spec(
    key: str,
    spec,
) -> None:
    """Validate the registry entry before training."""

    required = [
        "key",
        "display_name",
        "question",
        "target",
        "target_type",
        "feature_columns",
    ]

    missing = []

    for field in required:

        if not hasattr(
            spec,
            field,
        ):

            missing.append(field)

    if missing:

        raise ValueError(
            f"Target specification '{key}' "
            f"is missing fields: "
            f"{', '.join(missing)}"
        )

    if spec.target not in {
        "Calories",
        "Meets_10k_Steps",
        "Sleep_7h_Target",
    }:

        raise ValueError(
            f"Unsupported target column "
            f"for '{key}': {spec.target}"
        )

    if spec.target_type not in {
        "regression",
        "classification",
    }:

        raise ValueError(
            f"Unsupported target type "
            f"for '{key}': {spec.target_type}"
        )

    if not spec.feature_columns:

        raise ValueError(
            f"No feature columns configured "
            f"for '{key}'."
        )


# ============================================================
# Main
# ============================================================

def main() -> None:

    started = time.perf_counter()

    df = load_canonical_dataset()

    if "Date" not in df.columns:

        raise ValueError(
            "Canonical dataset is missing "
            "required column: Date"
        )

    if "Id" not in df.columns:

        raise ValueError(
            "Canonical dataset is missing "
            "required column: Id"
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "Date",
            "Id",
        ],
    ).copy()

    print()
    print(
        "MULTI-TARGET PREDICTIVE TRAINING",
        flush=True,
    )

    print(
        "--------------------------------",
        flush=True,
    )

    print(
        f"Source rows: {len(df):,}",
        flush=True,
    )

    print(
        f"Participants: "
        f"{df['Id'].nunique():,}",
        flush=True,
    )

    print(
        "Date range: "
        f"{df['Date'].min():%Y-%m-%d} → "
        f"{df['Date'].max():%Y-%m-%d}",
        flush=True,
    )

    MODEL_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = {}

    total_targets = len(
        TARGET_REGISTRY,
    )

    # --------------------------------------------------------
    # Train each target
    # --------------------------------------------------------

    for position, (
        key,
        spec,
    ) in enumerate(
        TARGET_REGISTRY.items(),
        start=1,
    ):

        target_started = (
            time.perf_counter()
        )

        print()
        print(
            "=" * 72,
            flush=True,
        )

        print(
            f"[{position}/{total_targets}] "
            f"STARTING: "
            f"{spec.display_name.upper()}",
            flush=True,
        )

        print(
            f"Target: {spec.target}",
            flush=True,
        )

        print(
            f"Problem type: {spec.target_type}",
            flush=True,
        )

        print(
            f"Configured minimum rows: "
            f"{getattr(spec, 'minimum_rows', 0)}",
            flush=True,
        )

        print(
            "Training may take a little time...",
            flush=True,
        )

        print(
            "=" * 72,
            flush=True,
        )

        try:

            validate_target_spec(
                key,
                spec,
            )

            print(
                "Building next-day dataset...",
                flush=True,
            )

            result = train_target(
                df,
                spec,
            )

            print(
                "Training completed. Saving artifact...",
                flush=True,
            )

            artifact = save_target_bundle(
                result,
                MODEL_ROOT,
            )

            results[key] = result

            elapsed = (
                time.perf_counter()
                - target_started
            )

            print_result(
                result,
            )

            print()
            print(
                f"Artifact: {artifact}",
                flush=True,
            )

            print(
                f"Target elapsed time: "
                f"{elapsed:.1f}s",
                flush=True,
            )

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - target_started
            )

            print()
            print(
                "=" * 72,
                flush=True,
            )

            print(
                f"{spec.display_name.upper()} "
                f"— NOT TRAINED",
                flush=True,
            )

            print(
                "=" * 72,
                flush=True,
            )

            print(
                f"Reason: {exc}",
                flush=True,
            )

            print(
                "This target remains disabled rather "
                "than being trained with insufficient "
                "or invalid evidence.",
                flush=True,
            )

            print(
                f"Target elapsed time: "
                f"{elapsed:.1f}s",
                flush=True,
            )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print(
        "=" * 72,
        flush=True,
    )

    print(
        "TRAINING SUMMARY",
        flush=True,
    )

    print(
        "=" * 72,
        flush=True,
    )

    for key, spec in TARGET_REGISTRY.items():

        if key in results:

            metadata = results[
                key
            ]["metadata"]

            print(
                f"{key}: "
                f"{metadata['algorithm']} | "
                f"{metadata['training_rows']:,} train | "
                f"{metadata['holdout_rows']:,} holdout | "
                f"{metadata.get('backtest_rows', 0):,} backtest | "
                f"shadow",
                flush=True,
            )

        else:

            print(
                f"{key}: NOT TRAINED",
                flush=True,
            )

    total_elapsed = (
        time.perf_counter()
        - started
    )

    print()
    print(
        f"Model root: {MODEL_ROOT}",
        flush=True,
    )

    print(
        f"Total training time: "
        f"{total_elapsed:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()