# pages/5_Statistical_Analysis.py
import base64
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import streamlit as st
from utils.data import load_data, activity_groups

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Statistical Analysis | Fitness Analytics",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# SAFE HTML RENDERER
def render_html(html: str):
    """
    Compatible HTML renderer for different Streamlit versions.
    """
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(
            html,
            unsafe_allow_html=True,
        )

# NUMBER / TEXT HELPERS
def safe_float(value, default=0.0):
    try:
        value = float(value)
        if np.isfinite(value):
            return value
        return default
    except Exception:
        return default

def format_p_value(value):
    """
    Executive-friendly p-value formatting.
    """
    value = safe_float(value)
    if value < 0.001:
        return "<0.001"
    return f"{value:.4g}"

def format_number(value, decimals=0):
    value = safe_float(value)
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"

def significance_text(p_value):
    """
    Descriptive significance statement.
    """
    p_value = safe_float(p_value)
    if p_value < 0.001:
        return "statistically significant (p < 0.001)"
    if p_value < 0.01:
        return f"statistically significant (p = {p_value:.4f})"
    if p_value < 0.05:
        return f"statistically significant (p = {p_value:.4f})"
    return f"not statistically significant (p = {p_value:.4f})"


def correlation_strength(r):
    """
    Descriptive interpretation of absolute correlation magnitude.
    """
    r = abs(safe_float(r))
    if r < 0.10:
        return "very weak"
    if r < 0.30:
        return "weak"
    if r < 0.50:
        return "moderate"
    if r < 0.70:
        return "strong"
    return "very strong"

def correlation_direction(r):
    r = safe_float(r)
    if r > 0:
        return "positive"
    if r < 0:
        return "negative"
    return "neutral"

def html_escape(value):
    """
    Basic HTML escaping for values inserted into rendered HTML.
    """
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

# STRAVA LOGO
ROOT_DIR = Path(__file__).resolve().parent.parent
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
        ).decode("utf-8")
        suffix = LOGO_PATH.suffix.lower()
        mime_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(
            suffix,
            "image/png",
        )
        logo_html = (
            f'<img src="data:{mime_type};base64,{logo_b64}" '
            f'alt="Strava logo">'
        )
    except Exception:
        logo_html = ""

# DATA
df = load_data()
global_filtered = st.session_state.get(
    "global_filtered",
    df,
)
if global_filtered is not None:
    df = global_filtered.copy()
else:
    df = df.copy()

# EMPTY DATA PROTECTION
if df is None or len(df) == 0:
    render_html(
        """
        <div style="
            margin:40px 0;
            padding:30px;
            border:1px solid rgba(255,255,255,0.12);
            border-radius:14px;
            background:rgba(15,17,22,0.85);
            color:white;
        ">
            <div style="
                color:#ff6b1a;
                font-size:0.65rem;
                font-weight:900;
                letter-spacing:0.15em;
                text-transform:uppercase;
                margin-bottom:10px;
            ">
                STATISTICAL ANALYSIS
            </div>
            <div style="
                font-size:1.25rem;
                font-weight:800;
                margin-bottom:8px;
            ">
                No observations available
            </div>
            <div style="
                color:rgba(255,255,255,0.62);
                line-height:1.5;
            ">
                The current filtered dataset contains no records.
                Adjust the global filters to continue the analysis.
            </div>
        </div>
        """
    )
    st.stop()
activity = activity_groups(df)

# DYNAMIC SIDEBAR VALUES
record_count = len(df)
participant_count = (
    df["Id"].nunique()
    if "Id" in df.columns
    else 0
)

# Analysis period
if "Date" in df.columns and len(df):

    dates = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )
    sidebar_start = dates.min()
    sidebar_end = dates.max()
    if (
        pd.notna(sidebar_start)
        and pd.notna(sidebar_end)
    ):
        period_text = (
            f"{sidebar_start:%d %b %Y} → "
            f"{sidebar_end:%d %b %Y}"
        )
    else:
        period_text = (
            "Current filtered view"
        )
else:
    period_text = (
        "Current filtered view"
    )

# Average steps
if (
    "TotalSteps" in df.columns
    and len(df)
):
    avg_steps = safe_float(
        pd.to_numeric(
            df["TotalSteps"],
            errors="coerce",
        ).mean()
    )
else:
    avg_steps = 0.0

# Average calories
if (
    "Calories" in df.columns
    and len(df)
):
    avg_calories = safe_float(
        pd.to_numeric(
            df["Calories"],
            errors="coerce",
        ).mean()
    )
else:
    avg_calories = 0.0

# 10K goal rate
if (
    "Meets_10k_Steps" in df.columns
    and len(df)
):
    goal_values = pd.to_numeric(
        df["Meets_10k_Steps"],
        errors="coerce",
    )
    goal_rate = safe_float(
        goal_values.mean() * 100
    )
else:
    goal_rate = 0.0

# Average active minutes
if (
    "Total_Active_Minutes" in df.columns
    and len(df)
):
    avg_active = safe_float(
        pd.to_numeric(
            df["Total_Active_Minutes"],
            errors="coerce",
        ).mean()
    )
else:
    active_components = [
        c
        for c in [
            "VeryActiveMinutes",
            "FairlyActiveMinutes",
            "LightlyActiveMinutes",
        ]
        if c in df.columns
    ]
    if (
        active_components
        and len(df)
    ):
        active_frame = (
            df[active_components]
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
            .fillna(0)
        )
        avg_active = safe_float(
            active_frame
            .sum(axis=1)
            .mean()
        )
    else:
        avg_active = 0.0

# Average sedentary minutes
if (
    "SedentaryMinutes" in df.columns
    and len(df)
):
    avg_sedentary = safe_float(
        pd.to_numeric(
            df["SedentaryMinutes"],
            errors="coerce",
        ).mean()
    )
else:
    avg_sedentary = 0.0

# Active share
if (
    "Total_Active_Minutes" in df.columns
    and len(df)
):
    active_values = pd.to_numeric(
        df["Total_Active_Minutes"],
        errors="coerce",
    )
    active_share = safe_float(
        active_values.gt(0).mean()
        * 100
    )
else:
    active_share = 0.0

# High sedentary rate
if (
    "SedentaryMinutes" in df.columns
    and len(df)
):
    sedentary_values = pd.to_numeric(
        df["SedentaryMinutes"],
        errors="coerce",
    )
    high_sedentary_rate = safe_float(
        sedentary_values.ge(600).mean()
        * 100
    )
else:
    high_sedentary_rate = 0.0

# GLOBAL THEME
render_html(
    """
    <style>
    /* ========================================================
       ROOT
       ======================================================== */
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
    }
    /* ========================================================
       APP BACKGROUND
       ======================================================== */
    .stApp {
        background:
            radial-gradient(
                circle at 88% 3%,
                rgba(252,82,0,0.065),
                transparent 25%
            ),
            linear-gradient(
                180deg,
                #0b0d10 0%,
                #090b0e 100%
            );
        color:var(--text);
    }
    [data-testid="stAppViewContainer"] {
        background:transparent;
    }
    [data-testid="stHeader"] {
        background:transparent;
    }
    /* ========================================================
       SIDEBAR
       ======================================================== */
    [data-testid="stSidebar"] {
        width:320px !important;
        min-width:320px !important;
        max-width:320px !important;
        background:
            linear-gradient(
                180deg,
                #0d0f13 0%,
                #0b0d10 100%
            ) !important;
        border-right:
            1px solid #292d34 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        width:320px !important;
        background:
            linear-gradient(
                180deg,
                #0d0f13 0%,
                #0b0d10 100%
            ) !important;
        padding:0 !important;
    }
    [data-testid="stSidebarContent"] {
        padding:
            0 16px 28px 16px !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top:0 !important;
    }
    [data-testid="stSidebar"] ::-webkit-scrollbar {
        width:7px;
    }
    [data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background:transparent;
    }
    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background:#30353e;
        border-radius:10px;
    }
    /* ========================================================
       NATIVE STREAMLIT SIDEBAR NAVIGATION
       ======================================================== */
    [data-testid="stSidebarNav"] {
        padding-top:0.35rem !important;
    }
    [data-testid="stSidebarNav"] ul {
        padding-top:0 !important;
    }
    [data-testid="stSidebarNav"] li {
        margin:0 !important;
    }
    [data-testid="stSidebarNav"] a {
        border-radius:7px !important;
        margin:2px 8px !important;
        padding:0 10px !important;
        height:40px !important;
        min-height:40px !important;
        box-sizing:border-box !important;
        display:flex !important;
        align-items:center !important;
        color:
            rgba(255,255,255,0.70) !important;
        font-size:13px !important;
        font-weight:700 !important;
        line-height:1.15 !important;
        transition:
            background 0.15s ease,
            border 0.15s ease,
            color 0.15s ease !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        color:#ffffff !important;
        background:
            rgba(255,107,26,0.08) !important;
        border:
            1px solid
            rgba(255,107,26,0.20) !important;
    }
    [data-testid="stSidebarNav"]
    a[aria-current="page"] {
        color:#ffffff !important;
        background:
            linear-gradient(
                90deg,
                rgba(255,107,26,0.20),
                rgba(255,107,26,0.07)
            ) !important;
        border:
            1px solid
            rgba(255,107,26,0.42) !important;
        box-shadow:
            inset 3px 0 0 #ff6b1a,
            0 4px 12px
            rgba(0,0,0,0.18)
            !important;
        padding:0 10px !important;
        height:40px !important;
        min-height:40px !important;
        box-sizing:border-box !important;
        font-weight:800 !important;
    }
    /* ========================================================
       SIDEBAR CONTENT
       ======================================================== */

    .fitness-sidebar-divider {
        height:1px;
        margin:
            14px 0 17px 0;
        background:
            rgba(255,255,255,0.12);
    }
    .fitness-sidebar-label {
        color:#ff6b1a;
        font-size:0.54rem;
        font-weight:850;
        letter-spacing:0.14em;
        margin:
            15px 2px 7px 2px;
        text-transform:uppercase;
    }
    .fitness-sidebar-card {
        padding:
            10px 11px;
        border-radius:8px;
        background:
            rgba(14,16,22,0.82);
        border:
            1px solid
            rgba(255,255,255,0.10);
        margin-bottom:12px;
    }
    .fitness-sidebar-item-title {
        color:
            rgba(255,255,255,0.90);
        font-size:0.62rem;
        font-weight:750;
        margin-top:4px;
        margin-bottom:4px;
    }
    .fitness-sidebar-item-text {
        color:
            rgba(255,255,255,0.45);
        font-size:0.53rem;
        line-height:1.4;
        margin:
            2px 0 6px 0;
    }
    .fitness-sidebar-tech {
        color:
            rgba(255,255,255,0.72);
        font-size:0.61rem;
        line-height:1.7;
    }
    /* ========================================================
       MAIN CONTENT
       ======================================================== */
    .block-container {
        max-width:none !important;
        width:100% !important;
        margin-left:0 !important;
        margin-right:0 !important;
        padding-top:72px !important;
        padding-left:22px !important;
        padding-right:24px !important;
        padding-bottom:4rem !important;
    }
    .block-container > div {
        max-width:none !important;
        width:100% !important;
    }
    /* ========================================================
       HERO
       ======================================================== */
    .statistical-hero {
        position:relative;
        isolation:isolate;
        overflow:hidden;
        border:1px solid rgba(255,255,255,0.16);
        border-radius:20px;
        padding:18px 28px 19px 28px;
        margin:0 0 18px 0;
        background:
            linear-gradient(105deg,
                rgba(25,37,54,0.48) 0%,
                rgba(16,22,31,0.38) 44%,
                rgba(55,25,14,0.42) 100%);
        box-shadow:
            0 18px 50px rgba(0,0,0,0.34),
            inset 0 1px 0 rgba(255,255,255,0.10),
            inset 0 -1px 0 rgba(0,0,0,0.20);
        backdrop-filter:blur(30px) saturate(165%);
        -webkit-backdrop-filter:blur(30px) saturate(165%);
    }
    .statistical-hero::before {
        content:"";
        position:absolute;
        z-index:0;
        inset:-42% -10%;
        background:
            radial-gradient(ellipse at 5% 50%,
                rgba(49,78,111,0.98) 0%,
                rgba(49,78,111,0.82) 18%,
                rgba(49,78,111,0.42) 39%,
                transparent 66%),
            radial-gradient(ellipse at 96% 42%,
                rgba(255,74,8,0.98) 0%,
                rgba(255,74,8,0.82) 18%,
                rgba(255,74,8,0.40) 40%,
                transparent 67%),
            radial-gradient(ellipse at 52% 115%,
                rgba(13,24,39,0.95) 0%,
                rgba(13,24,39,0.58) 30%,
                transparent 68%);
        filter:blur(52px) saturate(125%);
        transform:scale(1.08);
        opacity:0.92;
        pointer-events:none;
    }
    .statistical-hero::after {
        content:"";
        position:absolute;
        z-index:1;
        inset:0;
        background:
            linear-gradient(105deg,
                rgba(130,170,210,0.10) 0%,
                rgba(255,255,255,0.035) 45%,
                rgba(255,116,54,0.10) 100%),
            radial-gradient(circle at 78% 20%,
                rgba(255,255,255,0.09) 0%,
                transparent 30%);
        box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.025);
        pointer-events:none;
    }
    .statistical-hero > * {
        position:relative;
        z-index:3;
    }
    /* ========================================================
       HERO CONTENT
       ======================================================== */
    .statistical-eyebrow {
        color:#ff6b1a;
        font-size:0.60rem;
        font-weight:900;
        letter-spacing:0.155em;
        text-transform:uppercase;
        margin-bottom:6px;
    }
    .statistical-title-row {
        display:flex;
        align-items:center;
        gap:10px;
        margin-bottom:7px;
    }
    .statistical-logo {
        width:40px;
        height:40px;
        min-width:40px;
        display:flex;
        align-items:center;
        justify-content:center;
    }
    .statistical-logo img {
        width:29px;
        height:29px;
        object-fit:contain;
        display:block;
    }
    .statistical-title {
        display: inline-block;
        color: #ffffff;
        font-family: "Arial Rounded MT Bold", "Arial Black", "Trebuchet MS", "Helvetica Neue", Arial, sans-serif;
        font-size: clamp(2.05rem, 2.85vw, 2.85rem);
        font-weight: 900;
        letter-spacing: -1.65px;
        line-height: 0.96;
        white-space: nowrap;
        -webkit-font-smoothing: antialiased;
        text-rendering: geometricPrecision;
    }
    .statistical-title-orange {
        color:#ff6b1a;
    }
    .statistical-description {
        max-width:1100px;
        color:
            rgba(255,255,255,0.76);
        font-size:0.82rem;
        line-height:1.40;
        margin:0;
    }
    /* ========================================================
       EXECUTIVE READOUT
       ======================================================== */
    .executive-readout {
        padding:
            15px 16px 16px 16px;
        border:
            1px solid
            rgba(255,255,255,0.10);
        border-radius:12px;
        background:
            rgba(14,16,22,0.70);
        margin-bottom:28px;
    }
    .executive-label {
        color:#ff6b1a;
        font-size:0.57rem;
        font-weight:900;
        letter-spacing:0.16em;
        text-transform:uppercase;
        margin-bottom:7px;
    }
    .executive-title {
        color:#ffffff;
        font-size:0.90rem;
        font-weight:850;
        margin-bottom:6px;
    }
    .executive-copy {
        color:
            rgba(255,255,255,0.60);
        font-size:0.72rem;
        line-height:1.55;
    }
    /* ========================================================
       EXECUTIVE OVERVIEW KPI STRIP
       ======================================================== */
    .overview-kpi-grid {
        display:grid;
        grid-template-columns:
            repeat(4, minmax(0,1fr));
        gap:14px;
        margin-bottom:30px;
    }
    .overview-kpi {
        min-height:94px;
        padding:
            14px 15px;
        border:
            1px solid
            rgba(255,255,255,0.10);
        border-radius:12px;
        background:
            rgba(14,16,22,0.72);
    }
    .overview-kpi-label {
        color:
            rgba(255,255,255,0.45);
        font-size:0.52rem;
        font-weight:850;
        letter-spacing:0.10em;
        text-transform:uppercase;
        margin-bottom:8px;
    }
    .overview-kpi-value {
        color:#ffffff;
        font-size:1.05rem;
        font-weight:850;
        line-height:1.15;
    }
    .overview-kpi-note {
        color:
            rgba(255,255,255,0.38);
        font-size:0.52rem;
        line-height:1.3;
        margin-top:5px;
    }
    /* ========================================================
       SECTION HEADINGS
       ======================================================== */
    .stat-section {
        margin-top:28px;
        margin-bottom:30px;
        padding:0;
    }
    .stat-section-label {
        color:#ff6b1a;
        font-size:0.57rem;
        font-weight:900;
        letter-spacing:0.15em;
        text-transform:uppercase;
        margin-bottom:5px;
    }
    .stat-section-title {
        color:#ffffff;
        font-size:1.65rem;
        font-weight:900;
        line-height:1.15;
        letter-spacing:-0.025em;
        margin-bottom:7px;
    }
    .stat-section-copy {
        color:
            rgba(255,255,255,0.66);
        font-size:0.82rem;
        line-height:1.55;
        margin-bottom:17px;
    }
    /* ========================================================
       SECTION RECTANGLES
       ======================================================== */
    .analysis-panel {
        border:
            1px solid
            rgba(255,255,255,0.10);
        border-radius:13px;
        background:
            rgba(13,15,20,0.56);
        padding:
            18px 16px 16px 16px;
        margin-bottom:22px;
    }
    /* ========================================================
       KPI CARDS
       ======================================================== */
    .kpi-grid {
        display:grid;
        grid-template-columns:
            repeat(4, minmax(0,1fr));
        gap:14px;
        margin:
            0 0 16px 0;
    }
    .kpi-card {
        min-height:95px;
        padding:
            14px 15px;
        border:
            1px solid
            rgba(255,255,255,0.09);
        border-radius:11px;
        background:
            rgba(14,16,22,0.82);
    }
    .kpi-label {
        color:
            rgba(255,255,255,0.50);
        font-size:0.57rem;
        font-weight:750;
        margin-bottom:8px;
    }
    .kpi-value {
        color:#ffffff;
        font-size:1.58rem;
        font-weight:500;
        line-height:1.05;
        letter-spacing:-0.02em;
    }
    .kpi-note {
        color:
            rgba(255,255,255,0.36);
        font-size:0.50rem;
        line-height:1.3;
        margin-top:7px;
    }
    /* ========================================================
       INTERPRETATION
       ======================================================== */
    .statistical-interpretation {
        border-left:
            3px solid #ff6b1a;
        background:
            rgba(18,20,26,0.76);
        border-radius:
            0 8px 8px 0;
        padding:
            10px 13px;
        margin:
            12px 0 17px 0;
    }
    .statistical-interpretation-title {
        color:#ffffff;
        font-size:0.61rem;
        font-weight:850;
        margin-bottom:5px;
    }
    .statistical-interpretation-text {
        color:
            rgba(255,255,255,0.53);
        font-size:0.58rem;
        line-height:1.48;
    }
    .statistical-interpretation-text strong {
        color:
            rgba(255,255,255,0.78);
    }
    /* ========================================================
       BUSINESS USE
       ======================================================== */
    .business-use {
        border:
            1px solid
            rgba(255,255,255,0.10);
        border-radius:12px;
        background:
            rgba(14,16,22,0.72);
        padding:
            16px 16px;
        margin:
            22px 0 26px 0;
    }
    .business-use-label {
        color:#ff6b1a;
        font-size:0.56rem;
        font-weight:900;
        letter-spacing:0.15em;
        text-transform:uppercase;
        margin-bottom:6px;
    }
    .business-use-title {
        color:#ffffff;
        font-size:0.86rem;
        font-weight:850;
        margin-bottom:6px;
    }
    .business-use-copy {
        color:
            rgba(255,255,255,0.55);
        font-size:0.62rem;
        line-height:1.55;
    }
    /* ========================================================
       STREAMLIT CONTENT
       ======================================================== */
    h1, h2, h3, h4, h5, h6 {
        color:#ffffff !important;
    }
    p, label {
        color:
            rgba(255,255,255,0.82);
    }
    div[data-testid="stMetric"] {
        background:
            rgba(14,16,22,0.72);
        border:
            1px solid
            rgba(255,255,255,0.09);
        border-radius:12px;
        padding:
            0.75rem 0.85rem;
    }
    div[data-testid="stMetricLabel"] {
        color:
            rgba(255,255,255,0.62)
            !important;
    }
    div[data-testid="stMetricValue"] {
        color:#ffffff !important;
    }
    /* ========================================================
       SELECTBOX
       ======================================================== */
    div[data-baseweb="select"] > div {
        background:
            #24252e !important;
        border:
            1px solid
            rgba(255,255,255,0.05) !important;
        color:#ffffff !important;
        border-radius:8px !important;
    }
    /* ========================================================
       EXECUTIVE ANALYSIS CONTAINER
       ======================================================== */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border:1px solid rgba(255,255,255,0.10) !important;
        border-radius:13px !important;
        background:rgba(13,15,20,0.56) !important;
        box-shadow:none !important;
        padding:0.25rem 0.35rem !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius:13px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .stat-section {
        margin-top:8px;
        margin-bottom:14px;
    }

    /* ========================================================
       DATAFRAME
       ======================================================== */
    [data-testid="stDataFrame"] {
        border-radius:10px;
        overflow:hidden;
    }
    /* ========================================================
       WARNING / FINAL NOTE
       ======================================================== */
    .statistical-caveat {
        border-radius:10px;
        background:
            rgba(85,88,8,0.60);
        border:
            1px solid
            rgba(160,165,30,0.25);
        padding:
            14px 16px;
        color:
            rgba(255,255,255,0.78);
        font-size:0.70rem;
        line-height:1.55;
        margin-top:22px;
    }
    /* ========================================================
       RESPONSIVE
       ======================================================== */
    @media (max-width: 1100px) {
        .overview-kpi-grid,
        .kpi-grid {
            grid-template-columns:
                repeat(2, minmax(0,1fr));
        }
    }
    @media (max-width: 700px) {
        .overview-kpi-grid,
        .kpi-grid {
            grid-template-columns:
                1fr;
        }
        .statistical-title {
            font-size:1.75rem;
            letter-spacing:-1.15px;
        }
        .block-container {
            padding-left:14px !important;
            padding-right:14px !important;
        }
    }
    </style>
    """
)

# DYNAMIC SIDEBAR
with st.sidebar:

    render_html(
        f"""
        <div class="fitness-sidebar-divider"></div>
        <div class="fitness-sidebar-card">
            <div class="fitness-sidebar-label">
                STATISTICAL ANALYSIS
            </div>
            <div class="fitness-sidebar-item-title">
                Executive decision support
            </div>
            <div class="fitness-sidebar-item-text">
                Evidence-based comparison of activity groups,
                variable relationships, and weekday-versus-weekend
                behavior.
            </div>
            <div class="fitness-sidebar-item-title">
                Current view
            </div>
            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">
                    Analysis period:
                </strong><br>
                {html_escape(period_text)}
            </div>
            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">
                    Participant-days:
                </strong>
                {record_count:,}
            </div>
            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">
                    Participants:
                </strong>
                {participant_count:,}
            </div>
            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">
                    Avg steps:
                </strong>
                {avg_steps:,.0f}
            </div>
            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">
                    Avg calories:
                </strong>
                {avg_calories:,.0f}
            </div>
            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">
                    10K goal rate:
                </strong>
                {goal_rate:.1f}%
            </div>
        </div>
        <div class="fitness-sidebar-label">
            CURRENT ANALYTICS
        </div>
        <div class="fitness-sidebar-card fitness-sidebar-tech">
            <div>
                Active share: {active_share:.1f}%
            </div>
            <div>
                Avg active minutes: {avg_active:,.0f}
            </div>
            <div>
                Avg sedentary minutes: {avg_sedentary:,.0f}
            </div>
            <div>
                High sedentary rate: {high_sedentary_rate:.1f}%
            </div>
        </div>
        """
    )

# HERO
render_html(
    f"""
    <div class="statistical-hero">
        <div class="statistical-eyebrow">
            HOME &nbsp;•&nbsp; STATISTICAL ANALYSIS
        </div>
        <div class="statistical-title-row">
            <div class="statistical-logo">
                {logo_html}
            </div>
            <h1 class="statistical-title">
                <span class="statistical-title-orange">
                    Statistical
                </span>
                <span> Analysis</span>
            </h1>
        </div>
        <div class="statistical-description">
            Executive-grade statistical evidence for comparing
            activity segments, quantifying relationships, and
            identifying measurable differences in observed behavior.
        </div>
    </div>
    """
)

# EXECUTIVE READOUT
render_html(
    """
    <div class="executive-readout">
        <div class="executive-label">
            EXECUTIVE READOUT
        </div>
        <div class="executive-title">
            What this page is designed to answer
        </div>
        <div class="executive-copy">
            This page answers three management-level questions:
            whether observed activity groups differ in calorie
            expenditure, whether selected variables move together,
            and whether weekday and weekend activity distributions
            differ. Statistical significance, effect magnitude,
            sample size, and observed differences are reported
            separately so that a small p-value is not mistaken
            for business materiality.
        </div>
    </div>
    """
)

# EXECUTIVE KPI STRIP
render_html(
    f"""
    <div class="overview-kpi-grid">
        <div class="overview-kpi">
            <div class="overview-kpi-label">
                OBSERVATIONS
            </div>
            <div class="overview-kpi-value">
                {record_count:,}
            </div>
            <div class="overview-kpi-note">
                Participant-day records in the current view.
            </div>
        </div>

        <div class="overview-kpi">
            <div class="overview-kpi-label">
                PARTICIPANTS
            </div>
            <div class="overview-kpi-value">
                {participant_count:,}
            </div>
            <div class="overview-kpi-note">
                Unique participants where ID is available.
            </div>
        </div>

        <div class="overview-kpi">
            <div class="overview-kpi-label">
                ANALYSIS PERIOD
            </div>

            <div class="overview-kpi-value">
                {html_escape(period_text)}
            </div>

            <div class="overview-kpi-note">
                Based on the current filtered dataset.
            </div>
        </div>

        <div class="overview-kpi">
            <div class="overview-kpi-label">
                EVIDENCE STANDARD
            </div>

            <div class="overview-kpi-value">
                Significance + magnitude
            </div>

            <div class="overview-kpi-note">
                Findings are not treated as causal evidence.
            </div>
        </div>
    </div>
    """
)

# 1. ACTIVITY GROUPS VS CALORIE EXPENDITURE
required_activity_columns = {
    "Activity_Level",
    "Calories",
}

activity_ready = required_activity_columns.issubset(
    set(activity.columns)
)

with st.container(border=True):
    render_html(
        """
        <div class="stat-section-title">
            1. Activity Groups vs Calorie Expenditure
        </div>
        <div class="stat-section-copy">
            Tests whether calorie distributions differ across the
            Low, Moderate, and High Activity groups. The analysis
            reports both statistical evidence and effect magnitude.
        </div>
        """
    )

    if activity_ready:
        activity = activity.copy()
        activity["Calories"] = pd.to_numeric(
            activity["Calories"],
            errors="coerce",
        )

        groups = []
        group_labels = [
            "Low Activity",
            "Moderate Activity",
            "High Activity",
        ]

        for label in group_labels:
            values = (
                activity.loc[
                    activity["Activity_Level"] == label,
                    "Calories",
                ]
                .dropna()
            )
            if len(values):
                groups.append(values)

        if len(groups) >= 2:
            h_stat, p_value = stats.kruskal(*groups)
            n = sum(len(g) for g in groups)
            denominator = n - len(groups)

            if denominator > 0:
                epsilon_sq = max(
                    0.0,
                    (
                        h_stat
                        - len(groups)
                        + 1
                    ) / denominator,
                )
            else:
                epsilon_sq = 0.0

            summary = (
                activity
                .groupby(
                    "Activity_Level",
                    observed=True,
                )["Calories"]
                .agg(
                    [
                        "count",
                        "mean",
                        "median",
                    ]
                )
                .reset_index()
            )

            # KPI cards are part of the same bordered container.
            k1, k2, k3, k4 = st.columns(4)
            kpi_data = [
                (
                    k1,
                    "KRUSKAL-WALLIS H",
                    f"{h_stat:.4f}",
                    "Distributional test statistic.",
                ),
                (
                    k2,
                    "P-VALUE",
                    format_p_value(p_value),
                    "Statistical evidence against equal distributions.",
                ),
                (
                    k3,
                    "EPSILON-SQUARED",
                    f"{epsilon_sq:.4f}",
                    "Estimated distributional effect magnitude.",
                ),
                (
                    k4,
                    "OBSERVATIONS",
                    f"{n:,}",
                    "Records included in this test.",
                ),
            ]

            for col, label, value, note in kpi_data:
                with col:
                    render_html(
                        f"""
                        <div class="kpi-card">
                            <div class="kpi-label">{label}</div>
                            <div class="kpi-value">{value}</div>
                            <div class="kpi-note">{note}</div>
                        </div>
                        """
                    )

            render_html(
                f"""
                <div class="statistical-interpretation">
                    <div class="statistical-interpretation-title">
                        Executive interpretation
                    </div>
                    <div class="statistical-interpretation-text">
                        The observed calorie distributions are
                        <strong>{significance_text(p_value)}</strong>
                        across the activity groups. The estimated
                        epsilon-squared effect is
                        <strong>{epsilon_sq:.4f}</strong>.
                        The test identifies distributional differences;
                        it does not establish that activity level causes
                        calorie expenditure differences.
                    </div>
                </div>
                """
            )

            st.markdown("**Activity level summary**")
            st.dataframe(
                summary.style.format(
                    {
                        "count": "{:,.0f}",
                        "mean": "{:,.0f}",
                        "median": "{:,.0f}",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            plot_activity = activity[
                [
                    "Activity_Level",
                    "Calories",
                ]
            ].dropna()

            fig_activity = px.box(
                plot_activity,
                x="Activity_Level",
                y="Calories",
                points="outliers",
                category_orders={
                    "Activity_Level": [
                        "High Activity",
                        "Moderate Activity",
                        "Low Activity",
                    ]
                },
                title="Calorie Distribution by Activity Group",
            )

            fig_activity.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(
                    l=20,
                    r=20,
                    t=55,
                    b=20,
                ),
            )

            st.plotly_chart(
                fig_activity,
                use_container_width=True,
                key="activity_calorie_distribution",
            )

        else:
            render_html(
                """
                <div class="statistical-interpretation">
                    <div class="statistical-interpretation-title">
                        Insufficient observations
                    </div>
                    <div class="statistical-interpretation-text">
                        At least two non-empty activity groups are
                        required to perform the Kruskal-Wallis test.
                    </div>
                </div>
                """
            )

    else:
        render_html(
            """
            <div class="statistical-interpretation">
                <div class="statistical-interpretation-title">
                    Required fields unavailable
                </div>
                <div class="statistical-interpretation-text">
                    Activity_Level and Calories are required for this analysis.
                </div>
            </div>
            """
        )

# 2. CORRELATION EXPLORER
with st.container(border=True):
    render_html(
        """
        <div class="stat-section-title">
            2. Correlation Explorer
        </div>
        <div class="stat-section-copy">
            Quantifies the direction and strength of association between
            two selected numeric variables using both Pearson and Spearman
            correlation.
        </div>
        """
    )

    numeric = (
        df
        .select_dtypes(include="number")
        .columns
        .tolist()
    )

    if len(numeric) >= 2:
        default_x = (
            "Sleep_Minutes"
            if "Sleep_Minutes" in numeric
            else numeric[0]
        )

        default_y = (
            "TotalSteps"
            if "TotalSteps" in numeric
            else numeric[1]
        )

        filter_col_x, filter_col_y = st.columns(2)

        with filter_col_x:
            x = st.selectbox(
                "Variable X",
                numeric,
                index=numeric.index(default_x),
                key="statistical_correlation_x",
            )

        with filter_col_y:
            y = st.selectbox(
                "Variable Y",
                numeric,
                index=numeric.index(default_y),
                key="statistical_correlation_y",
            )

        pair = (
            df[[x, y]]
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
            .dropna()
        )

        if x == y:
            render_html(
                """
                <div class="statistical-interpretation">
                    <div class="statistical-interpretation-title">
                        Select two different variables
                    </div>
                    <div class="statistical-interpretation-text">
                        Variable X and Variable Y must be different numeric
                        fields to produce a meaningful correlation analysis.
                    </div>
                </div>
                """
            )

        elif len(pair) >= 3:
            try:
                pearson_r, pearson_p = stats.pearsonr(
                    pair[x],
                    pair[y],
                )
            except Exception:
                pearson_r = np.nan
                pearson_p = np.nan

            try:
                spearman_r, spearman_p = stats.spearmanr(
                    pair[x],
                    pair[y],
                )
            except Exception:
                spearman_r = np.nan
                spearman_p = np.nan

            regression_valid = (
                pair[x].nunique() > 1
                and pair[y].nunique() > 1
            )

            regression_r2 = np.nan
            regression_slope = np.nan
            regression_intercept = np.nan

            if regression_valid:
                try:
                    regression = stats.linregress(
                        pair[x],
                        pair[y],
                    )
                    regression_slope = safe_float(regression.slope)
                    regression_intercept = safe_float(regression.intercept)
                    regression_r2 = safe_float(regression.rvalue ** 2)
                except Exception:
                    regression_valid = False

            strength = correlation_strength(pearson_r)
            direction = correlation_direction(pearson_r)

            if safe_float(pearson_p) < 0.05:
                significance_statement = (
                    "The observed Pearson association is statistically "
                    "significant in this dataset."
                )
            else:
                significance_statement = (
                    "The observed Pearson association is not statistically "
                    "significant in this dataset."
                )

            # KPI cards — inside the same rectangle as everything below.
            k1, k2, k3, k4 = st.columns(4)
            kpi_data = [
                (
                    k1,
                    "PEARSON r",
                    f"{safe_float(pearson_r):.3f}",
                    "Linear association.",
                ),
                (
                    k2,
                    "PEARSON p",
                    format_p_value(pearson_p),
                    "Statistical evidence for Pearson association.",
                ),
                (
                    k3,
                    "SPEARMAN ρ",
                    f"{safe_float(spearman_r):.3f}",
                    "Rank-based monotonic association.",
                ),
                (
                    k4,
                    "VALID OBSERVATIONS",
                    f"{len(pair):,}",
                    "Complete X/Y observations used.",
                ),
            ]

            for col, label, value, note in kpi_data:
                with col:
                    render_html(
                        f"""
                        <div class="kpi-card">
                            <div class="kpi-label">{label}</div>
                            <div class="kpi-value">{value}</div>
                            <div class="kpi-note">{note}</div>
                        </div>
                        """
                    )

            render_html(
                f"""
                <div class="statistical-interpretation">
                    <div class="statistical-interpretation-title">
                        Relationship interpretation
                    </div>
                    <div class="statistical-interpretation-text">
                        {significance_statement}
                        The observed relationship is
                        <strong>{strength}</strong> and
                        <strong>{direction}</strong> based on Pearson r =
                        <strong>{safe_float(pearson_r):.3f}</strong>.
                        Correlation measures association and does not
                        establish causation.
                    </div>
                </div>
                """
            )

            # Correlation chart — still inside the same rectangle.
            fig_corr = px.scatter(
                pair,
                x=x,
                y=y,
                title=f"{x} vs {y}",
            )

            if regression_valid:
                x_min = safe_float(pair[x].min())
                x_max = safe_float(pair[x].max())
                x_values = np.linspace(x_min, x_max, 100)
                y_values = (
                    regression_slope * x_values
                    + regression_intercept
                )

                fig_corr.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode="lines",
                        name="Linear fit",
                        hovertemplate=(
                            "X=%{x:.2f}"
                            "<br>Predicted Y=%{y:.2f}"
                            "<extra></extra>"
                        ),
                    )
                )

            fig_corr.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(
                    l=20,
                    r=20,
                    t=55,
                    b=20,
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
            )

            st.plotly_chart(
                fig_corr,
                use_container_width=True,
                key="correlation_scatter_plot",
            )

            # Model reference — restored and kept inside the same rectangle.
            if regression_valid:
                render_html(
                    f"""
                    <div class="business-use">
                        <div class="business-use-label">
                            MODEL REFERENCE
                        </div>
                        <div class="business-use-title">
                            Linear relationship diagnostic
                        </div>
                        <div class="business-use-copy">
                            The fitted linear relationship has an estimated
                            R² of <strong>{regression_r2:.3f}</strong>.
                            This describes the proportion of observed
                            variation explained by the fitted linear
                            relationship within the selected data; it is not
                            a causal model or a forecasting guarantee.
                        </div>
                    </div>
                    """
                )

        else:
            render_html(
                """
                <div class="statistical-interpretation">
                    <div class="statistical-interpretation-title">
                        Insufficient observations
                    </div>
                    <div class="statistical-interpretation-text">
                        At least three complete observations are required
                        to calculate the correlation statistics.
                    </div>
                </div>
                """
            )

    else:
        render_html(
            """
            <div class="statistical-interpretation">
                <div class="statistical-interpretation-title">
                    Numeric variables unavailable
                </div>
                <div class="statistical-interpretation-text">
                    At least two numeric variables are required for
                    correlation analysis.
                </div>
            </div>
            """
        )

# 3. WEEKDAY VS WEEKEND
with st.container(border=True):

    # SECTION HEADER
    render_html(
        """
        <div class="stat-section correlation-section-heading">

            <div class="stat-section-label">
                STATISTICAL TEST 03
            </div>

            <div class="stat-section-title">
                3. Weekday vs Weekend
            </div>

            <div class="stat-section-copy">
                Compares observed TotalSteps distributions between
                weekdays and weekends using a two-sided Mann-Whitney
                U test, with median difference and effect magnitude
                reported separately.
            </div>

        </div>
        """
    )

    # VALIDATE REQUIRED COLUMNS
    if (
        "Is_Weekend" in df.columns
        and "TotalSteps" in df.columns
    ):

        week = df.copy()

        week["TotalSteps"] = pd.to_numeric(
            week["TotalSteps"],
            errors="coerce",
        )

        # ROBUST WEEKEND FLAG
        raw_weekend = week["Is_Weekend"]

        if pd.api.types.is_bool_dtype(raw_weekend):

            weekend_flag = (
                raw_weekend
                .fillna(False)
                .astype(bool)
            )

        else:

            weekend_text = (
                raw_weekend
                .astype(str)
                .str.strip()
                .str.lower()
            )

            weekend_flag = weekend_text.isin(
                [
                    "true",
                    "1",
                    "yes",
                    "y",
                    "weekend",
                ]
            )

        week["Day_Type"] = np.where(
            weekend_flag,
            "Weekend",
            "Weekday",
        )

        # GROUPS
        weekday = (
            week.loc[
                week["Day_Type"] == "Weekday",
                "TotalSteps",
            ]
            .dropna()
        )

        weekend = (
            week.loc[
                week["Day_Type"] == "Weekend",
                "TotalSteps",
            ]
            .dropna()
        )

        # STATISTICAL TEST
        if (
            len(weekday) >= 2
            and len(weekend) >= 2
        ):

            u_stat, mw_p = stats.mannwhitneyu(
                weekday,
                weekend,
                alternative="two-sided",
            )

            # MEDIANS
            weekday_median = safe_float(
                weekday.median()
            )

            weekend_median = safe_float(
                weekend.median()
            )

            median_difference = (
                weekend_median
                - weekday_median
            )

            # RANK-BISERIAL EFFECT SIZE
            n_weekday = len(weekday)
            n_weekend = len(weekend)

            denominator = (
                n_weekday
                * n_weekend
            )

            if denominator > 0:

                rank_biserial = (
                    2
                    * safe_float(u_stat)
                    / denominator
                    - 1
                )

            else:

                rank_biserial = 0.0

            # SUMMARY TABLE
            week_summary = (
                week
                .groupby("Day_Type")[
                    "TotalSteps"
                ]
                .agg(
                    [
                        "count",
                        "mean",
                        "median",
                    ]
                )
                .reindex(
                    [
                        "Weekday",
                        "Weekend",
                    ]
                )
                .reset_index()
            )

            # KPI CARDS
            render_html(
                f"""
                <div class="kpi-grid">

                    <div class="kpi-card">

                        <div class="kpi-label">
                            MANN-WHITNEY U
                        </div>

                        <div class="kpi-value">
                            {safe_float(u_stat):,.1f}
                        </div>

                        <div class="kpi-note">
                            Two-sided distributional comparison.
                        </div>

                    </div>


                    <div class="kpi-card">

                        <div class="kpi-label">
                            P-VALUE
                        </div>

                        <div class="kpi-value">
                            {format_p_value(mw_p)}
                        </div>

                        <div class="kpi-note">
                            Statistical evidence for a
                            weekday/weekend difference.
                        </div>

                    </div>


                    <div class="kpi-card">

                        <div class="kpi-label">
                            MEDIAN DIFFERENCE
                        </div>

                        <div class="kpi-value">
                            {median_difference:,.0f}
                        </div>

                        <div class="kpi-note">
                            Weekend median minus weekday median.
                        </div>

                    </div>


                    <div class="kpi-card">

                        <div class="kpi-label">
                            EFFECT MAGNITUDE
                        </div>

                        <div class="kpi-value">
                            {abs(rank_biserial):.3f}
                        </div>

                        <div class="kpi-note">
                            Absolute rank-biserial effect magnitude.
                        </div>

                    </div>

                </div>
                """
            )

            # INTERPRETATION
            render_html(
                f"""
                <div class="statistical-interpretation">

                    <div class="statistical-interpretation-title">
                        Weekday versus weekend interpretation
                    </div>

                    <div class="statistical-interpretation-text">

                        The observed weekday/weekend comparison is
                        <strong>
                            {significance_text(mw_p)}
                        </strong>.

                        The weekday median is
                        <strong>
                            {weekday_median:,.0f}
                        </strong>
                        steps, while the weekend median is
                        <strong>
                            {weekend_median:,.0f}
                        </strong>
                        steps.

                        This produces an observed weekend-minus-weekday
                        median difference of
                        <strong>
                            {median_difference:,.0f}
                        </strong>
                        steps.

                        The absolute rank-biserial effect magnitude is
                        <strong>
                            {abs(rank_biserial):.3f}
                        </strong>.

                        This describes observed behavioral differences
                        and does not establish why the difference exists
                        or imply causation.
                    </div>

                </div>
                """
            )

            # DAY TYPE TABLE
            st.dataframe(
                week_summary.style.format(
                    {
                        "count": "{:,.0f}",
                        "mean": "{:,.0f}",
                        "median": "{:,.0f}",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            # TOTAL STEPS CHART
            fig_week = px.box(
                week.dropna(
                    subset=[
                        "Day_Type",
                        "TotalSteps",
                    ]
                ),
                x="Day_Type",
                y="TotalSteps",
                points="outliers",
                category_orders={
                    "Day_Type": [
                        "Weekday",
                        "Weekend",
                    ]
                },
                title="Total Steps: Weekday vs Weekend",
            )

            fig_week.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(
                    l=20,
                    r=20,
                    t=55,
                    b=20,
                ),
                xaxis_title="Day Type",
                yaxis_title="Total Steps",
            )

            st.plotly_chart(
                fig_week,
                use_container_width=True,
            )

        else:

            render_html(
                """
                <div class="statistical-interpretation">

                    <div class="statistical-interpretation-title">
                        Insufficient observations
                    </div>

                    <div class="statistical-interpretation-text">
                        At least two valid weekday observations and
                        two valid weekend observations are required
                        for the Mann-Whitney comparison.
                    </div>

                </div>
                """
            )

    else:

        render_html(
            """
            <div class="statistical-interpretation">

                <div class="statistical-interpretation-title">
                    Required fields unavailable
                </div>

                <div class="statistical-interpretation-text">
                    Is_Weekend and TotalSteps are required for the
                    weekday-versus-weekend analysis.
                </div>

            </div>
            """
        )

# BUSINESS USE — OUTSIDE THE STATISTICAL TEST RECTANGLE
render_html(
    """
    <div class="business-use">

        <div class="business-use-label">
            BUSINESS USE
        </div>

        <div class="business-use-title">
            How to use this analysis in reporting
        </div>

        <div class="business-use-copy">

            Use the results to identify measurable patterns,
            prioritize questions for deeper investigation, and
            distinguish statistically detectable relationships
            from practically meaningful differences.

            A p-value alone should not be used as a business
            decision rule. Sample size, effect magnitude,
            uncertainty, data quality, operational context,
            and the cost or benefit of acting on the finding
            should also be considered.

        </div>

    </div>
    """
)

# FINAL STATISTICAL CAVEAT
render_html(
    """
    <div class="statistical-caveat">
        Statistical significance does not establish causation.
        These tests describe associations and distributional
        differences within the selected dataset and observation
        period. For business decisions, interpret the findings
        alongside effect size, sample size, uncertainty,
        data quality, operational context, and relevant
        domain evidence.
    </div>
    """
)