
import base64
from pathlib import Path

import streamlit as st
import pandas as pd

from utils.data import (
    load_data,
    ensure_database,
)
from utils.sql import (
    run_query,
    schema_info,
    EXAMPLES,
    BUSINESS_QUESTIONS,
    QUERY_TIMEOUT_SECONDS,
    MAX_QUERY_CHARS,
    DEFAULT_QUERY_LIMIT,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SQL Playground",
    page_icon="▣",
    layout="wide",
)


# ============================================================
# HTML RENDERING
# ============================================================

def render_html(html: str) -> None:
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(
            html,
            unsafe_allow_html=True,
        )


# ============================================================
# STYLING
# ============================================================

render_html(
    """
    <style>

    .block-container {
        padding-top: 5.25rem !important;
        padding-bottom: 3rem !important;
        max-width: 1500px !important;
    }

    h1, h2, h3 {
        letter-spacing: -0.025em;
    }

    .sql-hero {
        width: 100%;
        box-sizing: border-box;
        background:
            linear-gradient(
                115deg,
                #1a2638 0%,
                #18202d 34%,
                #30190f 66%,
                #8f2806 100%
            );
        border: 1px solid rgba(255,255,255,0.13);
        border-radius: 16px;
        padding: 25px 26px 24px 26px;
        margin: 0.2rem 0 20px 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    .sql-hero-eyebrow {
        color: #ff6419;
        font-size: 0.56rem;
        font-weight: 900;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .sql-hero-row {
        display: flex;
        align-items: center;
        gap: 11px;
    }

    .sql-hero-logo {
        width: 42px;
        height: 42px;
        flex: 0 0 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        overflow: hidden;
        background: #fc5200;
    }

    .sql-hero-logo img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
    }

    .sql-hero-title {
        color: #ffffff;
        font-size: clamp(2.25rem, 3.15vw, 3.2rem);
        font-weight: 900;
        letter-spacing: -2.1px;
        line-height: 1;
        margin: 0;
    }

    .sql-hero-title-accent {
        color: #fc5200;
    }

    .sql-hero-description {
        color: #aab2bd;
        font-size: 0.76rem;
        line-height: 1.6;
        max-width: 1150px;
        margin-top: 13px;
    }

    .section-eyebrow {
        color: #ff6419 !important;
        font-size: 0.56rem !important;
        font-weight: 900 !important;
        letter-spacing: 0.15em !important;
        line-height: 1.2 !important;
        text-transform: uppercase !important;
        margin: 0 0 7px 0 !important;
    }

    .section-shell {
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 15px;
        background: rgba(12,14,19,0.72);
        padding: 18px;
        margin-bottom: 14px;
    }

    .section-title {
        color: #f5f5f5 !important;
        font-size: 1.32rem !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
        margin: 0 0 6px 0 !important;
    }

    .section-description {
        color: rgba(255,255,255,0.62) !important;
        font-size: 0.78rem !important;
        line-height: 1.5 !important;
        margin: 0 !important;
    }

    .readout {
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 15px;
        background: rgba(12,14,19,0.72);
        padding: 18px;
        margin-bottom: 16px;
    }

    .readout-title {
        color: #f3f3f3 !important;
        font-size: 0.98rem !important;
        font-weight: 800 !important;
        line-height: 1.25 !important;
        margin: 0 0 7px 0 !important;
    }

    .readout-copy {
        color: rgba(255,255,255,0.61);
        font-size: 0.76rem;
        line-height: 1.55;
        margin: 0;
    }

    .kpi-card {
        background: #0d0f14;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 12px;
        padding: 13px 15px;
        min-height: 84px;
    }

    .kpi-label {
        color: rgba(255,255,255,0.52);
        font-size: 0.59rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        margin-bottom: 8px;
    }

    .kpi-value {
        color: #f3f3f3;
        font-size: 1.46rem;
        line-height: 1;
        font-weight: 750;
        margin-bottom: 7px;
    }

    .kpi-help {
        color: rgba(255,255,255,0.42);
        font-size: 0.61rem;
        line-height: 1.28;
    }

    .answer-card {
        background:
            linear-gradient(
                135deg,
                rgba(45,24,14,0.74),
                rgba(15,17,22,0.94)
            );
        border-left: 3px solid #ff6419;
        border-top: 1px solid rgba(255,100,25,0.16);
        border-right: 1px solid rgba(255,255,255,0.06);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        border-radius: 0 9px 9px 0;
        padding: 12px 14px;
        margin: 12px 0 12px 0;
    }

    .answer-label {
        color: #ff6419;
        font-size: 0.50rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .answer-copy {
        color: rgba(255,255,255,0.86);
        font-size: 0.70rem;
        line-height: 1.48;
        margin: 0;
    }

    .interpretation {
        border-left: 3px solid #ff6419;
        background: #101217;
        border-radius: 0 10px 10px 0;
        padding: 12px 14px;
        margin: 14px 0;
    }

    .interpretation-title {
        color: #f2f2f2;
        font-size: 0.71rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .interpretation-copy {
        color: rgba(255,255,255,0.59);
        font-size: 0.67rem;
        line-height: 1.45;
        margin: 0;
    }

    .business-copy {
        color: rgba(255,255,255,0.62);
        font-size: 0.72rem;
        line-height: 1.55;
        margin: 0;
    }

    /* --------------------------------------------------------
       Sidebar navigation
       -------------------------------------------------------- */

    [data-testid="stSidebar"] {
        background: #080a0e !important;
    }

    [data-testid="stSidebarNav"] {
        padding-top: 0.35rem !important;
    }

    [data-testid="stSidebarNav"] a {
        border-radius: 8px !important;
        margin: 4px 10px !important;
        padding: 0 12px !important;
        min-height: 38px !important;
        height: 38px !important;
        color: rgba(255,255,255,0.72) !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        color: #ffffff !important;
        background: rgba(255,100,25,0.08) !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        color: #ffffff !important;
        background: rgba(255,100,25,0.14) !important;
        border: 1px solid #ff6419 !important;
        box-shadow: inset 4px 0 0 #ff6419 !important;
    }

    .sidebar-insight-shell {
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 11px;
        background: #0f1217;
        padding: 12px;
        margin-top: 12px;
    }

    .sidebar-insight-eyebrow {
        color: #ff6419;
        font-size: 0.50rem;
        font-weight: 900;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 7px;
    }

    .sidebar-insight-question {
        color: rgba(255,255,255,0.62);
        font-size: 0.58rem;
        line-height: 1.35;
        margin-bottom: 9px;
    }

    .sidebar-kpi {
        background: #0a0c10;
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 8px;
        padding: 10px;
    }

    .sidebar-kpi-label {
        color: rgba(255,255,255,0.38);
        font-size: 0.46rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .sidebar-kpi-value {
        color: #ffffff;
        font-size: 1.08rem;
        font-weight: 850;
        line-height: 1.05;
        margin-bottom: 4px;
    }

    .sidebar-kpi-help {
        color: rgba(255,255,255,0.32);
        font-size: 0.47rem;
        line-height: 1.35;
    }

    .sidebar-status {
        color: rgba(255,255,255,0.29);
        font-size: 0.46rem;
        line-height: 1.35;
        margin-top: 7px;
    }

    .governance {
        background: rgba(102,103,17,0.42);
        border: 1px solid rgba(180,180,70,0.12);
        border-radius: 10px;
        padding: 14px 16px;
        color: rgba(255,255,255,0.73);
        font-size: 0.70rem;
        line-height: 1.5;
        margin-top: 16px;
    }

    .governance strong {
        color: #ffffff;
    }

    .helper {
        color: rgba(255,255,255,0.46);
        font-size: 0.67rem;
        line-height: 1.45;
    }

    </style>
    """
)


# ============================================================
# LOAD DATA / DATABASE
# ============================================================

try:
    df = load_data()
except Exception as exc:
    st.error(
        f"Unable to load the fitness dataset: {exc}"
    )
    st.stop()

df = st.session_state.get(
    "global_filtered",
    df,
)

if df.empty:
    st.error(
        "The current analytical dataset contains no rows."
    )
    st.stop()

db_path = ensure_database(
    df
)

schema = schema_info(
    db_path
)

if schema is None or schema.empty:
    schema = pd.DataFrame(
        columns=[
            "Table",
            "Column",
            "Type",
            "Nullable",
            "Primary Key",
        ]
    )


# ============================================================
# METADATA
# ============================================================

tables = (
    schema["Table"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .tolist()
    if "Table" in schema.columns
    else []
)

table_count = len(tables)
column_count = len(schema)
row_count = len(df)


# ============================================================
# LOGO
# ============================================================

ROOT_DIR = Path(
    __file__
).resolve().parent.parent

LOGO_PATH = (
    ROOT_DIR
    / "images"
    / "strava_logo.png"
)

logo_html = ""

if LOGO_PATH.exists():

    try:

        logo_bytes = LOGO_PATH.read_bytes()

        logo_b64 = base64.b64encode(
            logo_bytes
        ).decode(
            "utf-8"
        )

        logo_html = (
            '<img '
            f'src="data:image/png;base64,{logo_b64}" '
            'alt="Strava logo">'
        )

    except Exception:
        logo_html = ""


# ============================================================
# HERO
# ============================================================

render_html(
    f"""
    <div class="sql-hero">

        <div class="sql-hero-eyebrow">
            HOME&nbsp;&nbsp;•&nbsp;&nbsp;SQL PLAYGROUND
        </div>

        <div class="sql-hero-row">

            <div class="sql-hero-logo">
                {logo_html}
            </div>

            <div class="sql-hero-title">
                <span class="sql-hero-title-accent">SQL</span>
                <span> Playground</span>
            </div>

        </div>

        <div class="sql-hero-description">
            Executive-ready business questions with SQL-backed answers,
            followed by a controlled read-only workspace for deeper analysis.
        </div>

    </div>
    """
)



# ============================================================
# EXECUTIVE READOUT
# ============================================================

render_html(
    """
    <div class="readout">

        <div class="section-eyebrow">
            EXECUTIVE READOUT
        </div>

        <div class="readout-title">
            Start with the business question, then inspect the evidence
        </div>

        <p class="readout-copy">
            Select a question below. Reveal the SQL used to answer it,
            run that query, and inspect the returned evidence. The same
            read-only analytical database powers the executive questions
            and the custom SQL workspace.
        </p>

    </div>
    """
)


# ============================================================
# KPI STRIP
# ============================================================

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Participants</div>
            <div class="kpi-value">{df["Id"].nunique():,}</div>
            <div class="kpi-help">Unique participant identifiers</div>
        </div>
        """
    )

with k2:
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Participant-days</div>
            <div class="kpi-value">{row_count:,}</div>
            <div class="kpi-help">Observed participant-day records</div>
        </div>
        """
    )

with k3:
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Tables</div>
            <div class="kpi-value">{table_count:,}</div>
            <div class="kpi-help">Tables exposed through SQLite</div>
        </div>
        """
    )

with k4:
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">SQL access</div>
            <div class="kpi-value">READ-ONLY</div>
            <div class="kpi-help">
                {DEFAULT_QUERY_LIMIT:,} rows · {QUERY_TIMEOUT_SECONDS:.1f}s timeout
            </div>
        </div>
        """
    )


# ============================================================
# DYNAMIC SIDEBAR KPI
# ============================================================

def sidebar_kpi_from_result(
    question_key: str,
    result: pd.DataFrame,
):
    """
    Return one compact KPI that represents the main useful result
    from the selected CEO/business question.
    """

    if result is None or result.empty:
        return (
            "Result",
            "—",
            "No result returned.",
        )

    row = result.iloc[0]

    if question_key == "q1":
        return (
            "10K benchmark",
            f"{float(row['pct_days_meeting_10k']):.1f}%",
            "Measured participant-days meeting 10K",
        )

    if question_key == "q2":
        return (
            "Top average steps",
            f"{float(row['avg_steps']):,.0f}",
            f"Participant {row['Id']}",
        )

    if question_key == "q3":
        return (
            "Peak average calories",
            f"{float(row['avg_calories']):,.0f}",
            (
                f"{pd.to_datetime(row['Date']):%d %b %Y}"
                " · kcal"
            ),
        )

    if question_key == "q4":
        return (
            "Average calories",
            f"{float(row['avg_calories']):,.0f}",
            str(row["activity_group"]),
        )

    if question_key == "q5":
        return (
            "Sleep coverage",
            f"{float(row['sleep_coverage_pct']):.1f}%",
            "Records with measured sleep duration",
        )

    if question_key == "q6":
        return (
            "Highest sedentary time",
            f"{float(row['avg_sedentary_minutes']):,.0f}",
            f"{pd.to_datetime(row['Date']):%d %b %Y} · minutes",
        )

    if question_key == "q7":
        return (
            "Average steps",
            f"{float(row['avg_steps']):,.0f}",
            str(row["day_type"]),
        )

    if question_key == "q8":
        return (
            "Average recorded sleep",
            f"{float(row['avg_sleep_hours']):.2f} h",
            str(row["activity_group"]),
        )

    if question_key == "q9":
        return (
            "Activity variability",
            f"{float(row['average_activity_cv_pct']):.1f}%",
            "Average within-participant variation",
        )

    if question_key == "q10":
        return (
            "Average daily calories",
            f"{float(row['avg_daily_calories']):,.0f}",
            f"{row['period']} · kcal",
        )

    return (
        "Key result",
        "—",
        "See the answer on the main page.",
    )


# ============================================================
# CEO / BUSINESS QUESTIONS
# ============================================================

render_html(
    """
    <div class="section-shell">

        <div class="section-eyebrow">
            EXECUTIVE BUSINESS QUESTIONS
        </div>

        <div class="section-title">
            CEO & Business Questions
        </div>

        <div class="section-description">
            Choose a business question, reveal the underlying SQL,
            run it, and review the answer with supporting evidence.
        </div>

    </div>
    """
)


question_options = {
    key: value["title"]
    for key, value in BUSINESS_QUESTIONS.items()
}


selected_question_key = st.selectbox(
    "Select a business question",
    options=list(question_options.keys()),
    format_func=lambda key: question_options[key],
    key="ceo_business_question",
)


if "ceo_last_question" not in st.session_state:
    st.session_state["ceo_last_question"] = (
        selected_question_key
    )
    st.session_state["ceo_query_ran"] = False
    st.session_state["ceo_sql_visible"] = False
    st.session_state["ceo_sidebar_kpi"] = None

elif (
    st.session_state["ceo_last_question"]
    != selected_question_key
):

    st.session_state["ceo_last_question"] = (
        selected_question_key
    )
    st.session_state["ceo_query_ran"] = False
    st.session_state["ceo_sql_visible"] = False
    st.session_state["ceo_sidebar_kpi"] = None


selected_question = BUSINESS_QUESTIONS[
    selected_question_key
]


# ------------------------------------------------------------
# Controls
# ------------------------------------------------------------

control_left, control_right = st.columns(
    [1, 1],
    gap="medium",
)


with control_left:

    if st.button(
        (
            "Hide SQL"
            if st.session_state["ceo_sql_visible"]
            else "Show SQL"
        ),
        use_container_width=True,
        key=f"show_sql_button_{selected_question_key}",
    ):

        st.session_state["ceo_sql_visible"] = (
            not st.session_state["ceo_sql_visible"]
        )


with control_right:

    if st.button(
        "Run query",
        type="primary",
        use_container_width=True,
        key=f"run_ceo_question_{selected_question_key}",
    ):

        st.session_state["ceo_query_ran"] = True
        st.session_state["ceo_sidebar_kpi"] = None


# ------------------------------------------------------------
# SQL
# ------------------------------------------------------------

if st.session_state["ceo_sql_visible"]:

    st.code(
        selected_question["sql"].strip(),
        language="sql",
    )


# ------------------------------------------------------------
# ANSWER
# ------------------------------------------------------------

if st.session_state["ceo_query_ran"]:

    try:

        result = run_query(
            db_path,
            selected_question["sql"],
            limit=50,
            timeout_seconds=QUERY_TIMEOUT_SECONDS,
            query_type="business_question",
            context=selected_question["title"],
        )

        if result.empty:

            render_html(
                """
                <div class="answer-card">

                    <div class="answer-label">
                        SQL-BACKED ANSWER
                    </div>

                    <p class="answer-copy">
                        No records were returned for this question.
                    </p>

                </div>
                """
            )

        else:

            first_row = result.iloc[0]

            try:
                answer = selected_question[
                    "answer"
                ](
                    first_row
                )
            except Exception:
                answer = (
                    "The query returned evidence, but the "
                    "executive summary could not be formatted."
                )

            st.session_state["ceo_sidebar_kpi"] = (
                sidebar_kpi_from_result(
                    selected_question_key,
                    result,
                )
            )

            execution_ms = result.attrs.get(
                "sql_execution_ms"
            )

            query_hash_value = result.attrs.get(
                "sql_query_hash",
                "—",
            )

            render_html(
                f"""
                <div class="answer-card">

                    <div class="answer-label">
                        SQL-BACKED ANSWER
                    </div>

                    <p class="answer-copy">
                        {answer}
                    </p>

                    <div class="helper">
                        Query execution:
                        {execution_ms:.0f} ms
                        · Audit ID:
                        {query_hash_value}
                    </div>

                </div>
                """
            )

            with st.expander(
                "View supporting evidence",
                expanded=True,
            ):

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True,
                )

    except Exception as exc:

        st.error(
            f"Query could not be executed: {exc}"
        )


# ============================================================
# DYNAMIC SIDEBAR
# ============================================================

with st.sidebar:

    render_html(
        """
        <div style="
            height:1px;
            background:rgba(255,255,255,0.12);
            margin:14px 0 13px 0;
        "></div>
        """
    )

    sidebar_kpi = st.session_state.get(
        "ceo_sidebar_kpi"
    )

    if sidebar_kpi:

        label, value, help_text = sidebar_kpi

        render_html(
            f"""
            <div class="sidebar-insight-shell">

                <div class="sidebar-insight-eyebrow">
                    QUERY INSIGHT
                </div>

                <div class="sidebar-insight-question">
                    {selected_question["title"]}
                </div>

                <div class="sidebar-kpi">

                    <div class="sidebar-kpi-label">
                        {label}
                    </div>

                    <div class="sidebar-kpi-value">
                        {value}
                    </div>

                    <div class="sidebar-kpi-help">
                        {help_text}
                    </div>

                </div>

            </div>
            """
        )

    else:

        render_html(
            """
            <div class="sidebar-insight-shell">

                <div class="sidebar-insight-eyebrow">
                    QUERY INSIGHT
                </div>

                <div class="sidebar-kpi">

                    <div class="sidebar-kpi-label">
                        Status
                    </div>

                    <div class="sidebar-kpi-value">
                        READY
                    </div>

                    <div class="sidebar-kpi-help">
                        Run a CEO/business question to populate
                        the key-result card.
                    </div>

                </div>

            </div>
            """
        )


# ============================================================
# EXECUTIVE INTERPRETATION
# ============================================================

render_html(
    """
    <div class="interpretation">

        <div class="interpretation-title">
            Executive interpretation
        </div>

        <p class="interpretation-copy">
            These are descriptive SQL findings from the observed analytical
            population. They can support KPI validation, management discussion,
            segment review, and follow-up analysis. They should be interpreted
            within the observed period, population, filters, and data coverage.
        </p>

    </div>
    """
)


# ============================================================
# CUSTOM SQL WORKSPACE
# ============================================================

render_html(
    """
    <div class="section-shell">

        <div class="section-eyebrow">
            ANALYTICAL WORKSPACE
        </div>

        <div class="section-title">
            SQL Query Workspace
        </div>

        <div class="section-description">
            Build and execute your own read-only analytical queries against
            the same database used by the executive questions.
        </div>

    </div>
    """
)


left, right = st.columns(
    [1.75, 1],
    gap="large",
)


with left:

    example_options = (
        ["Custom query"]
        + list(EXAMPLES.keys())
    )

    example = st.selectbox(
        "Start from an example",
        example_options,
        key="sql_example",
    )

    default_sql = EXAMPLES.get(
        example,
        "SELECT *\nFROM fitness_daily\nLIMIT 50;",
    )

    query = st.text_area(
        "SQL editor",
        value=default_sql,
        height=270,
        max_chars=MAX_QUERY_CHARS,
        key="sql_editor",
        help=(
            "Use one read-only SELECT or WITH ... SELECT statement. "
            f"Maximum {MAX_QUERY_CHARS:,} characters and "
            f"{QUERY_TIMEOUT_SECONDS:.1f}s execution time."
        ),
    )

    run = st.button(
        "Run query",
        type="primary",
        use_container_width=True,
        key="run_sql_query",
    )


with right:

    render_html(
        """
        <div class="interpretation">

            <div class="interpretation-title">
                Business use
            </div>

            <p class="interpretation-copy">
                Use the custom workspace when a question goes beyond the
                predefined executive views, such as KPI validation,
                segment analysis, operational checks, or ad-hoc investigation.
            </p>

        </div>
        """
    )

    st.markdown(
        "**Query controls**"
    )

    render_html(
        f"""
        <div class="helper">
            Read-only analytical queries<br>
            SELECT and WITH ... SELECT supported<br>
            Maximum {MAX_QUERY_CHARS:,} query characters<br>
            Maximum {DEFAULT_QUERY_LIMIT:,} returned rows<br>
            {QUERY_TIMEOUT_SECONDS:.1f}s query timeout<br>
            Accepted and rejected queries are audit logged
        </div>
        """
    )


# ============================================================
# QUERY RESULTS
# ============================================================

if run:

    render_html(
        """
        <div class="section-shell">

            <div class="section-eyebrow">
                QUERY OUTPUT
            </div>

            <div class="section-title">
                Query Results & Export
            </div>

            <div class="section-description">
                Results returned directly by the hardened, read-only
                analytical database connection.
            </div>

        </div>
        """
    )

    try:

        result = run_query(
            db_path,
            query,
            limit=DEFAULT_QUERY_LIMIT,
            timeout_seconds=QUERY_TIMEOUT_SECONDS,
            query_type="custom",
            context="Custom SQL workspace",
        )

        result_rows = len(
            result
        )

        result_columns = len(
            result.columns
        )

        execution_ms = result.attrs.get(
            "sql_execution_ms",
            0.0,
        )

        query_hash_value = result.attrs.get(
            "sql_query_hash",
            "—",
        )

        r1, r2, r3, r4 = st.columns(4)

        with r1:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Returned rows</div>
                    <div class="kpi-value">{result_rows:,}</div>
                    <div class="kpi-help">Records returned by the query</div>
                </div>
                """
            )

        with r2:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Returned columns</div>
                    <div class="kpi-value">{result_columns:,}</div>
                    <div class="kpi-help">Fields included in the result</div>
                </div>
                """
            )

        with r3:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Execution time</div>
                    <div class="kpi-value">{execution_ms:.0f} ms</div>
                    <div class="kpi-help">Measured database execution time</div>
                </div>
                """
            )

        with r4:
            render_html(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Audit ID</div>
                    <div class="kpi-value">{query_hash_value}</div>
                    <div class="kpi-help">Short query identifier for the audit log</div>
                </div>
                """
            )

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download results as CSV",
            result.to_csv(
                index=False
            ),
            "sql_query_results.csv",
            "text/csv",
            use_container_width=True,
        )

    except Exception as exc:

        st.error(
            f"Query could not be executed: {exc}"
        )


# ============================================================
# DATABASE SCHEMA
# ============================================================

render_html(
    """
    <div class="section-shell">

        <div class="section-eyebrow">
            DATA STRUCTURE
        </div>

        <div class="section-title">
            Database Schema
        </div>

        <div class="section-description">
            Inspect the available fields before creating your own
            analytical questions.
        </div>

    </div>
    """
)


s1, s2, s3, s4 = st.columns(4)

with s1:
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Tables</div>
            <div class="kpi-value">{table_count:,}</div>
            <div class="kpi-help">Database tables currently exposed</div>
        </div>
        """
    )

with s2:
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Fields</div>
            <div class="kpi-value">{column_count:,}</div>
            <div class="kpi-help">Fields described in the schema</div>
        </div>
        """
    )

with s3:
    render_html(
        """
        <div class="kpi-card">
            <div class="kpi-label">Primary source</div>
            <div class="kpi-value">FITNESS</div>
            <div class="kpi-help">Validated fitness analytical dataset</div>
        </div>
        """
    )

with s4:
    render_html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">SQL access</div>
            <div class="kpi-value">SELECT</div>
            <div class="kpi-help">
                Read-only connection · {QUERY_TIMEOUT_SECONDS:.1f}s timeout
            </div>
        </div>
        """
    )


if tables:

    for table in tables:

        table_schema = schema[
            schema["Table"].astype(str)
            == str(table)
        ].copy()

        display_columns = [
            column
            for column in [
                "Column",
                "Type",
                "Nullable",
                "Primary Key",
            ]
            if column in table_schema.columns
        ]

        with st.expander(
            f"{table} · {len(table_schema):,} fields",
            expanded=(len(tables) == 1),
        ):

            st.dataframe(
                table_schema[
                    display_columns
                ],
                use_container_width=True,
                hide_index=True,
            )

else:

    st.info(
        "No database schema information is currently available."
    )


# ============================================================
# BUSINESS USE & GOVERNANCE
# ============================================================

render_html(
    """
    <div class="section-shell">

        <div class="section-eyebrow">
            BUSINESS USE
        </div>

        <div class="section-title">
            How to use SQL in executive reporting
        </div>

        <div class="section-description">
            The SQL layer should provide reproducible evidence underneath
            the executive dashboard rather than replace business judgment.
        </div>

        <p class="business-copy">
            <strong>Recommended workflow</strong><br><br>
            Start with a business question, confirm the population and period,
            inspect the schema, execute a focused query, review the returned
            evidence, and use the result to support a management discussion
            or dashboard KPI.
        </p>

    </div>
    """
)


render_html(
    f"""
    <div class="governance">

        <strong>SQL governance:</strong>
        This playground uses a read-only SQLite connection with database-level
        write blocking, a SQLite authorizer, a single-statement SELECT/WITH policy, a
        {MAX_QUERY_CHARS:,}-character query limit, a {DEFAULT_QUERY_LIMIT:,}-row
        output limit, a {QUERY_TIMEOUT_SECONDS:.1f}-second execution timeout,
        and an audit log of accepted and rejected queries.

    </div>
    """
)
