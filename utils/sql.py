
from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_QUERY_LIMIT = 5000
MAX_QUERY_CHARS = 12000
QUERY_TIMEOUT_SECONDS = 5.0

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

AUDIT_LOG_PATH = (
    PROJECT_ROOT
    / "data"
    / "quality"
    / "sql_query_audit_log.csv"
)


# ============================================================
# SQL VALIDATION
# ============================================================

# END is intentionally not blocked because it is a valid SQL token
# in CASE ... WHEN ... THEN ... ELSE ... END expressions.
FORBIDDEN = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|"
    r"ATTACH|DETACH|VACUUM|REINDEX|ANALYZE|PRAGMA|"
    r"BEGIN|COMMIT|ROLLBACK|SAVEPOINT"
    r")\b",
    re.IGNORECASE,
)


def normalize_query(query: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        query.strip(),
    )


def query_hash(query: str) -> str:
    return hashlib.sha256(
        normalize_query(query).encode(
            "utf-8"
        )
    ).hexdigest()[:16]


def validate_sql(
    query: str,
    max_query_chars: int = MAX_QUERY_CHARS,
):
    q = query.strip()

    if not q:
        return False, "Enter a SQL query."

    if len(q) > max_query_chars:
        return (
            False,
            f"Query exceeds the {max_query_chars:,}-character limit.",
        )

    if (
        q.count(";") > 1
        or (
            ";" in q
            and not q.rstrip().endswith(";")
        )
    ):
        return (
            False,
            "Only one SQL statement is allowed.",
        )

    if not re.match(
        r"^(SELECT|WITH)\b",
        q,
        re.IGNORECASE,
    ):
        return (
            False,
            "Only read-only SELECT or WITH queries are allowed.",
        )

    if FORBIDDEN.search(q):
        return (
            False,
            "This playground blocks write, schema, transaction, "
            "and administrative SQL commands.",
        )

    return True, ""


# ============================================================
# SQLITE AUTHORISER
# ============================================================

def _make_sqlite_authorizer(
    *,
    allow_readonly_pragma=False,
):
    """
    Return a SQLite authorizer callback.

    User queries receive a fully restrictive authorizer.
    Internal schema inspection may opt into read-only PRAGMA calls.
    """

    denied_actions = {
        sqlite3.SQLITE_INSERT,
        sqlite3.SQLITE_UPDATE,
        sqlite3.SQLITE_DELETE,
        sqlite3.SQLITE_ALTER_TABLE,
        sqlite3.SQLITE_DROP_TABLE,
        sqlite3.SQLITE_DROP_INDEX,
        sqlite3.SQLITE_DROP_TRIGGER,
        sqlite3.SQLITE_DROP_VIEW,
        sqlite3.SQLITE_CREATE_INDEX,
        sqlite3.SQLITE_CREATE_TABLE,
        sqlite3.SQLITE_CREATE_TEMP_INDEX,
        sqlite3.SQLITE_CREATE_TEMP_TABLE,
        sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
        sqlite3.SQLITE_CREATE_TEMP_VIEW,
        sqlite3.SQLITE_CREATE_TRIGGER,
        sqlite3.SQLITE_CREATE_VIEW,
        sqlite3.SQLITE_ATTACH,
        sqlite3.SQLITE_DETACH,
        sqlite3.SQLITE_TRANSACTION,
    }

    def authorizer(
        action,
        arg1,
        arg2,
        db_name,
        trigger_name,
    ):
        if (
            action == sqlite3.SQLITE_PRAGMA
            and allow_readonly_pragma
        ):
            return sqlite3.SQLITE_OK

        if action == sqlite3.SQLITE_PRAGMA:
            return sqlite3.SQLITE_DENY

        if action == getattr(
            sqlite3,
            "SQLITE_VACUUM",
            object(),
        ):
            return sqlite3.SQLITE_DENY

        if action in denied_actions:
            return sqlite3.SQLITE_DENY

        return sqlite3.SQLITE_OK

    return authorizer


# ============================================================
# READ-ONLY CONNECTION
# ============================================================

def _readonly_connection(
    db_path,
    *,
    allow_readonly_pragma=False,
) -> sqlite3.Connection:

    path = Path(
        db_path
    ).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Database not found: {path}"
        )

    # SQLite URI mode=ro prevents the connection from opening
    # the database for writes.
    uri = (
        f"file:{path.as_posix()}"
        "?mode=ro"
    )

    conn = sqlite3.connect(
        uri,
        uri=True,
    )

    conn.execute(
        "PRAGMA query_only = ON"
    )

    conn.set_authorizer(
        _make_sqlite_authorizer(
            allow_readonly_pragma=allow_readonly_pragma
        )
    )

    return conn


# ============================================================
# TIMEOUT
# ============================================================

def _install_timeout(
    conn: sqlite3.Connection,
    timeout_seconds: float,
):
    deadline = (
        time.perf_counter()
        + float(timeout_seconds)
    )

    def progress_handler():
        return (
            1
            if time.perf_counter() >= deadline
            else 0
        )

    conn.set_progress_handler(
        progress_handler,
        10_000,
    )


# ============================================================
# AUDIT LOG
# ============================================================

def _write_audit_event(
    *,
    query,
    query_type,
    status,
    started_at,
    execution_ms,
    returned_rows=None,
    error_message="",
    context="",
):
    AUDIT_LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = pd.DataFrame(
        [
            {
                "timestamp_utc": datetime.now(
                    timezone.utc
                ).isoformat(),
                "query_type": query_type,
                "context": context,
                "status": status,
                "query_hash": query_hash(query),
                "query_chars": len(
                    query.strip()
                ),
                "execution_ms": round(
                    float(execution_ms),
                    2,
                ),
                "returned_rows": (
                    returned_rows
                    if returned_rows is not None
                    else ""
                ),
                "error": error_message or "",
                "query": normalize_query(
                    query
                ),
            }
        ]
    )

    write_header = (
        not AUDIT_LOG_PATH.exists()
        or AUDIT_LOG_PATH.stat().st_size == 0
    )

    record.to_csv(
        AUDIT_LOG_PATH,
        mode="a",
        header=write_header,
        index=False,
    )


# ============================================================
# QUERY EXECUTION
# ============================================================

def run_query(
    db_path,
    query,
    limit=DEFAULT_QUERY_LIMIT,
    timeout_seconds=QUERY_TIMEOUT_SECONDS,
    query_type="custom",
    context="",
):
    ok, message = validate_sql(
        query
    )

    if not ok:
        _write_audit_event(
            query=query,
            query_type=query_type,
            status="REJECTED",
            started_at=datetime.now(
                timezone.utc
            ),
            execution_ms=0,
            returned_rows=None,
            error_message=message,
            context=context,
        )

        raise ValueError(
            message
        )

    safe_limit = min(
        max(
            int(limit),
            1,
        ),
        DEFAULT_QUERY_LIMIT,
    )

    clean = (
        query
        .strip()
        .rstrip(";")
    )

    wrapped = (
        "SELECT * FROM ("
        f"{clean}"
        ") "
        f"LIMIT {safe_limit}"
    )

    started = time.perf_counter()

    try:

        with _readonly_connection(
            db_path
        ) as conn:

            _install_timeout(
                conn,
                timeout_seconds,
            )

            result = pd.read_sql_query(
                wrapped,
                conn,
            )

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1000

        result.attrs[
            "sql_execution_ms"
        ] = float(
            elapsed_ms
        )

        result.attrs[
            "sql_query_hash"
        ] = query_hash(
            query
        )

        _write_audit_event(
            query=query,
            query_type=query_type,
            status="SUCCESS",
            started_at=None,
            execution_ms=elapsed_ms,
            returned_rows=len(result),
            error_message="",
            context=context,
        )

        return result

    except (
        sqlite3.DatabaseError,
        pd.errors.DatabaseError,
    ) as exc:

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1000

        _write_audit_event(
            query=query,
            query_type=query_type,
            status="ERROR",
            started_at=None,
            execution_ms=elapsed_ms,
            returned_rows=None,
            error_message=str(
                exc
            ),
            context=context,
        )

        message_text = str(
            exc
        )

        if (
            "interrupted"
            in message_text.lower()
        ):
            raise TimeoutError(
                f"Query exceeded the "
                f"{timeout_seconds:.1f}-second execution limit."
            ) from exc

        raise


# ============================================================
# SCHEMA
# ============================================================

def schema_info(
    db_path,
):
    with _readonly_connection(
        db_path,
        allow_readonly_pragma=True,
    ) as conn:

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """,
            conn,
        )

        rows = []

        for table in tables["name"]:

            # PRAGMA table_info is safe here because it is executed
            # by the application against a read-only connection.
            cols = pd.read_sql_query(
                f'PRAGMA table_info("{table}")',
                conn,
            )

            for _, row in cols.iterrows():

                rows.append(
                    {
                        "Table": table,
                        "Column": row["name"],
                        "Type": row["type"],
                        "Nullable": (
                            "No"
                            if row["notnull"]
                            else "Yes"
                        ),
                        "Primary Key": (
                            "Yes"
                            if row["pk"]
                            else "No"
                        ),
                    }
                )

        return pd.DataFrame(
            rows
        )


# ============================================================
# ANALYST EXAMPLES
# ============================================================

EXAMPLES = {
    "Daily activity summary": """
SELECT
    Date,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    ROUND(AVG(Calories), 0) AS avg_calories,
    ROUND(AVG(Total_Active_Minutes), 1) AS avg_active_minutes
FROM fitness_daily
GROUP BY Date
ORDER BY Date
""",
    "Top participants by steps": """
SELECT
    Id,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    COUNT(*) AS observation_days
FROM fitness_daily
WHERE TotalSteps IS NOT NULL
GROUP BY Id
HAVING COUNT(*) >= 3
ORDER BY avg_steps DESC
LIMIT 10
""",
    "10K step achievement": """
SELECT
    CASE
        WHEN TotalSteps >= 10000 THEN 'Met 10K'
        ELSE 'Below 10K'
    END AS goal_status,
    COUNT(*) AS participant_days,
    ROUND(
        100.0 * COUNT(*) /
        (
            SELECT COUNT(*)
            FROM fitness_daily
            WHERE TotalSteps IS NOT NULL
        ),
        1
    ) AS pct
FROM fitness_daily
WHERE TotalSteps IS NOT NULL
GROUP BY goal_status
ORDER BY participant_days DESC
""",
    "Sleep and activity": """
SELECT
    ROUND(AVG(Sleep_Minutes) / 60.0, 2) AS avg_sleep_hours,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    ROUND(AVG(Calories), 0) AS avg_calories,
    ROUND(AVG(SedentaryMinutes), 0) AS avg_sedentary_minutes
FROM fitness_daily
WHERE Sleep_Minutes IS NOT NULL
""",
}


# ============================================================
# CEO / BUSINESS QUESTIONS
# ============================================================

BUSINESS_QUESTIONS = {
    "q1": {
        "title": "How large and active is the observed population?",
        "purpose": (
            "Establish the scale of the observed population and how often "
            "measured participant-days reached the 10K-step benchmark."
        ),
        "sql": """
SELECT
    COUNT(DISTINCT Id) AS participants,
    COUNT(*) AS participant_days,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN TotalSteps >= 10000 THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        1
    ) AS pct_days_meeting_10k
FROM fitness_daily
WHERE TotalSteps IS NOT NULL
""",
        "answer": lambda row: (
            f"The dataset covers {int(row['participants']):,} participants "
            f"across {int(row['participant_days']):,} measurable participant-days. "
            f"Average daily steps were {row['avg_steps']:,.0f}, and "
            f"{row['pct_days_meeting_10k']:.1f}% of measured days met the "
            "10K benchmark."
        ),
    },
    "q2": {
        "title": "Which participants show the strongest sustained activity?",
        "purpose": (
            "Identify consistently active participants using average step "
            "volume across multiple observed days rather than one-day spikes."
        ),
        "sql": """
SELECT
    Id,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    ROUND(AVG(Total_Active_Minutes), 1) AS avg_active_minutes,
    COUNT(*) AS observation_days
FROM fitness_daily
WHERE TotalSteps IS NOT NULL
GROUP BY Id
HAVING COUNT(*) >= 3
ORDER BY avg_steps DESC
LIMIT 5
""",
        "answer": lambda row: (
            f"Participant {row['Id']} has the highest average measured "
            f"step volume at {row['avg_steps']:,.0f} steps across "
            f"{int(row['observation_days']):,} observed days."
        ),
    },
    "q3": {
        "title": "Which day recorded the highest average calorie expenditure?",
        "purpose": (
            "Locate the strongest observed day for average energy expenditure "
            "and show its accompanying activity level."
        ),
        "sql": """
SELECT
    Date,
    ROUND(AVG(Calories), 0) AS avg_calories,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    ROUND(AVG(Total_Active_Minutes), 1) AS avg_active_minutes
FROM fitness_daily
WHERE Calories IS NOT NULL
GROUP BY Date
ORDER BY avg_calories DESC
LIMIT 1
""",
        "answer": lambda row: (
            f"{pd.to_datetime(row['Date']):%d %b %Y} had the highest "
            f"average calorie expenditure at {row['avg_calories']:,.0f} kcal, "
            f"with {row['avg_steps']:,.0f} average steps and "
            f"{row['avg_active_minutes']:,.1f} active minutes."
        ),
    },
    "q4": {
        "title": "How do higher-step days compare with lower-step days?",
        "purpose": (
            "Compare observed calorie expenditure and active minutes between "
            "days that met and did not meet the 10K-step benchmark."
        ),
        "sql": """
SELECT
    CASE
        WHEN TotalSteps >= 10000 THEN 'Met 10K'
        ELSE 'Below 10K'
    END AS activity_group,
    COUNT(*) AS participant_days,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    ROUND(AVG(Calories), 0) AS avg_calories,
    ROUND(AVG(Total_Active_Minutes), 1) AS avg_active_minutes
FROM fitness_daily
WHERE TotalSteps IS NOT NULL
  AND Calories IS NOT NULL
GROUP BY activity_group
ORDER BY avg_steps DESC
""",
        "answer": lambda row: (
            f"Within the {row['activity_group']} group, participant-days "
            f"averaged {row['avg_calories']:,.0f} kcal and "
            f"{row['avg_active_minutes']:,.1f} active minutes. "
            "The comparison is descriptive and does not establish causation."
        ),
    },
    "q5": {
        "title": "How much sleep data is available for analysis?",
        "purpose": (
            "Quantify sleep-data coverage before using sleep-related metrics "
            "or predictive results in reporting."
        ),
        "sql": """
SELECT
    COUNT(*) AS total_rows,
    SUM(
        CASE
            WHEN Sleep_Minutes IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS rows_with_sleep,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN Sleep_Minutes IS NOT NULL THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        1
    ) AS sleep_coverage_pct,
    ROUND(
        AVG(
            CASE
                WHEN Sleep_Minutes IS NOT NULL
                THEN Sleep_Minutes
            END
        ) / 60.0,
        2
    ) AS avg_sleep_hours
FROM fitness_daily
""",
        "answer": lambda row: (
            f"Sleep duration is available for {int(row['rows_with_sleep']):,} "
            f"of {int(row['total_rows']):,} records "
            f"({row['sleep_coverage_pct']:.1f}% coverage). "
            f"Average recorded sleep was {row['avg_sleep_hours']:.2f} hours."
        ),
    },
    "q6": {
        "title": "Which dates show the highest sedentary burden?",
        "purpose": (
            "Highlight dates with the highest average sedentary time for "
            "operational or engagement review."
        ),
        "sql": """
SELECT
    Date,
    ROUND(AVG(SedentaryMinutes), 0) AS avg_sedentary_minutes,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    ROUND(AVG(Total_Active_Minutes), 1) AS avg_active_minutes
FROM fitness_daily
WHERE SedentaryMinutes IS NOT NULL
GROUP BY Date
ORDER BY avg_sedentary_minutes DESC
LIMIT 5
""",
        "answer": lambda row: (
            f"{pd.to_datetime(row['Date']):%d %b %Y} shows the highest "
            f"average sedentary time at "
            f"{row['avg_sedentary_minutes']:,.0f} minutes."
        ),
    },
    "q7": {
        "title": "Are participants more active on weekdays or weekends?",
        "purpose": (
            "Compare average activity volume and calorie expenditure across "
            "weekday and weekend participant-days."
        ),
        "sql": """
SELECT
    CASE
        WHEN CAST(strftime('%w', Date) AS INTEGER) IN (0, 6)
            THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    COUNT(*) AS participant_days,
    ROUND(AVG(TotalSteps), 0) AS avg_steps,
    ROUND(AVG(Total_Active_Minutes), 1) AS avg_active_minutes,
    ROUND(AVG(Calories), 0) AS avg_calories
FROM fitness_daily
WHERE TotalSteps IS NOT NULL
GROUP BY day_type
ORDER BY avg_steps DESC
""",
        "answer": lambda row: (
            f"{row['day_type']} participant-days averaged "
            f"{row['avg_steps']:,.0f} steps, "
            f"{row['avg_active_minutes']:,.1f} active minutes, and "
            f"{row['avg_calories']:,.0f} kcal."
        ),
    },
    "q8": {
        "title": "How does sleep duration differ across activity levels?",
        "purpose": (
            "Compare recorded sleep duration across lower- and higher-step "
            "participant-days while keeping the interpretation descriptive."
        ),
        "sql": """
WITH activity_bands AS (
    SELECT
        CASE
            WHEN TotalSteps >= 10000 THEN 'Met 10K'
            ELSE 'Below 10K'
        END AS activity_group,
        Sleep_Minutes
    FROM fitness_daily
    WHERE TotalSteps IS NOT NULL
      AND Sleep_Minutes IS NOT NULL
)
SELECT
    activity_group,
    COUNT(*) AS participant_days,
    ROUND(AVG(Sleep_Minutes) / 60.0, 2) AS avg_sleep_hours,
    ROUND(AVG(Sleep_Minutes), 0) AS avg_sleep_minutes
FROM activity_bands
GROUP BY activity_group
ORDER BY avg_sleep_hours DESC
""",
        "answer": lambda row: (
            f"{row['activity_group']} participant-days averaged "
            f"{row['avg_sleep_hours']:.2f} hours of recorded sleep."
        ),
    },
    "q9": {
        "title": "How consistent is participant activity over time?",
        "purpose": (
            "Measure how much participants' daily step volume varies relative "
            "to their own average using a coefficient-of-variation style measure."
        ),
        "sql": """
WITH participant_stats AS (
    SELECT
        Id,
        COUNT(*) AS observation_days,
        AVG(TotalSteps) AS avg_steps,
        AVG(TotalSteps * TotalSteps)
            - AVG(TotalSteps) * AVG(TotalSteps) AS variance_steps
    FROM fitness_daily
    WHERE TotalSteps IS NOT NULL
    GROUP BY Id
    HAVING COUNT(*) >= 3
)
SELECT
    COUNT(*) AS participants_with_3plus_days,
    ROUND(AVG(avg_steps), 0) AS average_participant_step_mean,
    ROUND(
        AVG(
            CASE
                WHEN avg_steps > 0
                    THEN SQRT(
                        CASE
                            WHEN variance_steps > 0
                                THEN variance_steps
                            ELSE 0
                        END
                    ) / avg_steps
                ELSE NULL
            END
        ) * 100,
        1
    ) AS average_activity_cv_pct
FROM participant_stats
""",
        "answer": lambda row: (
            f"{int(row['participants_with_3plus_days']):,} participants "
            f"have at least 3 measured days. Their average participant-level "
            f"step mean is {row['average_participant_step_mean']:,.0f}, while "
            f"the average within-participant variability is "
            f"{row['average_activity_cv_pct']:.1f}% of the participant's own mean."
        ),
    },
    "q10": {
        "title": "Is calorie expenditure trending across the observation period?",
        "purpose": (
            "Compare average calorie expenditure across the first and second "
            "half of the observed period to identify directional change."
        ),
        "sql": """
WITH dated AS (
    SELECT
        Date,
        AVG(Calories) AS avg_calories,
        NTILE(2) OVER (
            ORDER BY Date
        ) AS period_half
    FROM fitness_daily
    WHERE Calories IS NOT NULL
    GROUP BY Date
)
SELECT
    CASE
        WHEN period_half = 1 THEN 'First half'
        ELSE 'Second half'
    END AS period,
    COUNT(*) AS observed_dates,
    ROUND(AVG(avg_calories), 0) AS avg_daily_calories
FROM dated
GROUP BY period_half
ORDER BY period_half
""",
        "answer": lambda row: (
            f"{row['period']} of the observed period averaged "
            f"{row['avg_daily_calories']:,.0f} kcal across "
            f"{int(row['observed_dates']):,} dates."
        ),
    },
}
