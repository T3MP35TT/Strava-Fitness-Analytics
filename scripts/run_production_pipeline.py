
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# PRODUCTION PIPELINE
# ============================================================
#
# Purpose:
#   Run the end-to-end predictive analytics lifecycle from one
#   batch entry point:
#
#   1. Data-quality gate
#   2. Model training / artifact refresh
#   3. Participant prediction store
#   4. Prediction monitoring
#   5. Run report + history
#
# Run from the project root:
#
#   python scripts/run_production_pipeline.py
#
# Daily operational run without retraining:
#
#   python scripts/run_production_pipeline.py --skip-training
#
# CI validation:
#
#   python scripts/run_production_pipeline.py --ci --skip-training
#
# The script intentionally orchestrates the existing tested scripts
# instead of duplicating their ML/data logic.
# ============================================================


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

PYTHON = sys.executable

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "fitness_daily_master.csv"
)

QUALITY_DIR = (
    PROJECT_ROOT
    / "data"
    / "quality"
)

RUN_REPORT_PATH = (
    QUALITY_DIR
    / "production_pipeline_latest.json"
)

RUN_HISTORY_PATH = (
    QUALITY_DIR
    / "production_pipeline_history.jsonl"
)

LOCK_PATH = (
    QUALITY_DIR
    / ".production_pipeline.lock"
)

MODEL_ROOT = (
    PROJECT_ROOT
    / "models"
    / "predictive_models"
)


STEPS = [
    (
        "data_quality",
        [
            "scripts/run_data_quality_gate.py",
        ],
    ),
    (
        "training",
        [
            "scripts/train_predictive_model.py",
        ],
    ),
    (
        "predictions",
        [
            "scripts/run_predictive_predictions.py",
        ],
    ),
    (
        "monitoring",
        [
            "scripts/run_predictive_monitoring.py",
            "--model",
            "all",
        ],
    ),
]


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def iso_timestamp(value: datetime) -> str:
    return value.isoformat()


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


def append_jsonl(
    path: Path,
    payload: dict[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as handle:

        handle.write(
            json.dumps(
                payload,
                default=str,
            )
        )

        handle.write("\n")


def acquire_lock() -> None:

    LOCK_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if LOCK_PATH.exists():

        existing = (
            LOCK_PATH
            .read_text(
                encoding="utf-8"
            )
            .strip()
        )

        raise RuntimeError(
            "Another production pipeline appears to be running. "
            f"Lock: {LOCK_PATH} "
            f"{existing}"
        )

    payload = {
        "pid": os.getpid(),
        "started_at_utc": iso_timestamp(
            utc_now()
        ),
    }

    LOCK_PATH.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )


def release_lock() -> None:

    try:
        LOCK_PATH.unlink(
            missing_ok=True
        )
    except Exception:
        pass


def run_command(
    name: str,
    command_parts: list[str],
    *,
    timeout_seconds: int = 900,
) -> dict[str, Any]:

    command = [
        PYTHON,
        *command_parts,
    ]

    started = time.perf_counter()

    print()
    print("=" * 72)
    print(
        f"STEP: {name.upper()}"
    )
    print("=" * 72)
    print(
        "Command:",
        " ".join(
            str(part)
            for part in command
        ),
    )

    try:

        # Force child Python processes to emit UTF-8 on Windows.
        # This prevents CP1252 console failures when a child script
        # prints Unicode characters such as the right-arrow symbol.
        child_env = os.environ.copy()
        child_env["PYTHONUTF8"] = "1"
        child_env["PYTHONIOENCODING"] = "utf-8"

        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=child_env,
            timeout=timeout_seconds,
        )

    except subprocess.TimeoutExpired as exc:

        elapsed = (
            time.perf_counter()
            - started
        )

        return {
            "name": name,
            "status": "FAILED",
            "return_code": None,
            "duration_seconds": round(
                elapsed,
                3,
            ),
            "stdout": (
                exc.stdout
                or ""
            ),
            "stderr": (
                exc.stderr
                or ""
            ),
            "error": (
                f"Step exceeded "
                f"{timeout_seconds} seconds."
            ),
        }

    elapsed = (
        time.perf_counter()
        - started
    )

    stdout = (
        completed.stdout
        or ""
    )

    stderr = (
        completed.stderr
        or ""
    )

    if stdout:
        print(stdout.rstrip())

    if stderr:
        print(
            stderr.rstrip(),
            file=sys.stderr,
        )

    status = (
        "SUCCESS"
        if completed.returncode == 0
        else "FAILED"
    )

    return {
        "name": name,
        "status": status,
        "return_code": completed.returncode,
        "duration_seconds": round(
            elapsed,
            3,
        ),
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
    }


def preflight(
    *,
    ci: bool = False,
) -> dict[str, Any]:

    required_files = [
        DATA_PATH,
        PROJECT_ROOT
        / "scripts"
        / "run_data_quality_gate.py",
        PROJECT_ROOT
        / "scripts"
        / "train_predictive_model.py",
        PROJECT_ROOT
        / "scripts"
        / "run_predictive_predictions.py",
        PROJECT_ROOT
        / "scripts"
        / "run_predictive_monitoring.py",
    ]

    missing = [
        str(path)
        for path in required_files
        if not path.exists()
    ]

    if missing:

        raise FileNotFoundError(
            "Production pipeline preflight failed. "
            "Missing required files:\n"
            + "\n".join(missing)
        )

    if not DATA_PATH.is_file():

        raise RuntimeError(
            f"Canonical dataset is not a file: {DATA_PATH}"
        )

    if DATA_PATH.stat().st_size <= 0:

        raise RuntimeError(
            "Canonical dataset is empty."
        )

    result = {
        "status": "PASS",
        "project_root": str(
            PROJECT_ROOT
        ),
        "python": PYTHON,
        "dataset": str(
            DATA_PATH
        ),
        "dataset_bytes": DATA_PATH.stat().st_size,
        "model_root": str(
            MODEL_ROOT
        ),
        "ci": ci,
        "checked_at_utc": iso_timestamp(
            utc_now()
        ),
    }

    print()
    print(
        "Preflight: PASS"
    )
    print(
        f"Dataset: {DATA_PATH}"
    )
    print(
        f"Dataset size: "
        f"{DATA_PATH.stat().st_size:,} bytes"
    )

    return result


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Run the production-style fitness "
            "analytics pipeline."
        )
    )

    parser.add_argument(
        "--skip-training",
        action="store_true",
        help=(
            "Skip model retraining and use the "
            "currently persisted model artifacts."
        ),
    )

    parser.add_argument(
        "--skip-monitoring",
        action="store_true",
        help=(
            "Stop after prediction generation."
        ),
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help=(
            "Run in CI mode. Implies --skip-training "
            "unless training is explicitly requested."
        ),
    )

    parser.add_argument(
        "--training-timeout",
        type=int,
        default=1800,
        help=(
            "Maximum training step duration in seconds."
        ),
    )

    parser.add_argument(
        "--step-timeout",
        type=int,
        default=900,
        help=(
            "Maximum duration for non-training steps."
        ),
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    if (
        args.ci
        and not args.skip_training
    ):
        # CI should validate the deployment path against
        # persisted artifacts rather than retrain models.
        args.skip_training = True

    started_at = utc_now()

    report: dict[str, Any] = {
        "run_id": started_at.strftime(
            "%Y%m%dT%H%M%SZ"
        ),
        "started_at_utc": iso_timestamp(
            started_at
        ),
        "status": "RUNNING",
        "options": {
            "skip_training": args.skip_training,
            "skip_monitoring": args.skip_monitoring,
            "ci": args.ci,
        },
        "steps": [],
    }

    QUALITY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    acquire_lock()

    try:

        report["preflight"] = preflight(
            ci=args.ci
        )

        # ----------------------------------------------------
        # DATA QUALITY
        # ----------------------------------------------------

        quality_result = run_command(
            "data_quality",
            STEPS[0][1],
            timeout_seconds=args.step_timeout,
        )

        report["steps"].append(
            quality_result
        )

        if quality_result["status"] != "SUCCESS":

            raise RuntimeError(
                "Data-quality gate failed. "
                "Prediction generation was not allowed to continue."
            )

        # ----------------------------------------------------
        # MODEL TRAINING
        # ----------------------------------------------------

        if args.skip_training:

            training_result = {
                "name": "training",
                "status": "SKIPPED",
                "reason": "Training disabled for this run.",
            }

            print()
            print(
                "STEP: TRAINING"
            )
            print(
                "Status: SKIPPED"
            )

        else:

            training_result = run_command(
                "training",
                STEPS[1][1],
                timeout_seconds=(
                    args.training_timeout
                ),
            )

            if (
                training_result["status"]
                != "SUCCESS"
            ):

                report["steps"].append(
                    training_result
                )

                raise RuntimeError(
                    "Predictive model training failed."
                )

        report["steps"].append(
            training_result
        )

        # ----------------------------------------------------
        # PARTICIPANT PREDICTIONS
        # ----------------------------------------------------

        prediction_result = run_command(
            "predictions",
            STEPS[2][1],
            timeout_seconds=args.step_timeout,
        )

        report["steps"].append(
            prediction_result
        )

        if prediction_result["status"] != "SUCCESS":

            raise RuntimeError(
                "Participant prediction generation failed."
            )

        # ----------------------------------------------------
        # MONITORING
        # ----------------------------------------------------

        if args.skip_monitoring:

            monitoring_result = {
                "name": "monitoring",
                "status": "SKIPPED",
                "reason": "Monitoring disabled for this run.",
            }

            print()
            print(
                "STEP: MONITORING"
            )
            print(
                "Status: SKIPPED"
            )

        else:

            monitoring_result = run_command(
                "monitoring",
                STEPS[3][1],
                timeout_seconds=args.step_timeout,
            )

            if (
                monitoring_result["status"]
                != "SUCCESS"
            ):

                raise RuntimeError(
                    "Predictive monitoring failed."
                )

        report["steps"].append(
            monitoring_result
        )

        # ----------------------------------------------------
        # OUTPUT INVENTORY
        # ----------------------------------------------------

        outputs = {
            "quality_report": (
                PROJECT_ROOT
                / "data"
                / "quality"
                / "data_quality_report.json"
            ),
            "prediction_store": (
                PROJECT_ROOT
                / "data"
                / "processed"
                / "predictions.csv"
            ),
            "monitoring_log": (
                PROJECT_ROOT
                / "models"
                / "predictive_models"
                / "monitoring_log.csv"
            ),
        }

        report["outputs"] = {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "bytes": (
                    path.stat().st_size
                    if path.exists()
                    else None
                ),
            }
            for name, path in outputs.items()
        }

        # ----------------------------------------------------
        # FINAL STATUS
        # ----------------------------------------------------

        finished_at = utc_now()

        report["finished_at_utc"] = (
            iso_timestamp(
                finished_at
            )
        )

        report["duration_seconds"] = (
            finished_at - started_at
        ).total_seconds()

        report["status"] = "SUCCESS"

        write_json(
            RUN_REPORT_PATH,
            report,
        )

        append_jsonl(
            RUN_HISTORY_PATH,
            report,
        )

        print()
        print("=" * 72)
        print(
            "PRODUCTION PIPELINE: SUCCESS"
        )
        print("=" * 72)
        print(
            f"Run ID: {report['run_id']}"
        )
        print(
            f"Duration: "
            f"{report['duration_seconds']:.1f}s"
        )
        print(
            f"Report: {RUN_REPORT_PATH}"
        )

        return 0

    except Exception as exc:

        finished_at = utc_now()

        report["finished_at_utc"] = (
            iso_timestamp(
                finished_at
            )
        )

        report["duration_seconds"] = (
            finished_at - started_at
        ).total_seconds()

        report["status"] = "FAILED"
        report["error"] = str(
            exc
        )

        write_json(
            RUN_REPORT_PATH,
            report,
        )

        append_jsonl(
            RUN_HISTORY_PATH,
            report,
        )

        print()
        print("=" * 72)
        print(
            "PRODUCTION PIPELINE: FAILED"
        )
        print("=" * 72)
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        print(
            f"Report: {RUN_REPORT_PATH}"
        )

        return 1

    finally:

        release_lock()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
