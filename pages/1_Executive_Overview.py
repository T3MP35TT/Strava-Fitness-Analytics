import base64
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from textwrap import dedent

# PAGE CONFIG
st.set_page_config(
    page_title="Executive Overview | Strava Fitness Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# GLOBAL STYLING
st.html(
    dedent(
        """
        <style>
        :root {
            --fitness-orange: #FC5200;
            --fitness-orange-light: #ff7a45;
            --fitness-bg: #0b0d10;
            --fitness-surface: #11141a;
            --fitness-surface-2: #181b22;
            --fitness-border: #292d36;
            --fitness-text: #f5f7fa;
            --fitness-muted: #a7adb8;
            --fitness-blue: #62b7ff;
        }
        /* ====================================================
        APP
        ==================================================== */
        .stApp {
            background:
                radial-gradient(
                    circle at 84% 3%,
                    rgba(252,82,0,0.085),
                    transparent 25%
                ),
                radial-gradient(
                    circle at 12% 15%,
                    rgba(252,82,0,0.025),
                    transparent 28%
                ),
                var(--fitness-bg);
            color: var(--fitness-text);
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        /* ====================================================
        SIDEBAR
        ==================================================== */
        [data-testid="stSidebar"] {
            background: #0b0d10 !important;
            border-right: 1px solid #252931 !important;
        }
        [data-testid="stSidebar"] > div:first-child,
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"] {
            background: #0b0d10 !important;
        }
        [data-testid="stSidebarNav"] {
            padding-top: 0.35rem;
        }
        [data-testid="stSidebarNav"] ul {
            padding-top: 0;
        }
        [data-testid="stSidebarNav"] li {
            margin: 0;
        }
        [data-testid="stSidebarNav"] a {
            color: #f0f2f5 !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            border-radius: 7px !important;
            margin: 2px 8px !important;
            padding: 6px 10px !important;
            min-height: 28px !important;
            transition:
                background 0.15s ease,
                border 0.15s ease !important;
        }
        [data-testid="stSidebarNav"] a:hover {
            color: #ffffff !important;
            background: rgba(252,82,0,0.08) !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            color: #ffffff !important;
            background: rgba(252,82,0,0.16) !important;
            border: 1px solid rgba(252,82,0,0.80) !important;
            box-shadow: inset 3px 0 0 #FC5200 !important;
            padding: 5px 9px !important;
            min-height: 28px !important;
            margin: 2px 22px 2px 8px !important;
            font-size: 11.5px !important;
        }
        /* ====================================================
        SIDEBAR CARD
        ==================================================== */
        .fitness-sidebar-card {
            border: 1px solid #292d36;
            border-radius: 10px;
            background: #11141a;
            padding: 12px 13px;
            margin: 0;
        }
        .fitness-sidebar-card .label {
            color: var(--fitness-orange);
            font-size: 9px;
            font-weight: 850;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
        .fitness-sidebar-card .heading {
            color: #f5f7fa;
            font-size: 11px;
            font-weight: 800;
            margin-bottom: 5px;
        }
        .fitness-sidebar-card .copy {
            color: #8e96a3;
            font-size: 9.5px;
            line-height: 1.45;
        }
        /* ====================================================
        HERO
        ==================================================== */
        .executive-hero {
            position: relative;
            isolation: isolate;
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 20px;
            padding: 30px 36px;
            margin: 6px 0 22px 0;
            /* Same frosted / blurred glass background treatment as app.py. */
            background:
                linear-gradient(
                    110deg,
                    rgba(21,29,40,0.60),
                    rgba(14,18,26,0.52) 48%,
                    rgba(39,20,13,0.48) 100%
                );
            box-shadow:
                0 18px 48px rgba(0,0,0,0.34),
                inset 0 1px 0 rgba(255,255,255,0.07);
            overflow: hidden;
            backdrop-filter:
                blur(24px)
                saturate(145%);
            -webkit-backdrop-filter:
                blur(24px)
                saturate(145%);
        }
        /* Primary blurred blue / orange color field from app.py. */
        .executive-hero::before {
            content: "";
            position: absolute;
            z-index: 0;
            left: -8%;
            top: -90%;
            width: 116%;
            height: 280%;
            background:
                radial-gradient(
                    ellipse at 12% 50%,
                    rgba(38,58,83,0.95) 0%,
                    rgba(38,58,83,0.68) 19%,
                    rgba(38,58,83,0.22) 39%,
                    transparent 62%
                ),
                radial-gradient(
                    ellipse at 83% 43%,
                    rgba(255,72,8,0.92) 0%,
                    rgba(255,72,8,0.66) 18%,
                    rgba(255,72,8,0.25) 39%,
                    transparent 63%
                ),
                radial-gradient(
                    ellipse at 52% 92%,
                    rgba(17,28,43,0.92) 0%,
                    rgba(17,28,43,0.48) 30%,
                    transparent 65%
                );
            filter: blur(42px);
            transform: scale(1.05);
            opacity: 0.92;
            pointer-events: none;
        }
        /* Secondary soft orange light on the right, from app.py. */
        .executive-hero::after {
            content: "";
            position: absolute;
            z-index: 1;
            width: 500px;
            height: 500px;
            right: -230px;
            top: -275px;
            border-radius: 50%;
            background:
                radial-gradient(
                    circle,
                    rgba(255,88,18,0.62) 0%,
                    rgba(255,88,18,0.34) 25%,
                    rgba(255,88,18,0.12) 46%,
                    transparent 72%
                );
            filter: blur(34px);
            opacity: 0.92;
            pointer-events: none;
        }
        /* Keep the existing hero content above the visual layers. */
        .executive-hero > * {
            position: relative;
            z-index: 3;
        }
        .executive-hero-top {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 18px;
            margin-bottom: 14px;
        }
        .executive-brand-logo {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;
            line-height: 1;
        }
        .executive-brand-logo img {
            display: block;
            width: auto;
            height: 50px;
            max-width: 180px;
            object-fit: contain;
        }
        .executive-badge {
            color: #b8bec8;
            font-size: 11px;
            font-weight: 750;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }
        .executive-title {
            color: #ffffff;
            font-size: clamp(2rem, 3.6vw, 3.1rem);
            font-weight: 900;
            letter-spacing: -1.7px;
            line-height: 1.0;
            margin-bottom: 0;
            white-space: nowrap;
        }
        .executive-title-orange {
            color: var(--fitness-orange);
        }
        @media (max-width: 760px) {
            .executive-hero-top {
                gap: 12px;
                align-items: center;
            }
            .executive-brand-logo img {
                height: 42px;
                max-width: 150px;
            }
        }
        .executive-description {
            max-width: 900px;
            color: #aeb5c0;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 14px;
        }
        .executive-period {
            color: #7f8794;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.4px;
        }
        /* ====================================================
        SECTION HEADERS
        ==================================================== */
        .section-header {
            margin-bottom: 17px;
        }
        .section-label {
            color: var(--fitness-orange);
            font-size: 9px;
            font-weight: 900;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
        .section-title {
            color: #ffffff;
            font-size: 24px;
            font-weight: 850;
            letter-spacing: -0.6px;
            line-height: 1.1;
            margin-bottom: 6px;
        }
        .section-copy {
            color: #aeb5c0;
            font-size: 12px;
            line-height: 1.55;
        }
        /* ====================================================
        MAIN EXECUTIVE RECTANGLES
        ==================================================== */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #292d36 !important;
            border-radius: 16px !important;
            background: rgba(15,17,22,0.90) !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            border-radius: 16px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div > div {
            gap: 0.55rem !important;
        }
        .executive-container-top {
            margin-top: 0;
        }
        /* ====================================================
        KPI CARDS
        ==================================================== */
        .fitness-kpi {
            position: relative;
            overflow: hidden;
            border: 1px solid #2b303a;
            border-radius: 13px;
            background:
                radial-gradient(
                    circle at 100% 0%,
                    rgba(252,82,0,0.075),
                    transparent 38%
                ),
                linear-gradient(
                    145deg,
                    #15181e 0%,
                    #101217 100%
                );
            padding: 16px 17px 15px 17px;
            min-height: 112px;
            box-shadow:
                0 9px 24px rgba(0,0,0,0.16);
            transition:
                transform 0.15s ease,
                border-color 0.15s ease,
                box-shadow 0.15s ease;
        }
        .fitness-kpi::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #333944;
        }
        .fitness-kpi.kpi-accent::before {
            background: var(--fitness-orange);
        }
        .fitness-kpi:hover {
            transform: translateY(-1px);
            border-color: #3a404b;
            box-shadow:
                0 12px 28px rgba(0,0,0,0.20);
        }
        .fitness-kpi-label {
            color: #8e96a3;
            font-size: 8.5px;
            font-weight: 850;
            letter-spacing: 1.0px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .fitness-kpi-value {
            color: #ffffff;
            font-size: 27px;
            font-weight: 900;
            letter-spacing: -0.8px;
            line-height: 1.0;
        }
        .fitness-kpi-accent {
            color: var(--fitness-orange);
        }
        .fitness-kpi-sub {
            color: #707887;
            font-size: 8.8px;
            line-height: 1.35;
            margin-top: 9px;
        }
        /* ====================================================
        OPERATING PICTURE CARDS
        ==================================================== */
        .operating-card {
            border: 1px solid #292d36;
            border-radius: 13px;
            background:
                linear-gradient(
                    145deg,
                    #14171d,
                    #101217
                );
            padding: 17px 18px;
            min-height: 185px;
        }
        .operating-card-label {
            color: var(--fitness-orange);
            font-size: 9px;
            font-weight: 900;
            letter-spacing: 1.3px;
            text-transform: uppercase;
            margin-bottom: 9px;
        }
        .operating-card-title {
            color: #ffffff;
            font-size: 18px;
            font-weight: 850;
            letter-spacing: -0.3px;
            margin-bottom: 4px;
        }
        .operating-card-value {
            color: #ffffff;
            font-size: 28px;
            font-weight: 900;
            letter-spacing: -0.8px;
            margin-top: 11px;
        }
        .operating-card-value.orange {
            color: var(--fitness-orange);
        }
        .operating-card-copy {
            color: #8f97a5;
            font-size: 10px;
            line-height: 1.45;
            margin-top: 4px;
        }
        .operating-divider {
            height: 1px;
            background: #292d36;
            margin: 13px 0;
        }
        .operating-stat {
            color: #cfd5dd;
            font-size: 10px;
            line-height: 1.55;
        }
        .operating-stat strong {
            color: #ffffff;
        }
        .status-pill {
            display: inline-block;
            margin-top: 10px;
            padding: 4px 8px;
            border-radius: 5px;
            border: 1px solid rgba(252,82,0,0.45);
            background: rgba(252,82,0,0.10);
            color: #ff8b5d;
            font-size: 8px;
            font-weight: 900;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }
        .status-pill.neutral {
            border-color: #39404c;
            background: #181b22;
            color: #aeb5c0;
        }
        /* ====================================================
        FILTERS
        ==================================================== */
        .filter-intro {
            margin-bottom: 9px;
        }
        .filter-label {
            color: var(--fitness-orange);
            font-size: 9px;
            font-weight: 900;
            letter-spacing: 1.4px;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .filter-copy {
            color: #8f97a5;
            font-size: 11px;
            line-height: 1.45;
        }
        [data-testid="stDateInput"],
        [data-testid="stMultiSelect"],
        [data-testid="stSelectbox"] {
            margin-bottom: 4px;
        }
        .filter-status {
            display: flex;
            align-items: center;
            gap: 7px;
            margin-top: 8px;
            padding-top: 9px;
            border-top: 1px solid #252a33;
            color: #747c89;
            font-size: 8.5px;
            line-height: 1.4;
        }
        .filter-status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--fitness-orange);
            box-shadow: 0 0 0 3px rgba(252,82,0,0.10);
            flex: 0 0 auto;
        }
        /* ====================================================
        DATA CONTEXT STRIP
        ==================================================== */
        .data-context {
            border: 1px solid #292d36;
            border-radius: 9px;
            background: #0f1217;
            padding: 9px 12px;
            margin-top: 13px;
            color: #69717e;
            font-size: 9px;
            line-height: 1.4;
        }
        .data-context strong {
            color: #aeb5c0;
        }
        /* ====================================================
        EXECUTIVE CONTEXT CARDS
        ==================================================== */
        .insight-card {
            position: relative;
            overflow: hidden;
            border: 1px solid #2b303a;
            border-radius: 12px;
            background:
                linear-gradient(
                    145deg,
                    #15181e 0%,
                    #101217 100%
                );
            padding: 15px 17px 16px 18px;
            min-height: 116px;

            box-shadow:
                0 8px 22px rgba(0,0,0,0.14);
        }
        .insight-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: var(--fitness-orange);
        }
        .insight-eyebrow {
            color: #7f8794;
            font-size: 8px;
            font-weight: 850;
            letter-spacing: 1.0px;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
        .insight-headline {
            color: #ffffff;
            font-size: 13px;
            font-weight: 800;
            line-height: 1.3;
            margin-bottom: 7px;
        }
        .insight-value {
            color: var(--fitness-orange);
            font-size: 20px;
            font-weight: 900;
            letter-spacing: -0.4px;
            line-height: 1.0;
            margin-bottom: 7px;
        }
        .insight-copy {
            color: #969eab;
            font-size: 9.5px;
            line-height: 1.45;
        }
        .insight-copy strong {
            color: #e7ebf0;
        }
        /* ====================================================
        CHART CONTAINERS
        ==================================================== */
        .chart-section {
            border: 1px solid #292d36;
            border-radius: 16px;
            background: rgba(15,17,22,0.90);
            padding: 20px 22px 16px 22px;
            margin: 16px 0;
        }
        .chart-section-label {
            color: var(--fitness-orange);
            font-size: 9px;
            font-weight: 900;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
        .chart-section-title {
            color: #ffffff;
            font-size: 22px;
            font-weight: 850;
            letter-spacing: -0.5px;
            margin-bottom: 5px;
        }
        .chart-section-copy {
            color: #aeb5c0;
            font-size: 11px;
            line-height: 1.5;
        }
        /* ====================================================
        PLOTLY
        ==================================================== */
        .stPlotlyChart {
            border-radius: 12px;
        }
        </style>
        """
    )
)

# DATA LOCATION
CURRENT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = (
    CURRENT_DIR.parent
    if CURRENT_DIR.name.lower() == "pages"
    else CURRENT_DIR
)

# BRAND ASSET
STRAVA_LOGO_PATH = PROJECT_ROOT / "images" / "strava_logo.png"

def get_logo_data_uri(path):
    if not path.exists():
        return ""
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""

STRAVA_LOGO_URI = get_logo_data_uri(STRAVA_LOGO_PATH)

MASTER_CANDIDATES = [
    PROJECT_ROOT / "data" / "processed" / "fitness_daily_master.csv",
    CURRENT_DIR / "data" / "processed" / "fitness_daily_master.csv",
]

MASTER_CSV = next(
    (
        path
        for path in MASTER_CANDIDATES
        if path.exists()
    ),
    MASTER_CANDIDATES[0],
)

# LOAD MASTER DATA
@st.cache_data(show_spinner=False)
def load_master_data(path_string):
    path = Path(path_string)
    if not path.exists():
        return pd.DataFrame()
    data = pd.read_csv(path)
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(
            data["Date"],
            errors="coerce",
        )
        data = data.dropna(
            subset=["Date"]
        )
    numeric_columns = [
        "TotalSteps",
        "Calories",
        "VeryActiveMinutes",
        "FairlyActiveMinutes",
        "LightlyActiveMinutes",
        "SedentaryMinutes",
        "Total_Active_Minutes",
        "Sleep_Minutes",
        "Time_In_Bed_Minutes",
        "Sleep_Efficiency_Pct",
        "HeartRate_Avg",
        "HeartRate_Min",
        "HeartRate_Max",
        "HeartRate_Median",
        "BMI",
        "Weight_Kg",
    ]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )
    if (
        "Is_Weekend" not in data.columns
        and "Date" in data.columns
    ):
        data["Is_Weekend"] = (
            data["Date"].dt.dayofweek >= 5
        )
    if (
        "Total_Active_Minutes" not in data.columns
    ):
        active_columns = [
            column
            for column in [
                "VeryActiveMinutes",
                "FairlyActiveMinutes",
                "LightlyActiveMinutes",
            ]
            if column in data.columns
        ]
        if active_columns:
            data["Total_Active_Minutes"] = (
                data[active_columns]
                .fillna(0)
                .sum(axis=1)
            )
    if (
        "Meets_10k_Steps" not in data.columns
        and "TotalSteps" in data.columns
    ):
        data["Meets_10k_Steps"] = (
            data["TotalSteps"] >= 10000
        )
    if (
        "Sleep_7h_Target" not in data.columns
        and "Sleep_Minutes" in data.columns
    ):
        data["Sleep_7h_Target"] = (
            data["Sleep_Minutes"] >= 420
        )
    if (
        "Day_Of_Week" not in data.columns
        and "Date" in data.columns
    ):
        data["Day_Of_Week"] = (
            data["Date"].dt.day_name()
        )
    if (
        "Id" in data.columns
        and "Date" in data.columns
    ):
        data = data.sort_values(
            ["Date", "Id"]
        )
    return data.reset_index(drop=True)

df = load_master_data(
    str(MASTER_CSV)
)

# DATA VALIDATION
if df.empty:

    st.error(
        "Master CSV not found or could not be loaded.\n\n"
        f"Expected one of:\n"
        + "\n".join(
            f"- `{path}`"
            for path in MASTER_CANDIDATES
        )
        + "\n\n"
        "This page uses only "
        "`fitness_daily_master.csv`."
    )
    st.stop()

# GLOBAL FILTER
global_filtered = st.session_state.get(
    "global_filtered"
)

if global_filtered is None:
    filtered = df.copy()

else:
    filtered = global_filtered.copy()

if filtered.empty:
    st.warning(
        "No records match the current dashboard filters."
    )
    st.stop()

# HELPERS
def fmt(value, decimals=0):
    if pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f}"

def pct(value, decimals=1):
    if pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}%"

def safe_mean(dataframe, column):
    if column not in dataframe.columns:
        return np.nan
    series = dataframe[column].dropna()
    if series.empty:
        return np.nan
    return series.mean()

def period_label(dataframe):
    if (
        "Date" not in dataframe.columns
        or not dataframe["Date"].notna().any()
    ):
        return "—"
    start = dataframe["Date"].min()
    end = dataframe["Date"].max()
    return (
        f"{start.strftime('%d %b %Y')} "
        f"— "
        f"{end.strftime('%d %b %Y')}"
    )

# FILTER STATE
filter_base = filtered.copy()

def _initialize_filter_state(dataframe):
    if "executive_date_filter" not in st.session_state:
        if (
            "Date" in dataframe.columns
            and dataframe["Date"].notna().any()
        ):
            st.session_state["executive_date_filter"] = (
                dataframe["Date"].min().date(),
                dataframe["Date"].max().date(),
            )
        else:
            st.session_state["executive_date_filter"] = None

    if "executive_participant_filter" not in st.session_state:
        st.session_state["executive_participant_filter"] = []

    if "executive_day_type_filter" not in st.session_state:
        st.session_state["executive_day_type_filter"] = "All days"

    if "executive_goal_filter" not in st.session_state:
        st.session_state["executive_goal_filter"] = "All records"

    # Keep stored participant selections valid when a global filter changes.
    if "Id" in dataframe.columns:
        valid_participants = set(
            dataframe["Id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        st.session_state["executive_participant_filter"] = [
            value
            for value in st.session_state["executive_participant_filter"]
            if value in valid_participants
        ]

    # Keep stored dates inside the current global date range.
    if (
        "Date" in dataframe.columns
        and dataframe["Date"].notna().any()
    ):
        min_date = dataframe["Date"].min().date()
        max_date = dataframe["Date"].max().date()
        current_dates = st.session_state.get(
            "executive_date_filter"
        )
        if (
            not isinstance(current_dates, (tuple, list))
            or len(current_dates) != 2
        ):
            current_dates = (min_date, max_date)
        start_date = max(min_date, current_dates[0])
        end_date = min(max_date, current_dates[1])
        if start_date > end_date:
            start_date, end_date = min_date, max_date
        st.session_state["executive_date_filter"] = (
            start_date,
            end_date,
        )
_initialize_filter_state(filter_base)

# APPLY PAGE FILTERS
selected_dates = st.session_state.get(
    "executive_date_filter"
)
selected_participants = st.session_state.get(
    "executive_participant_filter",
    [],
)
day_type = st.session_state.get(
    "executive_day_type_filter",
    "All days",
)
goal_filter = st.session_state.get(
    "executive_goal_filter",
    "All records",
)
page_filtered = filter_base.copy()

# DATE FILTER
if (
    selected_dates
    and isinstance(selected_dates, (tuple, list))
    and len(selected_dates) == 2
    and "Date" in page_filtered.columns
):
    start_date, end_date = selected_dates
    page_filtered = page_filtered[
        page_filtered["Date"].dt.date.between(
            start_date,
            end_date,
        )
    ]

# PARTICIPANT FILTER
if (
    selected_participants
    and "Id" in page_filtered.columns
):
    page_filtered = page_filtered[
        page_filtered["Id"]
        .astype(str)
        .isin(selected_participants)
    ]

# DAY TYPE
if day_type != "All days":
    if "Is_Weekend" in page_filtered.columns:
        if day_type == "Weekdays":
            page_filtered = page_filtered[
                ~page_filtered["Is_Weekend"].fillna(False)
            ]
        else:
            page_filtered = page_filtered[
                page_filtered["Is_Weekend"].fillna(False)
            ]
    elif "Date" in page_filtered.columns:
        if day_type == "Weekdays":
            page_filtered = page_filtered[
                page_filtered["Date"].dt.dayofweek < 5
            ]
        else:
            page_filtered = page_filtered[
                page_filtered["Date"].dt.dayofweek >= 5
            ]

# GOAL FILTER
if (
    goal_filter != "All records"
    and "Meets_10k_Steps" in page_filtered.columns
):
    if goal_filter == "Met 10K":
        page_filtered = page_filtered[
            page_filtered["Meets_10k_Steps"].fillna(False)
        ]
    else:
        page_filtered = page_filtered[
            ~page_filtered["Meets_10k_Steps"].fillna(False)
        ]
if page_filtered.empty:
    st.warning(
        "No records match the selected executive filters."
    )
    st.stop()
filtered = page_filtered.copy()

# APPLY PAGE FILTERS
page_filtered = filtered.copy()

# DATE FILTER
if (
    selected_dates
    and isinstance(
        selected_dates,
        (tuple, list),
    )
    and len(selected_dates) == 2
    and "Date" in page_filtered.columns
):
    start_date, end_date = selected_dates
    page_filtered = page_filtered[
        page_filtered["Date"].dt.date.between(
            start_date,
            end_date,
        )
    ]

# PARTICIPANT FILTER
if (
    selected_participants
    and "Id" in page_filtered.columns
):
    page_filtered = page_filtered[
        page_filtered["Id"]
        .astype(str)
        .isin(selected_participants)
    ]

# DAY TYPE
if day_type != "All days":
    if "Is_Weekend" in page_filtered.columns:
        if day_type == "Weekdays":
            page_filtered = page_filtered[
                ~page_filtered[
                    "Is_Weekend"
                ].fillna(False)
            ]
        else:
            page_filtered = page_filtered[
                page_filtered[
                    "Is_Weekend"
                ].fillna(False)
            ]
    elif "Date" in page_filtered.columns:
        if day_type == "Weekdays":
            page_filtered = page_filtered[
                page_filtered[
                    "Date"
                ].dt.dayofweek < 5
            ]
        else:
            page_filtered = page_filtered[
                page_filtered[
                    "Date"
                ].dt.dayofweek >= 5
            ]

# GOAL FILTER
if (
    goal_filter != "All records"
    and "Meets_10k_Steps"
    in page_filtered.columns
):
    if goal_filter == "Met 10K":
        page_filtered = page_filtered[
            page_filtered[
                "Meets_10k_Steps"
            ].fillna(False)
        ]
    else:
        page_filtered = page_filtered[
            ~page_filtered[
                "Meets_10k_Steps"
            ].fillna(False)
        ]
if page_filtered.empty:
    st.warning(
        "No records match the selected executive filters."
    )
    st.stop()
filtered = page_filtered.copy()

# CURRENT PERIOD
period_start = (
    filtered["Date"].min().strftime("%d %b %Y")
    if (
        "Date" in filtered.columns
        and filtered["Date"].notna().any()
    )
    else "—"
)
period_end = (
    filtered["Date"].max().strftime("%d %b %Y")
    if (
        "Date" in filtered.columns
        and filtered["Date"].notna().any()
    )
    else "—"
)
period_text = (
    f"{period_start} — {period_end}"
)

# EXECUTIVE HERO
st.html(
    f"""
    <div class="executive-hero">
        <div class="executive-badge">
            🏃 &nbsp; HOME • EXECUTIVE OVERVIEW
        </div>
        <div class="executive-hero-top">
            {
                f'<div class="executive-brand-logo"><img src="{STRAVA_LOGO_URI}" alt="Strava" /></div>'
                if STRAVA_LOGO_URI
                else ""
            }
            <div class="executive-title">
                <span class="executive-title-orange">
                    Executive
                </span>
                Overview
            </div>
        </div>
        <div class="executive-description">
            Executive view of participant activity,
            goal attainment, movement behavior,
            calories, and wellness outcomes.
            Detailed analytical views remain available
            through the dashboard navigation.
        </div>
        <div class="executive-period">
            Analysis Period &nbsp;•&nbsp;
            {period_text}
        </div>
    </div>
    """
)

# 1. PERFORMANCE AT A GLANCE
participant_days = len(filtered)
participants = (
    filtered["Id"].nunique()
    if "Id" in filtered.columns
    else np.nan
)
avg_steps = safe_mean(
    filtered,
    "TotalSteps",
)
avg_calories = safe_mean(
    filtered,
    "Calories",
)
goal_rate = (
    filtered["Meets_10k_Steps"].mean() * 100
    if (
        "Meets_10k_Steps" in filtered.columns
        and filtered["Meets_10k_Steps"].notna().any()
    )
    else np.nan
)
with st.container(border=True):
    st.html(
        """
        <div class="section-header">
            <div class="section-label">
                EXECUTIVE SNAPSHOT
            </div>
            <div class="section-title">
                Performance at a glance
            </div>
            <div class="section-copy">
                The core operating measures for the
                currently selected participant-day population.
            </div>
        </div>
        """
    )
    k1, k2, k3, k4, k5 = st.columns(
        5,
        gap="medium",
    )

    # KPI 1
    with k1:
        st.html(
            f"""
            <div class="fitness-kpi">
                <div class="fitness-kpi-label">
                    Participants
                </div>
                <div class="fitness-kpi-value">
                    {fmt(participants)}
                </div>
                <div class="fitness-kpi-sub">
                    Unique participants in current view
                </div>
            </div>
            """
        )

    # KPI 2
    with k2:
        st.html(
            f"""
            <div class="fitness-kpi">
                <div class="fitness-kpi-label">
                    Participant-Days
                </div>
                <div class="fitness-kpi-value">
                    {participant_days:,}
                </div>
                <div class="fitness-kpi-sub">
                    Filtered observation volume
                </div>
            </div>
            """
        )

    # KPI 3
    with k3:
        st.html(
            f"""
            <div class="fitness-kpi">
                <div class="fitness-kpi-label">
                    Average Steps
                </div>
                <div class="fitness-kpi-value">
                    {fmt(avg_steps)}
                </div>
                <div class="fitness-kpi-sub">
                    Daily average per participant-day
                </div>
            </div>
            """
        )

    # KPI 4
    with k4:
        st.html(
            f"""
            <div class="fitness-kpi">
                <div class="fitness-kpi-label">
                    Average Calories
                </div>
                <div class="fitness-kpi-value">
                    {fmt(avg_calories)}
                </div>
                <div class="fitness-kpi-sub">
                    Daily recorded expenditure
                </div>
            </div>
            """
        )

    # KPI 5
    with k5:
        goal_value = (
            f"{goal_rate:.1f}%"
            if not pd.isna(goal_rate)
            else "—"
        )
        st.html(
            f"""
            <div class="fitness-kpi">
                <div class="fitness-kpi-label">
                    10K Goal Attainment
                </div>
                <div class="fitness-kpi-value fitness-kpi-accent">
                    {goal_value}
                </div>
                <div class="fitness-kpi-sub">
                    Share of participant-days meeting target
                </div>
            </div>
            """
        )

    # DATA CONTEXT
    st.html(
        f"""
        <div class="data-context">
            <strong>Data coverage:</strong>
            {period_text}
            &nbsp; • &nbsp;
            <strong>Current view:</strong>
            {period_text}
            &nbsp; • &nbsp;
            <strong>Observations:</strong>
            {participant_days:,}
            &nbsp; • &nbsp;
            <strong>Source:</strong>
            fitness_daily_master.csv
        </div>
        """
    )

# 2. CURRENT OPERATING PICTURE
active_minutes = safe_mean(
    filtered,
    "Total_Active_Minutes",
)

sedentary_minutes = safe_mean(
    filtered,
    "SedentaryMinutes",
)

sleep_hours = (
    safe_mean(
        filtered,
        "Sleep_Minutes",
    ) / 60
    if "Sleep_Minutes" in filtered.columns
    else np.nan
)

sleep_target_rate = (
    filtered["Sleep_7h_Target"].mean() * 100
    if (
        "Sleep_7h_Target" in filtered.columns
        and filtered["Sleep_7h_Target"].notna().any()
    )
    else np.nan
)

with st.container(border=True):
    st.html(
        """
        <div class="section-header">
            <div class="section-label">
                EXECUTIVE SIGNALS
            </div>
            <div class="section-title">
                Current operating picture
            </div>
            <div class="section-copy">
                The three operating areas that matter most
                in the current participant-day population:
                activity, target attainment, and wellness.
            </div>
        </div>
        """
    )
    op1, op2, op3 = st.columns(
        3,
        gap="medium",
    )

    # ACTIVITY
    with op1:
        activity_status = (
            "AT / ABOVE REFERENCE"
            if (
                not pd.isna(avg_steps)
                and avg_steps >= 10000
            )
            else "BELOW 10K REFERENCE"
        )
        activity_class = (
            ""
            if activity_status == "AT / ABOVE REFERENCE"
            else ""
        )
        st.html(
            f"""
            <div class="operating-card">
                <div class="operating-card-label">
                    ACTIVITY
                </div>
                <div class="operating-card-title">
                    Daily movement
                </div>
                <div class="operating-card-value">
                    {fmt(avg_steps)}
                    <span style="
                        font-size:12px;
                        font-weight:700;
                        color:#8f97a5;
                    ">
                        steps/day
                    </span>
                </div>
                <div class="operating-card-copy">
                    Average recorded steps across the
                    selected participant-day population.
                </div>
                <div class="operating-divider"></div>
                <div class="operating-stat">
                    <strong>Active time:</strong>
                    {
                        f"{active_minutes:,.0f} min/day"
                        if not pd.isna(active_minutes)
                        else "Not available"
                    }
                </div>
                <div class="operating-stat">
                    <strong>Sedentary time:</strong>
                    {
                        f"{sedentary_minutes:,.0f} min/day"
                        if not pd.isna(sedentary_minutes)
                        else "Not available"
                    }
                </div>
                <div class="status-pill">
                    {activity_status}
                </div>
            </div>
            """
        )

    # GOAL ATTAINMENT
    with op2:
        goal_status = (
            "TARGET ATTAINMENT"
            if (
                not pd.isna(goal_rate)
                and goal_rate >= 50
            )
            else "BELOW 50% ATTAINMENT"
        )
        st.html(
            f"""
            <div class="operating-card">
                <div class="operating-card-label">
                    GOAL ATTAINMENT
                </div>
                <div class="operating-card-title">
                    10K step target
                </div>
                <div class="operating-card-value orange">
                    {
                        f"{goal_rate:.1f}%"
                        if not pd.isna(goal_rate)
                        else "—"
                    }
                </div>
                <div class="operating-card-copy">
                    Share of participant-days reaching
                    the 10,000-step activity target.
                </div>
                <div class="operating-divider"></div>
                <div class="operating-stat">
                    <strong>Target:</strong>
                    10,000 steps/day
                </div>
                <div class="operating-stat">
                    <strong>Below target:</strong>
                    {
                        f"{100 - goal_rate:.1f}%"
                        if not pd.isna(goal_rate)
                        else "Not available"
                    }
                </div>
                <div class="status-pill">
                    {goal_status}
                </div>
            </div>
            """
        )

    # WELLNESS
    with op3:
        wellness_status = (
            "MEETS 7H REFERENCE"
            if (
                not pd.isna(sleep_target_rate)
                and sleep_target_rate >= 50
            )
            else "BELOW 7H REFERENCE"
        )
        st.html(
            f"""
            <div class="operating-card">
                <div class="operating-card-label">
                    WELLNESS
                </div>
                <div class="operating-card-title">
                    Recorded sleep
                </div>
                <div class="operating-card-value">
                    {
                        f"{sleep_hours:.1f}"
                        if not pd.isna(sleep_hours)
                        else "—"
                    }
                    <span style="
                        font-size:12px;
                        font-weight:700;
                        color:#8f97a5;
                    ">
                        hrs/day
                    </span>
                </div>
                <div class="operating-card-copy">
                    Average recorded sleep across the
                    selected participant-day population.
                </div>
                <div class="operating-divider"></div>
                <div class="operating-stat">
                    <strong>7-hour attainment:</strong>
                    {
                        f"{sleep_target_rate:.1f}%"
                        if not pd.isna(sleep_target_rate)
                        else "Not available"
                    }
                </div>
                <div class="operating-stat">
                    <strong>Reference:</strong>
                    7 hours/night
                </div>
                <div class="status-pill">
                    {wellness_status}
                </div>
            </div>
            """
        )

# 3. EXECUTIVE CONTEXT
with st.container(border=True):
    st.html(
        """
        <div class="section-header">
            <div class="section-label">
                MANAGEMENT CONTEXT
            </div>
            <div class="section-title">
                Measures requiring context
            </div>
            <div class="section-copy">
                Concise interpretation of the current operating
                picture. These statements describe the data;
                detailed investigation remains available below.
            </div>
        </div>
        """
    )
    insight_cols = st.columns(
        3,
        gap="medium",
    )

    # ACTIVITY INSIGHT
    with insight_cols[0]:
        if not pd.isna(avg_steps):
            if avg_steps < 10000:
                activity_copy = (
                    f"Below the 10,000-step reference by "
                    f"<strong>{10000 - avg_steps:,.0f}</strong> steps/day."
                )
            else:
                activity_copy = (
                    f"At or above the 10,000-step reference, "
                    f"averaging <strong>{avg_steps:,.0f}</strong> steps/day."
                )
        else:
            activity_copy = (
                "<strong>Activity:</strong> "
                "Step data is not available."
            )
        st.html(
            f"""
            <div class="insight-card">
                <div class="insight-eyebrow">ACTIVITY SIGNAL</div>
                <div class="insight-headline">Daily movement level</div>
                <div class="insight-value">
                    {fmt(avg_steps)}
                    <span style="font-size:10px;color:#7f8794;font-weight:700;">
                        steps/day
                    </span>
                </div>
                <div class="insight-copy">
                    {activity_copy}
                </div>
            </div>
            """
        )

    # GOAL INSIGHT
    with insight_cols[1]:
        if not pd.isna(goal_rate):
            goal_copy = (
                f"<strong>10K attainment:</strong> "
                f"{goal_rate:.1f}% of participant-days "
                f"meet the 10,000-step target."
            )
        else:
            goal_copy = (
                "<strong>10K attainment:</strong> "
                "Target data is not available."
            )
        st.html(
            f"""
            <div class="insight-card">
                <div class="insight-eyebrow">GOAL SIGNAL</div>
                <div class="insight-headline">10K target attainment</div>
                <div class="insight-value">
                    {goal_rate:.1f}%
                </div>
                <div class="insight-copy">
                    {goal_copy}
                </div>
            </div>
            """
        )

    # WELLNESS INSIGHT
    with insight_cols[2]:
        if not pd.isna(sleep_target_rate):
            wellness_copy = (
                f"<strong>Sleep target:</strong> "
                f"{sleep_target_rate:.1f}% of participant-days "
                f"meet the seven-hour recorded sleep target."
            )
        else:
            wellness_copy = (
                "<strong>Sleep target:</strong> "
                "Sleep target data is not available."
            )
        st.html(
            f"""
            <div class="insight-card">
                <div class="insight-eyebrow">WELLNESS SIGNAL</div>
                <div class="insight-headline">Seven-hour sleep target</div>
                <div class="insight-value">
                    {sleep_target_rate:.1f}%
                </div>
                <div class="insight-copy">
                    {wellness_copy}
                </div>
            </div>
            """
        )

# VIEW FILTERS
with st.container(border=True):
    st.html(
        """
        <div class="filter-intro">
            <div class="filter-label">
                VIEW FILTERS
            </div>
            <div class="filter-copy">
                Refine the executive view before reviewing the period trend.
                The selected scope applies to the measures and charts on this page.
            </div>
        </div>
        """
    )
    filter_cols = st.columns(
        [1.35, 1.0, 1.0, 1.0],
        gap="medium",
    )

    # DATE
    if (
        "Date" in filter_base.columns
        and filter_base["Date"].notna().any()
    ):
        min_date = filter_base["Date"].min().date()
        max_date = filter_base["Date"].max().date()
        with filter_cols[0]:
            st.date_input(
                "Analysis period",
                value=st.session_state["executive_date_filter"],
                min_value=min_date,
                max_value=max_date,
                format="YYYY-MM-DD",
                key="executive_date_filter",
            )

    # PARTICIPANT
    with filter_cols[1]:
        if "Id" in filter_base.columns:
            participant_options = sorted(
                filter_base["Id"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            st.multiselect(
                "Participant",
                options=participant_options,
                placeholder="All participants",
                key="executive_participant_filter",
            )

    # DAY TYPE
    with filter_cols[2]:
        st.selectbox(
            "Day type",
            [
                "All days",
                "Weekdays",
                "Weekends",
            ],
            key="executive_day_type_filter",
        )

    # GOAL
    with filter_cols[3]:

        st.selectbox(
            "10K goal",
            [
                "All records",
                "Met 10K",
                "Below 10K",
            ],
            key="executive_goal_filter",
        )
    st.html(
        """
        <div class="filter-status">
            <span class="filter-status-dot"></span>
            <span>
                Filters are applied automatically and update the executive view.
            </span>
        </div>
        """
    )

# 4. PERFORMANCE TREND
with st.container(border=True):
    st.html(
        """
        <div class="section-header">
            <div class="section-label">
                PERFORMANCE TREND
            </div>
            <div class="section-title">
                Activity trend over the period
            </div>
            <div class="section-copy">
                Daily average steps against the 10,000-step
                reference and daily participant coverage.
            </div>
        </div>
        """
    )
    trend_left, trend_right = st.columns(
        2,
        gap="medium",
    )

    # STEPS TREND
    with trend_left:
        if (
            "TotalSteps" in filtered.columns
            and "Date" in filtered.columns
        ):
            daily_steps = (
                filtered
                .groupby(
                    "Date",
                    as_index=False,
                )["TotalSteps"]
                .mean()
                .sort_values("Date")
            )
            daily_steps["Rolling_7d"] = (
                daily_steps["TotalSteps"]
                .rolling(
                    7,
                    min_periods=1,
                )
                .mean()
            )
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=daily_steps["Date"],
                    y=daily_steps["TotalSteps"],
                    mode="lines",
                    name="Daily Average",
                    line=dict(
                        color="#3b414c",
                        width=1,
                    ),
                    hovertemplate=(
                        "%{x|%d %b %Y}<br>"
                        "Daily Avg: %{y:,.0f} steps"
                        "<extra></extra>"
                    ),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=daily_steps["Date"],
                    y=daily_steps["Rolling_7d"],
                    mode="lines",
                    name="7-Day Trend",
                    line=dict(
                        color="#FC5200",
                        width=2.5,
                    ),
                    hovertemplate=(
                        "%{x|%d %b %Y}<br>"
                        "7-Day Avg: %{y:,.0f} steps"
                        "<extra></extra>"
                    ),
                )
            )
            fig.add_hline(
                y=10000,
                line_dash="dash",
                line_color="#62b7ff",
                annotation_text="10K Reference",
                annotation_position="top left",
                annotation_font_color="#62b7ff",
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0b0d10",
                plot_bgcolor="#11141a",
                font=dict(
                    color="#dce1e8"
                ),
                height=310,
                margin=dict(
                    l=20,
                    r=20,
                    t=35,
                    b=20,
                ),
                xaxis_title=None,
                yaxis_title="Average Steps",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.05,
                    xanchor="right",
                    x=1,
                ),
            )
            fig.update_xaxes(
                gridcolor="#292d36"
            )
            fig.update_yaxes(
                gridcolor="#292d36"
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False
                },
            )
        else:
            st.info(
                "Step trend data is not available."
            )

    # PARTICIPATION TREND
    with trend_right:
        if (
            "Id" in filtered.columns
            and "Date" in filtered.columns
        ):
            daily_participation = (
                filtered
                .groupby(
                    "Date",
                    as_index=False,
                )["Id"]
                .nunique()
                .rename(
                    columns={
                        "Id":
                        "Active_Participants"
                    }
                )
                .sort_values("Date")
            )
            fig = px.area(
                daily_participation,
                x="Date",
                y="Active_Participants",
            )
            fig.update_traces(
                line_color="#FC5200",
                fillcolor="rgba(252,82,0,0.18)",
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    "Active Participants: %{y}"
                    "<extra></extra>"
                ),
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0b0d10",
                plot_bgcolor="#11141a",
                font=dict(
                    color="#dce1e8"
                ),
                height=310,
                margin=dict(
                    l=20,
                    r=20,
                    t=35,
                    b=20,
                ),
                xaxis_title=None,
                yaxis_title="Active Participants",
                showlegend=False,
            )
            fig.update_xaxes(
                gridcolor="#292d36"
            )
            fig.update_yaxes(
                gridcolor="#292d36"
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False
                },
            )
        else:
            st.info(
                "Participant identifiers are not available."
            )

# 5. WEEKDAY / WEEKEND COMPARISON
with st.container(border=True):
    st.html(
        """
        <div class="section-header">
            <div class="section-label">
                EXECUTIVE COMPARISON
            </div>
            <div class="section-title">
                Where activity behavior differs
            </div>
            <div class="section-copy">
                Weekday and weekend behavior provides context
                for the overall activity and calorie signal.
            </div>
        </div>
        """
    )
    if (
        "TotalSteps" in filtered.columns
        and "Calories" in filtered.columns
    ):
        comparison_df = filtered.copy()
        if "Is_Weekend" in comparison_df.columns:
            comparison_df["Day_Type"] = np.where(
                comparison_df["Is_Weekend"],
                "Weekend",
                "Weekday",
            )
        elif "Date" in comparison_df.columns:
            comparison_df["Day_Type"] = np.where(
                comparison_df["Date"].dt.dayofweek >= 5,
                "Weekend",
                "Weekday",
            )
        else:

            comparison_df["Day_Type"] = "All Days"
        comparison = (
            comparison_df
            .groupby(
                "Day_Type",
                as_index=False,
            )
            .agg(
                Avg_Steps=(
                    "TotalSteps",
                    "mean",
                ),
                Avg_Calories=(
                    "Calories",
                    "mean",
                ),
            )
        )
        left, right = st.columns(
            2,
            gap="medium",
        )

        # STEPS
        with left:
            fig = px.bar(
                comparison,
                x="Day_Type",
                y="Avg_Steps",
                color="Day_Type",
                text_auto=".0f",
                color_discrete_map={
                    "Weekday": "#FC5200",
                    "Weekend": "#ff9b70",
                },
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0b0d10",
                plot_bgcolor="#11141a",
                font=dict(
                    color="#dce1e8"
                ),
                showlegend=False,
                height=290,
                margin=dict(
                    l=20,
                    r=20,
                    t=12,
                    b=20,
                ),
                xaxis_title=None,
                yaxis_title="Average Steps",
            )
            fig.update_xaxes(
                gridcolor="#292d36"
            )
            fig.update_yaxes(
                gridcolor="#292d36"
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False
                },
            )

        # CALORIES
        with right:

            fig = px.bar(
                comparison,
                x="Day_Type",
                y="Avg_Calories",
                color="Day_Type",
                text_auto=".0f",
                color_discrete_map={
                    "Weekday": "#62b7ff",
                    "Weekend": "#a678ff",
                },
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0b0d10",
                plot_bgcolor="#11141a",
                font=dict(
                    color="#dce1e8"
                ),
                showlegend=False,
                height=290,
                margin=dict(
                    l=20,
                    r=20,
                    t=12,
                    b=20,
                ),
                xaxis_title=None,
                yaxis_title="Average Calories",
            )
            fig.update_xaxes(
                gridcolor="#292d36"
            )
            fig.update_yaxes(
                gridcolor="#292d36"
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False
                },
            )
    else:
        st.info(
            "Weekday/weekend comparison data is not available."
        )

# 6. PROGRAM OUTCOME + ACTIVITY PROFILE
outcome_left, outcome_right = st.columns(
    2,
    gap="medium",
)

# 10K GOAL ATTAINMENT
with outcome_left:
    with st.container(border=True):
        st.html(
            """
            <div class="section-header">
                <div class="section-label">
                    PROGRAM OUTCOME
                </div>
                <div class="section-title">
                    10K Goal Attainment
                </div>
                <div class="section-copy">
                    Share of participant-days reaching
                    the 10,000-step activity target.
                </div>
            </div>
            """
        )
        if "Meets_10k_Steps" in filtered.columns:

            goal_data = (
                filtered
                .assign(
                    Status=np.where(
                        filtered[
                            "Meets_10k_Steps"
                        ].fillna(False),
                        "Met 10K",
                        "Below 10K",
                    )
                )
                .groupby("Status")
                .size()
                .reset_index(
                    name="Records"
                )
            )
            fig = px.pie(
                goal_data,
                names="Status",
                values="Records",
                hole=0.68,
                color="Status",
                color_discrete_map={
                    "Met 10K": "#FC5200",
                    "Below 10K": "#3b414c",
                },
            )
            fig.update_traces(
                textinfo="percent",
                textfont=dict(
                    size=13,
                    color="#ffffff",
                ),
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Participant-days: %{value:,}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                ),
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0b0d10",
                plot_bgcolor="#11141a",
                font=dict(
                    color="#dce1e8"
                ),
                height=315,
                margin=dict(
                    l=10,
                    r=10,
                    t=5,
                    b=20,
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.08,
                    xanchor="center",
                    x=0.5,
                ),
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False
                },
            )
        else:
            st.info(
                "10K goal data is not available."
            )

# ACTIVITY INTENSITY
with outcome_right:
    with st.container(border=True):
        st.html(
            """
            <div class="section-header">
                <div class="section-label">
                    ACTIVITY PROFILE
                </div>
                <div class="section-title">
                    Activity Intensity Mix
                </div>
                <div class="section-copy">
                    Average daily minutes across recorded
                    activity-intensity categories.
                </div>
            </div>
            """
        )

        intensity_columns = [
            (
                "VeryActiveMinutes",
                "Very Active",
            ),
            (
                "FairlyActiveMinutes",
                "Fairly Active",
            ),
            (
                "LightlyActiveMinutes",
                "Lightly Active",
            ),
            (
                "SedentaryMinutes",
                "Sedentary",
            ),
        ]

        available_intensity = [
            item
            for item in intensity_columns
            if item[0] in filtered.columns
        ]

        if available_intensity:
            intensity_data = pd.DataFrame(
                {
                    "Activity Level": [
                        label
                        for _, label
                        in available_intensity
                    ],
                    "Average Minutes": [
                        filtered[column].mean()
                        for column, _
                        in available_intensity
                    ],
                }
            )

            intensity_data = (
                intensity_data
                .sort_values(
                    "Average Minutes",
                    ascending=True,
                )
            )

            fig = px.bar(
                intensity_data,
                x="Average Minutes",
                y="Activity Level",
                orientation="h",
                text="Average Minutes",
            )

            fig.update_traces(
                marker_color="#FC5200",
                texttemplate="%{text:.0f} min",
                textposition="outside",
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Average: %{x:.1f} minutes/day"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0b0d10",
                plot_bgcolor="#11141a",
                font=dict(
                    color="#dce1e8"
                ),
                height=315,
                margin=dict(
                    l=10,
                    r=55,
                    t=5,
                    b=25,
                ),
                xaxis_title="Average Minutes per Day",
                yaxis_title=None,
                showlegend=False,
            )

            fig.update_xaxes(
                gridcolor="#292d36",
                zeroline=False,
            )

            fig.update_yaxes(
                gridcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False
                },
            )
        else:
            st.info(
                "Activity-intensity data is not available."
            )

# 7. WELLNESS OUTCOME
if "Sleep_7h_Target" in filtered.columns:
    with st.container(border=True):
        st.html(
            """
            <div class="section-header">
                <div class="section-label">
                    WELLNESS OUTCOME
                </div>
                <div class="section-title">
                    Sleep Target Attainment
                </div>
                <div class="section-copy">
                    Participant-day share meeting the
                    seven-hour recorded sleep target.
                </div>
            </div>
            """
        )

        sleep_data = (
            filtered
            .assign(
                Status=np.where(
                    filtered[
                        "Sleep_7h_Target"
                    ].fillna(False),
                    "Met 7h Target",
                    "Below 7h",
                )
            )
            .groupby("Status")
            .size()
            .reset_index(
                name="Records"
            )
        )

        sleep_left, sleep_right = st.columns(
            [1.0, 1.35],
            gap="medium",
        )

        # SLEEP DONUT
        with sleep_left:

            fig = px.pie(
                sleep_data,
                names="Status",
                values="Records",
                hole=0.70,
                color="Status",
                color_discrete_map={
                    "Met 7h Target": "#62b7ff",
                    "Below 7h": "#3b414c",
                },
            )

            fig.update_traces(
                textinfo="percent",
                textfont=dict(
                    size=12,
                    color="#ffffff",
                ),
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Participant-days: %{value:,}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0b0d10",
                plot_bgcolor="#11141a",
                font=dict(
                    color="#dce1e8"
                ),
                height=285,
                margin=dict(
                    l=5,
                    r=5,
                    t=5,
                    b=15,
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.10,
                    xanchor="center",
                    x=0.5,
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False
                },
            )

        # SLEEP CONTEXT
        with sleep_right:
            st.html(
                f"""
                <div class="operating-card">
                    <div class="operating-card-label">
                        WELLNESS CONTEXT
                    </div>
                    <div class="operating-card-title">
                        Recorded sleep signal
                    </div>
                    <div class="operating-card-copy">
                        Sleep is presented as an executive
                        wellness outcome. Detailed behavioral
                        investigation remains on the
                        Sleep & Wellness page.
                    </div>
                    <div class="operating-divider"></div>
                    <div class="operating-stat">
                        <strong>
                            Average recorded sleep:
                        </strong>
                        {
                            f"{sleep_hours:.1f} hours/day"
                            if not pd.isna(sleep_hours)
                            else "Not available"
                        }
                    </div>
                    <div class="operating-stat">
                        <strong>
                            7-hour target attainment:
                        </strong>
                        {
                            f"{sleep_target_rate:.1f}%"
                            if not pd.isna(sleep_target_rate)
                            else "Not available"
                        }
                    </div>
                    <div class="operating-stat">
                        <strong>
                            Active minutes:
                        </strong>
                        {
                            f"{active_minutes:,.0f} min/day"
                            if not pd.isna(active_minutes)
                            else "Not available"
                        }
                    </div>
                </div>
                """
            )
else:
    with st.container(border=True):
        st.html(
            """
            <div class="section-header">
                <div class="section-label">
                    WELLNESS OUTCOME
                </div>
                <div class="section-title">
                    Wellness data unavailable
                </div>
                <div class="section-copy">
                    Sleep target attainment is not available
                    in the current master dataset.
                </div>
            </div>
            """
        )

# SIDEBAR EXECUTIVE SUMMARY
with st.sidebar:

    sidebar_participants = (
        filtered["Id"].nunique()
        if "Id" in filtered.columns
        else np.nan
    )

    sidebar_steps = safe_mean(
        filtered,
        "TotalSteps",
    )

    sidebar_calories = safe_mean(
        filtered,
        "Calories",
    )

    sidebar_goal = (
        filtered["Meets_10k_Steps"].mean() * 100
        if (
            "Meets_10k_Steps" in filtered.columns
            and filtered["Meets_10k_Steps"].notna().any()
        )
        else np.nan
    )

    sidebar_sleep = (
        safe_mean(
            filtered,
            "Sleep_Minutes",
        ) / 60
        if "Sleep_Minutes" in filtered.columns
        else np.nan
    )

    sidebar_sleep_target = (
        filtered[
            "Sleep_7h_Target"
        ].mean() * 100
        if (
            "Sleep_7h_Target" in filtered.columns
            and filtered[
                "Sleep_7h_Target"
            ].notna().any()
        )
        else np.nan
    )

    st.html(
        f"""
        <div class="fitness-sidebar-card">
            <div class="label">
                EXECUTIVE OVERVIEW
            </div>
            <div class="heading">
                Decision-focused summary
            </div>
            <div class="copy">
                High-level view of participation,
                activity, goal attainment, and wellness.
            </div>
            <div style="height:14px;"></div>
            <div class="heading">
                Current view
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Analysis period:
                </strong><br>
                {period_text}
            </div>
            <div style="height:9px;"></div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Participant-days:
                </strong>
                {len(filtered):,}
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Participants:
                </strong>
                {
                    f"{sidebar_participants:,.0f}"
                    if not pd.isna(sidebar_participants)
                    else "—"
                }
            </div>
            <div style="height:10px;"></div>
            <div class="heading">
                Activity signal
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Avg. steps:
                </strong>
                {
                    f"{sidebar_steps:,.0f}"
                    if not pd.isna(sidebar_steps)
                    else "—"
                }
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Avg. calories:
                </strong>
                {
                    f"{sidebar_calories:,.0f}"
                    if not pd.isna(sidebar_calories)
                    else "—"
                }
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    10K goal:
                </strong>
                {
                    f"{sidebar_goal:.1f}%"
                    if not pd.isna(sidebar_goal)
                    else "—"
                }
            </div>
            <div style="height:10px;"></div>
            <div class="heading">
                Wellness signal
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Avg. sleep:
                </strong>
                {
                    f"{sidebar_sleep:.1f} hrs/day"
                    if not pd.isna(sidebar_sleep)
                    else "—"
                }
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    7h target:
                </strong>
                {
                    f"{sidebar_sleep_target:.1f}%"
                    if not pd.isna(sidebar_sleep_target)
                    else "—"
                }
            </div>
            <div style="height:10px;"></div>
            <div class="copy" style="color:#69717e;">
                Values reflect the currently filtered
                participant-day dataset.
            </div>
        </div>
        """
    )