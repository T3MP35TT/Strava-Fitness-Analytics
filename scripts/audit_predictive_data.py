"""
Audit the predictive modeling dataset without training a model.

Run from the project root:

    python scripts/audit_predictive_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data import load_data_uncached
from utils.predictive_model import audit_daily_pipeline


def main() -> None:
    print("Loading canonical dataset...")
    df = load_data_uncached()

    audit = audit_daily_pipeline(df)

    print()
    print("PREDICTIVE DATA LINEAGE AUDIT")
    print("=============================")
    print(f"Source rows: {audit['raw_rows']:,}")
    print(
        "Rows after complete-case validation: "
        f"{audit['rows_after_complete_case_filter']:,}"
    )
    print(
        "Rows removed by complete-case validation: "
        f"{audit['row_loss_from_complete_case_filter']:,}"
    )
    print(
        "Unique dates after validation: "
        f"{audit['unique_dates_after_complete_case_filter']:,}"
    )
    print(
        "Daily rows before final feature drop: "
        f"{audit['daily_rows_before_feature_drop']:,}"
    )
    print(
        "Final daily modeling rows: "
        f"{audit['daily_rows_final']:,}"
    )
    print(
        "Daily dates removed after aggregation: "
        f"{audit['daily_dates_removed_after_aggregation']:,}"
    )

    if audit["removed_daily_dates"]:
        print(
            "Removed dates: "
            + ", ".join(audit["removed_daily_dates"])
        )

    print()
    print("Invalid numeric values by source column:")
    for column, count in audit["numeric_invalid_counts"].items():
        print(f"  {column}: {count:,}")

    print()
    print("Missing daily modeling values:")
    for column, count in audit["feature_missing_by_date"].items():
        print(f"  {column}: {count:,}")

    print()
    print(
        "Modeling period: "
        f"{audit['final_start']} → {audit['final_end']}"
    )


if __name__ == "__main__":
    main()
