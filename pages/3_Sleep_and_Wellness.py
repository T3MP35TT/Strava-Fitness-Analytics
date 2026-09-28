# pages/3_Sleep_and_Wellness.py

import base64
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.data import load_data

# PAGE CONFIG
st.set_page_config(
    page_title="Sleep & Wellness | Fitness Analytics",
    page_icon="😴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# HELPERS
def render_html(html: str) -> None:
    """Render HTML using the best available Streamlit API."""
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)

def clean_numeric(series: pd.Series) -> pd.Series:
    """Convert a Series to numeric values, coercing invalid values."""
    return pd.to_numeric(series, errors="coerce")

def safe_mean(series: pd.Series, default: float = 0.0) -> float:
    """Return a safe numeric mean."""
    value = pd.to_numeric(series, errors="coerce").mean()
    if pd.isna(value):
        return default
    return float(value)

def safe_median(series: pd.Series, default: float = 0.0) -> float:
    """Return a safe numeric median."""
    value = pd.to_numeric(series, errors="coerce").median()
    if pd.isna(value):
        return default
    return float(value)

def safe_percentage(
    numerator: float,
    denominator: float,
    default: float = 0.0,
) -> float:
    """Calculate a safe percentage."""
    if denominator == 0:
        return default
    return float(numerator / denominator * 100)

def format_number(value: float, decimals: int = 1) -> str:
    """Format a numeric value safely."""
    if pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f}"


def configure_plot(fig, height: int = 360):
    """Apply the shared dashboard Plotly configuration."""
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#dfe3e8",
            size=10,
        ),
        hoverlabel=dict(
            bgcolor="#171a20",
            bordercolor="#343943",
            font=dict(
                color="#ffffff",
                size=11,
            ),
        ),
    )
    return fig

# STRAVA LOGO
ROOT_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = ROOT_DIR / "images" / "strava_logo.png"

logo_data_uri = ""

if LOGO_PATH.exists():
    try:
        logo_bytes = LOGO_PATH.read_bytes()
        logo_b64 = base64.b64encode(logo_bytes).decode("utf-8")

        suffix = LOGO_PATH.suffix.lower()

        mime_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(suffix, "image/png")

        logo_data_uri = f"data:{mime_type};base64,{logo_b64}"

    except Exception:
        logo_data_uri = ""

# LOADING SCREEN
if logo_data_uri:
    loading_logo_html = f"""
        <img
            src="{logo_data_uri}"
            alt="Strava"
            class="fitness-loading-logo"
        />
    """
else:
    loading_logo_html = """
        <div class="fitness-loading-fallback">
            A
        </div>
    """
render_html(
    f"""
    <style>
        /* ====================================================
           FULL-SCREEN LOADING SCREEN
           ==================================================== */
        .fitness-loading-screen {{
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            z-index: 999999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background:
                radial-gradient(
                    circle at 50% 42%,
                    rgba(252, 82, 0, 0.075),
                    transparent 28%
                ),
                linear-gradient(
                    180deg,
                    #0b0d10 0%,
                    #090b0e 100%
                );
            opacity: 1;
            visibility: visible;
            pointer-events: all;
            transition:
                opacity 0.45s ease,
                visibility 0.45s ease;
        }}
        /* ====================================================
           LOGO
           ==================================================== */
        .fitness-loading-logo {{
            width: 105px;
            height: 105px;
            object-fit: contain;
            display: block;
            background: transparent;
            border: none;
            box-shadow: none;
            margin-bottom: 28px;
            animation:
                fitness-logo-pulse 1.8s ease-in-out infinite;
        }}
        .fitness-loading-fallback {{
            width: 82px;
            height: 82px;

            border-radius: 50%;

            display: flex;
            align-items: center;
            justify-content: center;

            background: #fc5200;

            color: #ffffff;

            font-size: 40px;
            font-weight: 900;

            margin-bottom: 30px;
        }}
        /* ====================================================
           LOADING RING
           ==================================================== */

        .fitness-loading-spinner {{
            width: 34px;
            height: 34px;
            border-radius: 50%;
            border: 3px solid rgba(255,255,255,0.12);
            border-top-color: #fc5200;
            animation:
                fitness-spin 0.85s linear infinite;
            margin-bottom: 20px;
        }}
        /* ====================================================
           LOADING TEXT
           ==================================================== */
        .fitness-loading-title {{
            color: #ffffff;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: 0.15px;
            margin: 0 0 7px 0;
            text-align: center;
        }}
        .fitness-loading-copy {{
            color: #747d89;
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.55px;
            text-transform: uppercase;
            margin: 0;
            text-align: center;
        }}
        /* ====================================================
           ANIMATIONS
           ==================================================== */
        @keyframes fitness-spin {{
            from {{
                transform: rotate(0deg);
            }}
            to {{
                transform: rotate(360deg);
            }}
        }}
        @keyframes fitness-logo-pulse {{
            0%,
            100% {{
                transform: scale(1);
                opacity: 1;
            }}
            50% {{
                transform: scale(1.035);
                opacity: 0.86;
            }}
        }}
        /* ====================================================
           SAFETY FALLBACK
           ==================================================== */
        /*
        If something prevents the final dashboard marker from
        rendering, automatically release the screen after 20s.
        */
        .fitness-loading-screen {{
            animation:
                fitness-loading-safety-release 20s forwards;
        }}
        @keyframes fitness-loading-safety-release {{
            0% {{
                opacity: 1;
                visibility: visible;
            }}
            92% {{
                opacity: 1;
                visibility: visible;
            }}
            100% {{
                opacity: 0;
                visibility: hidden;
                pointer-events: none;
            }}
        }}
        /* ====================================================
           REAL DASHBOARD READY STATE
           ==================================================== */
        /*
        Modern browsers support :has().
        Once Streamlit renders .dashboard-loaded,
        the loading screen disappears immediately.
        */
        body:has(.dashboard-loaded) .fitness-loading-screen {{
            opacity: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }}
    </style>
    <div class="fitness-loading-screen">
        {loading_logo_html}
        <div class="fitness-loading-spinner"></div>
        <div class="fitness-loading-title">
            Loading Sleep &amp; Wellness
        </div>
        <div class="fitness-loading-copy">
            Preparing your fitness analytics dashboard
        </div>
    </div>
    """
)

# DASHBOARD THEME
render_html(
    """
    <style>
    :root {
        --bg: #0b0d10;
        --surface: #101318;
        --surface-2: #151920;
        --surface-3: #1a1e26;
        --border: #2a2f38;
        --text: #f5f7fa;
        --muted: #9aa2ae;
        --muted-2: #737c89;
        --orange: #fc5200;
        --orange-light: #ff7840;
        --blue: #79bdf0;
        --green: #5fcf9a;
        --red: #f27d7d;
    }

    /* ========================================================
       APP
       ======================================================== */
    .stApp {
        background:
            radial-gradient(
                circle at 88% 3%,
                rgba(252, 82, 0, 0.065),
                transparent 25%
            ),
            linear-gradient(
                180deg,
                #0b0d10 0%,
                #090b0e 100%
            );
        color: var(--text);
    }
    [data-testid="stAppViewContainer"] {
        background: transparent;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }

    /* ========================================================
       SIDEBAR
       ======================================================== */
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
    .fitness-sidebar-divider {
        height: 1px;
        background: #2a2d34;
        margin: 16px 0 12px 0;
    }
    .fitness-sidebar-card {
        border: 1px solid #292d36;
        border-radius: 10px;
        background: #11141a;
        padding: 12px 13px;
        margin: 0;
    }
    .fitness-sidebar-card .label {
        color: var(--orange);
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

    /* ========================================================
       MAIN CONTENT
       ======================================================== */
    .block-container {
        max-width: none !important;
        width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-top: 64px !important;
        padding-left: 24px !important;
        padding-right: 24px !important;
        padding-bottom: 4rem !important;
    }
    .block-container > div {
        max-width: none !important;
        width: 100% !important;
        gap: 12px !important;
        row-gap: 12px !important;
    }

    /* ========================================================
       HERO
       ======================================================== */
    .sleep-hero {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 20px;
        padding: 27px 48px 29px 48px;
        margin: 0 0 22px 0 !important;
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
        backdrop-filter: blur(24px) saturate(145%);
        -webkit-backdrop-filter: blur(24px) saturate(145%);
    }
    .sleep-hero::before {
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
    .sleep-hero::after {
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
    .sleep-hero > * {
        position: relative;
        z-index: 3;
    }
    .sleep-eyebrow {
        color: var(--orange);
        font-size: 9px;
        font-weight: 900;
        letter-spacing: 1.55px;
        text-transform: uppercase;
        margin-bottom: 13px;
    }
    .sleep-title-row {
        display: flex;
        align-items: center;
        gap: 13px;
        margin: 0 0 12px 0;
    }
    .sleep-logo {
        width: 43px;
        height: 43px;
        min-width: 43px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: transparent;
        border: none;
        box-shadow: none;
        overflow: visible;
    }
    .sleep-logo img {
        width: 43px;
        height: 43px;
        object-fit: contain;
        display: block;
        border: none;
        box-shadow: none;
        background: transparent;
    }
    .sleep-icon {
        width: 31px;
        height: 31px;
        border-radius: 50%;
        background: #fc5200;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        font-weight: 900;
    }
    .sleep-title {
        color: #ffffff;
        font-size: clamp(
            2.05rem,
            3.4vw,
            3.15rem
        );
        font-weight: 900;
        letter-spacing: -1.9px;
        line-height: 1;
        margin: 0;
    }
    .sleep-title .sleep-title-orange {
        color: var(--orange);
    }
    .sleep-description {
        max-width: 1080px;
        color: #aab2bd;
        font-size: 13px;
        line-height: 1.65;
        margin: 0;
    }

    /* ========================================================
       MAJOR CARDS
       ======================================================== */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--border) !important;
        border-radius: 15px !important;
        background:
            linear-gradient(
                145deg,
                rgba(17,20,25,0.98),
                rgba(12,14,18,0.98)
            ) !important;
        box-shadow:
            0 10px 28px rgba(0,0,0,0.10);
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]
        [data-testid="stVerticalBlock"] {
        gap: 0 !important;
        row-gap: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]
        [data-testid="stElementContainer"] {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]
        [data-testid="stHtml"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* ========================================================
       SECTION HEADERS
       ======================================================== */
    .section-header {
        padding: 18px 20px 7px 20px;
        margin: 0 !important;
    }
    .section-label {
        color: var(--orange);
        font-size: 9px;
        font-weight: 900;
        letter-spacing: 1.55px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .section-title {
        color: #ffffff;
        font-size: 22px;
        font-weight: 850;
        letter-spacing: -0.55px;
        line-height: 1.15;
        margin-bottom: 5px;
    }
    .section-copy {
        color: #747d89;
        font-size: 11px;
        line-height: 1.55;
        margin: 0;
    }

    /* ========================================================
       FILTERS
       ======================================================== */
    .filter-header {
        padding: 8px 10px 6px 10px !important;
        margin: 0 !important;
    }
    .filter-label {
        color: var(--orange);
        font-size: 9px;
        font-weight: 900;
        letter-spacing: 1.55px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .filter-title {
        color: #ffffff;
        font-size: 21px;
        font-weight: 850;
        letter-spacing: -0.45px;
        line-height: 1.15;
        margin: 0;
    }
    .filter-copy {
        color: #747d89;
        font-size: 11px;
        line-height: 1.45;
        margin-top: 4px;
        margin-bottom: 0;
    }
    .filter-content {
        padding: 2px 5px 0px 0px !important;
        margin: 0 !important;
    }
    .filter-content [data-testid="stHorizontalBlock"] {
        gap: 12px !important;
    }
    .filter-content [data-testid="stHorizontalBlock"] > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    .filter-content [data-testid="stVerticalBlock"] {
        gap: 0 !important;
        row-gap: 0 !important;
    }
    .filter-content [data-testid="stElementContainer"] {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    .filter-content [data-testid="stDateInput"],
    .filter-content [data-testid="stSelectbox"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    /* ========================================================
       INPUTS
       ======================================================== */
    label {
        color: #a9b1bd !important;
        font-size: 10px !important;
        font-weight: 750 !important;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-testid="stDateInput"] > div {
        background: #20232b !important;
        border-color: #2d323d !important;
    }
    div[data-baseweb="select"] *,
    div[data-baseweb="input"] *,
    div[data-testid="stDateInput"] * {
        color: #f3f5f8 !important;
    }

    /* ========================================================
       KPI
       ======================================================== */
    .kpi-content {
        padding: 2px 20px 0px 20px !important;
        margin: 0 !important;
    }
    .kpi-content [data-testid="stHorizontalBlock"] {
        gap: 14px !important;
    }
    .kpi-content [data-testid="stElementContainer"] {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stMetric"] {
        border: 1px solid var(--border);
        border-radius: 13px;
        background:
            linear-gradient(
                145deg,
                #14171d,
                #101217
            );
        padding: 14px 15px;
        min-height: 96px;
        box-shadow:
            0 8px 22px rgba(0,0,0,0.12);
    }
    div[data-testid="stMetricLabel"] {
        color: #89929f !important;
        font-size: 9px !important;
        font-weight: 800 !important;
        letter-spacing: 0.75px !important;
        text-transform: uppercase !important;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 25px !important;
        font-weight: 900 !important;
        letter-spacing: -0.6px !important;
    }

    /* ========================================================
       BUSINESS SIGNALS
       ======================================================== */
    .signals-content {
        padding: 4px 20px 0px 20px !important;
        margin: 0 !important;
    }
    .signal-grid {
        display: grid;
        grid-template-columns:
            repeat(4, minmax(0, 1fr));
        gap: 14px;
    }
    .signal-card {
        border: 1px solid var(--border);
        border-top: 2px solid var(--orange);
        border-radius: 10px;
        background: #11141a;
        padding: 13px 14px;
        min-height: 82px;
    }
    .signal-title {
        color: #89929f;
        font-size: 9px;
        font-weight: 850;
        letter-spacing: 0.65px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .signal-value {
        color: #ffffff;
        font-size: 18px;
        font-weight: 850;
        letter-spacing: -0.25px;
        line-height: 1.2;
        margin-bottom: 5px;
    }
    .signal-copy {
        color: #747d89;
        font-size: 10px;
        line-height: 1.45;
    }

    /* ========================================================
       CHARTS
       ======================================================== */
    .sleep-chart-content {
        padding: 4px 20px 0 20px;
    }
    .sleep-chart-title {
        color: #ffffff;
        font-size: 18px;
        font-weight: 850;
        letter-spacing: -0.35px;
        margin: 0 0 6px 0;
    }
    .sleep-chart-copy {
        color: #747d89;
        font-size: 10px;
        line-height: 1.5;
        margin-bottom: 4px;
    }
    div[data-testid="stPlotlyChart"] {
        padding: 0 !important;
    }

    /* ========================================================
       INTERPRETATION
       ======================================================== */
    .sleep-note {
        margin: 12px 0 18px 0;
        padding: 12px 14px;
        border: 1px solid #292d36;
        border-left: 3px solid var(--orange);
        border-radius: 0 10px 10px 0;
        background: #11141a;
        color: #8f98a5;
        font-size: 10px;
        line-height: 1.55;
    }
    .sleep-note strong {
        color: #e8ebef;
    }

    /* ========================================================
       EMPTY / INFO STATES
       ======================================================== */
    .wellness-empty {
        padding: 25px 20px;
        color: #89929f;
        font-size: 11px;
        line-height: 1.5;
        text-align: center;
    }

    /* ========================================================
       MOBILE
       ======================================================== */
    @media (max-width: 900px) {
        [data-testid="stSidebar"] {
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            width: 280px !important;
        }
        .block-container {
            padding-top: 64px !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .block-container > div {
            gap: 10px !important;
            row-gap: 10px !important;
        }
        .sleep-hero {
            padding: 23px 22px;
        }
        .signal-grid {
            grid-template-columns: 1fr 1fr;
        }
    }
    @media (max-width: 600px) {
        .signal-grid {
            grid-template-columns: 1fr;
        }
        .sleep-title {
            font-size: 2rem;
        }
        .sleep-description {
            font-size: 12px;
        }
    }
    </style>
    """
)

# LOAD DATA
df = load_data()

if df is None or df.empty:
    st.warning("No wellness records are available.")
    st.stop()

df = df.copy()

# BASIC DATA PREPARATION
if "Date" in df.columns:
    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )
numeric_columns = [
    "Sleep_Minutes",
    "Sleep_7h_Target",
    "Sleep_Efficiency_Pct",
    "HeartRate_Avg",
    "TotalSteps",
    "Calories",
    "Total_Active_Minutes",
    "SedentaryMinutes",
]
for column in numeric_columns:
    if column in df.columns:
        df[column] = clean_numeric(df[column])
required_columns = [
    "Sleep_Minutes",
    "Sleep_7h_Target",
    "Sleep_Efficiency_Pct",
    "HeartRate_Avg",
    "TotalSteps",
    "Calories",
    "Total_Active_Minutes",
    "SedentaryMinutes",
    "Day_Of_Week",
]
missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]
if missing_columns:
    st.error(
        "The Sleep & Wellness page is missing required dataset columns."
    )
    st.code(
        ", ".join(missing_columns),
        language="text",
    )
    st.stop()

# HERO
if logo_data_uri:
    logo_html = (
        f'<img src="{logo_data_uri}" alt="Strava" />'
    )
else:
    logo_html = (
        '<div class="sleep-icon">A</div>'
    )

render_html(
    f"""
    <div class="sleep-hero">
        <div class="sleep-eyebrow">
            HOME &nbsp;•&nbsp; SLEEP &amp; WELLNESS
        </div>
        <div class="sleep-title-row">
            <div class="sleep-logo">
                {logo_html}
            </div>
            <h1 class="sleep-title">
                <span class="sleep-title-orange">Sleep</span>
                <span> &amp; Wellness</span>
            </h1>
        </div>
        <div class="sleep-description">
            Executive view of sleep duration, sleep quality, heart rate,
            sedentary behavior, and wellness relationships across the
            selected operating population.
        </div>
    </div>
    """
)

# FILTERS
with st.container(border=True):
    render_html(
        """
        <div class="filter-header">
            <div class="filter-label">
                ANALYSIS CONTROLS
            </div>
            <div class="filter-title">
                Define the operating population
            </div>
            <div class="filter-copy">
                Narrow the reporting population by period, participant,
                activity level, and daily goal attainment.
            </div>
        </div>
        """
    )
    render_html(
        '<div class="filter-content">'
    )
    f1, f2, f3, f4 = st.columns(
        [1.35, 0.95, 0.95, 0.95],
        gap="small",
    )

    # DATE
    with f1:
        if (
            "Date" in df.columns
            and df["Date"].notna().any()
        ):
            valid_dates = df["Date"].dropna()
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            selected_dates = st.date_input(
                "Analysis period",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="sleep_analysis_period",
            )
        else:
            selected_dates = None

    # PARTICIPANT
    with f2:
        if "Id" in df.columns:
            participants = (
                df["Id"]
                .dropna()
                .astype(str)
                .sort_values()
                .unique()
                .tolist()
            )
            participant_options = [
                "All participants"
            ] + participants
            selected_participant = st.selectbox(
                "Participant",
                participant_options,
                key="sleep_participant_filter",
            )
        else:
            selected_participant = "All participants"

    # ACTIVITY LEVEL
    with f3:
        activity_options = [
            "All activity levels",
            "Low (< 5K steps)",
            "Moderate (5K–9,999)",
            "High (10K+ steps)",
        ]
        selected_activity = st.selectbox(
            "Activity level",
            activity_options,
            key="sleep_activity_filter",
        )

    # 10K GOAL
    with f4:
        goal_options = [
            "All participant-days",
            "10K goal achieved",
            "Below 10K goal",
        ]
        selected_goal = st.selectbox(
            "10K step goal",
            goal_options,
            key="sleep_goal_filter",
        )
    render_html("</div>")

# APPLY FILTERS
filtered_df = df.copy()

# DATE FILTER
if (
    selected_dates is not None
    and isinstance(selected_dates, tuple)
    and len(selected_dates) == 2
):
    start_date = pd.Timestamp(
        selected_dates[0]
    )
    end_date = (
        pd.Timestamp(selected_dates[1])
        + pd.Timedelta(days=1)
        - pd.Timedelta(microseconds=1)
    )
    filtered_df = filtered_df[
        filtered_df["Date"].between(
            start_date,
            end_date,
            inclusive="both",
        )
    ]
elif selected_dates is not None:
    selected_date = pd.Timestamp(
        selected_dates
    )
    filtered_df = filtered_df[
        filtered_df["Date"].dt.normalize()
        == selected_date.normalize()
    ]

# PARTICIPANT FILTER
if (
    selected_participant != "All participants"
    and "Id" in filtered_df.columns
):

    filtered_df = filtered_df[
        filtered_df["Id"].astype(str)
        == str(selected_participant)
    ]

# ACTIVITY FILTER
if selected_activity == "Low (< 5K steps)":
    filtered_df = filtered_df[
        filtered_df["TotalSteps"] < 5000
    ]
elif selected_activity == "Moderate (5K–9,999)":
    filtered_df = filtered_df[
        filtered_df["TotalSteps"].between(
            5000,
            9999,
            inclusive="both",
        )
    ]
elif selected_activity == "High (10K+ steps)":
    filtered_df = filtered_df[
        filtered_df["TotalSteps"] >= 10000
    ]

# GOAL FILTER
if selected_goal == "10K goal achieved":
    filtered_df = filtered_df[
        filtered_df["TotalSteps"] >= 10000
    ]
elif selected_goal == "Below 10K goal":
    filtered_df = filtered_df[
        filtered_df["TotalSteps"] < 10000
    ]

# EMPTY STATE
if filtered_df.empty:
    st.warning(
        "No participant-days match the selected operating population."
    )
    st.stop()

# SELECTED POPULATION SUMMARY
participant_days = len(filtered_df)
if "Id" in filtered_df.columns:
    participant_count = (
        filtered_df["Id"]
        .dropna()
        .nunique()
    )
else:
    participant_count = participant_days

# PERIOD
if "Date" in filtered_df.columns:
    dates = (
        filtered_df["Date"]
        .dropna()
    )
else:
    dates = pd.Series(
        dtype="datetime64[ns]"
    )
if not dates.empty:
    min_date = dates.min().date()
    max_date = dates.max().date()
    period_text = (
        f"{min_date.strftime('%d %b %Y')} — "
        f"{max_date.strftime('%d %b %Y')}"
    )
else:
    period_text = (
        "Available observation period"
    )

# SLEEP DATASET
sleep = filtered_df[
    filtered_df["Sleep_Minutes"].notna()
].copy()
if sleep.empty:
    st.warning(
        "No records with sleep data are available "
        "for the selected operating population."
    )
    st.stop()

# KPI CALCULATIONS
avg_sleep = (
    safe_mean(sleep["Sleep_Minutes"]) / 60
)
target_rate = (
    safe_mean(sleep["Sleep_7h_Target"]) * 100
)
sleep_efficiency = safe_mean(
    sleep["Sleep_Efficiency_Pct"]
)
avg_heart_rate = safe_mean(
    filtered_df["HeartRate_Avg"]
)
sleep_observation_rate = safe_percentage(
    len(sleep),
    len(filtered_df),
)

# BUSINESS OPERATING SIGNALS
median_sleep = (
    safe_median(sleep["Sleep_Minutes"]) / 60
)
goal_series = filtered_df[
    "TotalSteps"
].dropna()
if not goal_series.empty:
    goal_attainment = safe_percentage(
        (goal_series >= 10000).sum(),
        len(goal_series),
    )
else:
    goal_attainment = 0.0
sedentary_series = filtered_df[
    "SedentaryMinutes"
].dropna()
sedentary_exposure = safe_mean(
    sedentary_series
)
sleep_coverage = sleep_observation_rate

# SIDEBAR SUMMARY
with st.sidebar:
    st.html(
        f"""
        <div class="fitness-sidebar-divider"></div>
        <div class="fitness-sidebar-card">
            <div class="label">
                SLEEP &amp; WELLNESS
            </div>
            <div class="heading">
                Decision-focused summary
            </div>
            <div class="copy">
                High-level view of sleep duration, sleep quality,
                heart rate, activity, and wellness relationships.
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
                {participant_days:,}
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Participants:
                </strong>
                {participant_count:,}
            </div>
            <div style="height:10px;"></div>
            <div class="heading">
                Wellness signal
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Avg. sleep:
                </strong>
                {avg_sleep:.1f} hrs
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    7h target:
                </strong>
                {target_rate:.1f}%
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Sleep efficiency:
                </strong>
                {sleep_efficiency:.1f}%
            </div>
            <div style="height:10px;"></div>
            <div class="heading">
                Cardiovascular signal
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Avg. heart rate:
                </strong>
                {avg_heart_rate:.1f} bpm
            </div>
            <div class="copy">
                <strong style="color:#f5f7fa;">
                    Sleep coverage:
                </strong>
                {sleep_coverage:.1f}%
            </div>
        </div>
        """
    )

# PLOTLY CONFIG
chart_config = {
    "displayModeBar": False,
    "responsive": True,
}

# EXECUTIVE SNAPSHOT
with st.container(border=True):
    render_html(
        """
        <div class="section-header">
            <div class="section-label">
                EXECUTIVE READOUT
            </div>
            <div class="section-title">
                Wellness performance at a glance
            </div>
            <div class="section-copy">
                Headline sleep and cardiovascular measures for the
                currently selected operating population.
            </div>
        </div>
        """
    )
    render_html(
        '<div class="kpi-content">'
    )
    k1, k2, k3, k4 = st.columns(
        4,
        gap="medium",
    )
    with k1:
        st.metric(
            "Avg Sleep",
            f"{avg_sleep:.1f} hrs",
        )
    with k2:
        st.metric(
            "7h Target",
            f"{target_rate:.1f}%",
        )
    with k3:
        st.metric(
            "Sleep Efficiency",
            f"{sleep_efficiency:.1f}%",
        )
    with k4:
        st.metric(
            "Avg Heart Rate",
            f"{avg_heart_rate:.1f} bpm",
        )
    render_html("</div>")

# BUSINESS SIGNALS
with st.container(border=True):
    render_html(
        """
        <div class="section-header">
            <div class="section-label">
                BUSINESS SIGNALS
            </div>
            <div class="section-title">
                Wellness operating signals
            </div>
            <div class="section-copy">
                Additional measures provide operational context around
                sleep coverage, activity, and sedentary behavior.
            </div>
        </div>
        """
    )
    render_html(
        f"""
        <div class="signals-content">
            <div class="signal-grid">
                <div class="signal-card">
                    <div class="signal-title">
                        Median sleep
                    </div>
                    <div class="signal-value">
                        {median_sleep:.1f} hrs
                    </div>
                    <div class="signal-copy">
                        Median recorded sleep duration across
                        participant-days with sleep observations.
                    </div>
                </div>
                <div class="signal-card">
                    <div class="signal-title">
                        10K goal attainment
                    </div>
                    <div class="signal-value">
                        {goal_attainment:.1f}%
                    </div>
                    <div class="signal-copy">
                        Share of selected participant-days reaching
                        at least 10,000 steps.
                    </div>
                </div>
                <div class="signal-card">
                    <div class="signal-title">
                        Sedentary exposure
                    </div>
                    <div class="signal-value">
                        {sedentary_exposure:,.0f} min/day
                    </div>
                    <div class="signal-copy">
                        Average recorded sedentary time per
                        participant-day in the selected population.
                    </div>
                </div>
                <div class="signal-card">
                    <div class="signal-title">
                        Sleep coverage
                    </div>
                    <div class="signal-value">
                        {sleep_coverage:.1f}%
                    </div>
                    <div class="signal-copy">
                        Share of selected participant-days containing
                        a recorded sleep observation.
                    </div>
                </div>
            </div>
        </div>
        """
    )

# SLEEP PATTERNS
with st.container(border=True):
    render_html(
        """
        <div class="section-header">
            <div class="section-label">
                SLEEP PATTERNS
            </div>
            <div class="section-title">
                Recorded sleep behavior
            </div>
            <div class="section-copy">
                Distribution of recorded sleep duration and its
                observational relationship with daily activity.
            </div>
        </div>
        """
    )
    left, right = st.columns(
        2,
        gap="medium",
    )

    # SLEEP DISTRIBUTION
    with left:
        render_html(
            """
            <div class="sleep-chart-content">
                <div class="sleep-chart-title">
                    Sleep Duration Distribution
                </div>
                <div class="sleep-chart-copy">
                    Recorded sleep duration across participant-days.
                </div>
            </div>
            """
        )
        sleep_distribution = sleep[
            ["Sleep_Minutes"]
        ].dropna()
        if len(sleep_distribution) >= 1:
            fig = px.histogram(
                sleep_distribution,
                x="Sleep_Minutes",
                nbins=25,
            )
            fig.update_traces(
                marker_line_width=0,
            )
            fig.update_layout(
                xaxis_title="Sleep duration (minutes)",
                yaxis_title="Participant-days",
            )
            fig = configure_plot(
                fig,
                height=360,
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=chart_config,
            )
        else:
            render_html(
                """
                <div class="wellness-empty">
                    No sleep-duration observations are available.
                </div>
                """
            )

    # SLEEP VS STEPS
    with right:
        render_html(
            """
            <div class="sleep-chart-content">
                <div class="sleep-chart-title">
                    Sleep vs Steps
                </div>
                <div class="sleep-chart-copy">
                    Observational relationship between recorded sleep
                    and daily step volume.
                </div>
            </div>
            """
        )
        scatter_columns = [
            "Sleep_Minutes",
            "TotalSteps",
        ]
        scatter_data = sleep[
            scatter_columns
        ].dropna()
        hover_fields = [
            column
            for column in ["Id", "Date"]
            if column in sleep.columns
        ]
        if not scatter_data.empty:
            scatter_data = sleep.dropna(
                subset=[
                    "Sleep_Minutes",
                    "TotalSteps",
                ]
            )
            fig = px.scatter(
                scatter_data,
                x="Sleep_Minutes",
                y="TotalSteps",
                hover_data=hover_fields,
            )
            fig.update_layout(
                xaxis_title="Sleep duration (minutes)",
                yaxis_title="Total steps",
            )
            fig = configure_plot(
                fig,
                height=360,
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=chart_config,
            )
        else:
            render_html(
                """
                <div class="wellness-empty">
                    Insufficient paired sleep and step observations
                    are available for this view.
                </div>
                """
            )

# CORRELATIONS
corr_cols = [
    "Sleep_Minutes",
    "Sleep_Efficiency_Pct",
    "TotalSteps",
    "Calories",
    "Total_Active_Minutes",
    "SedentaryMinutes",
]
available_corr_cols = [
    column
    for column in corr_cols
    if column in sleep.columns
]
corr = sleep[
    available_corr_cols
].corr()
corr = corr.dropna(
    axis=0,
    how="all",
)
corr = corr.dropna(
    axis=1,
    how="all",
)
with st.container(border=True):
    render_html(
        """
        <div class="section-header">
            <div class="section-label">
                RELATIONSHIPS
            </div>
            <div class="section-title">
                Sleep &amp; activity correlations
            </div>
            <div class="section-copy">
                Pairwise Pearson correlations across the available
                sleep and activity measures.
            </div>
        </div>
        """
    )
    if (
        not corr.empty
        and corr.shape[0] >= 2
        and corr.shape[1] >= 2
    ):
        fig = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
        )
        fig.update_layout(
            coloraxis_colorbar=dict(
                title="r",
            )
        )
        fig = configure_plot(
            fig,
            height=430,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=chart_config,
        )
    else:
        render_html(
            """
            <div class="wellness-empty">
                Not enough numeric observations are available to
                calculate the correlation matrix.
            </div>
            """
        )

# SLEEP BY DAY OF WEEK
day_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
week = (
    sleep[
        [
            "Day_Of_Week",
            "Sleep_Minutes",
        ]
    ]
    .dropna(
        subset=[
            "Day_Of_Week",
            "Sleep_Minutes",
        ]
    )
    .groupby(
        "Day_Of_Week",
        as_index=False,
    )
    .agg(
        Avg_Sleep=(
            "Sleep_Minutes",
            "mean",
        ),
        Participant_Days=(
            "Sleep_Minutes",
            "size",
        ),
    )
)
if not week.empty:
    week["Day_Of_Week"] = pd.Categorical(
        week["Day_Of_Week"],
        categories=day_order,
        ordered=True,
    )
    week = (
        week
        .sort_values("Day_Of_Week")
        .reset_index(drop=True)
    )
with st.container(border=True):
    render_html(
        """
        <div class="section-header">
            <div class="section-label">
                WEEKLY PATTERN
            </div>
            <div class="section-title">
                Sleep by day of week
            </div>
            <div class="section-copy">
                Average recorded sleep duration by day of the week.
            </div>
        </div>
        """
    )
    if not week.empty:
        fig = px.bar(
            week,
            x="Day_Of_Week",
            y="Avg_Sleep",
            text_auto=".0f",
            hover_data={
                "Participant_Days": True,
                "Avg_Sleep": ":.1f",
            },
        )
        fig.update_layout(
            yaxis_title="Average sleep (minutes)",
            xaxis_title="",
        )
        fig = configure_plot(
            fig,
            height=390,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=chart_config,
        )
    else:
        render_html(
            """
            <div class="wellness-empty">
                No day-of-week sleep observations are available.
            </div>
            """
        )

# INTERPRETATION
render_html(
    """
    <div class="sleep-note">
        <strong>Interpretation:</strong>
        These measures describe recorded participant-day behavior
        and observational relationships in the available data.
        Correlations describe statistical association only and
        should not be interpreted as causal or clinical effects.
    </div>
    """
)

# DASHBOARD LOADED
render_html(
    """
    <div
        class="dashboard-loaded"
        aria-hidden="true"
        style="
            width:0;
            height:0;
            overflow:hidden;
            opacity:0;
            pointer-events:none;
        "
    ></div>
    """
)