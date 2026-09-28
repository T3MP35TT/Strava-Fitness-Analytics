"""
Run the predictive data-quality gate.

Run from the project root:

    python scripts/run_data_quality_gate.py

Exit codes:
- 0 = PASS or WARN
- 1 = FAIL / prediction should be blocked
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data_quality import (
    enforce_quality_gate,
    print_report,
    run_quality_gate,
)


def main() -> int:
    report = run_quality_gate(
        project_root=PROJECT_ROOT
    )

    report_path = (
        PROJECT_ROOT
        / "data"
        / "quality"
        / "data_quality_report.json"
    )

    print_report(
        report,
        report_path,
    )

    try:
        enforce_quality_gate(
            report
        )
    except RuntimeError as exc:
        print()
        print(
            f"BLOCKED: {exc}"
        )
        return 1

    if report["overall_status"] == "WARN":
        print()
        print(
            "QUALITY GATE PASSED WITH WARNINGS."
        )
    else:
        print()
        print(
            "QUALITY GATE PASSED."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
