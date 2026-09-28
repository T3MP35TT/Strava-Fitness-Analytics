# pages/2_Activity_and_Calories.py
import base64
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.data import load_data, activity_groups

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Activity & Calories | Fitness Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# SAFE HTML RENDERER
def render_html(html: str):
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)

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

# GLOBAL DASHBOARD THEME
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
        --blue: #79bdf0;
        --green: #5fcf9a;
        --red: #f27d7d;
    }

    /* ========================================================
       APP BACKGROUND
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
       MATCHES REFERENCE
       ======================================================== */
    [data-testid="stSidebar"] {
        width: 320px !important;
        min-width: 320px !important;
        max-width: 320px !important;
        background:
            linear-gradient(
                180deg,
                #0d0f13 0%,
                #0b0d10 100%
            ) !important;
        border-right: 1px solid #292d34 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 320px !important;
        background:
            linear-gradient(
                180deg,
                #0d0f13 0%,
                #0b0d10 100%
            ) !important;

        padding: 0 !important;
    }
    [data-testid="stSidebarContent"] {
        padding: 0 16px 28px 16px !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
    }

    /* ========================================================
       SIDEBAR SCROLLBAR
       ======================================================== */
    [data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 7px;
    }
    [data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: transparent;
    }
    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: #30353e;
        border-radius: 10px;
    }

    /* DYNAMIC SIDEBAR CONTENT */
    .fitness-sidebar-divider { height: 1px; margin: 14px 0 17px 0; background: rgba(255,255,255,0.12); }
    .fitness-sidebar-label { color:#ff6b1a; font-size:.54rem; font-weight:850; letter-spacing:.14em; margin:15px 2px 7px 2px; text-transform:uppercase; }
    .fitness-sidebar-card { padding:10px 11px; border-radius:8px; background:rgba(14,16,22,.82); border:1px solid rgba(255,255,255,.10); margin-bottom:12px; }
    .fitness-sidebar-item-title { color:rgba(255,255,255,.90); font-size:.62rem; font-weight:750; margin-top:4px; margin-bottom:4px; }
    .fitness-sidebar-item-text { color:rgba(255,255,255,.45); font-size:.53rem; line-height:1.4; margin:2px 0 6px 0; }
    .fitness-sidebar-tech { color:rgba(255,255,255,.72); font-size:.61rem; line-height:1.7; }

    /* ========================================================
       SIDEBAR APP HEADER
       ======================================================== */
    .sidebar-app {
        height: 42px;

        display: flex;
        align-items: center;

        padding: 0 10px;

        margin: 18px 8px 12px 8px;

        border-radius: 7px;

        background:
            linear-gradient(
                135deg,
                rgba(252,82,0,0.13),
                rgba(252,82,0,0.045)
            );

        color: #f5f7fa;

        font-size: 12px;
        font-weight: 850;
        letter-spacing: -0.1px;
    }


    /* ========================================================
       SIDEBAR NAVIGATION
       ======================================================== */

    .sidebar-nav {
        display: flex;
        flex-direction: column;

        gap: 2px;

        margin: 0 8px;
    }

    .sidebar-nav-item {
        min-height: 38px;

        display: flex;
        align-items: center;

        padding: 0 9px;

        border: 1px solid transparent;
        border-radius: 7px;

        color: #d8dce3;

        font-size: 11px;
        font-weight: 800;

        text-decoration: none;

        transition:
            background 0.15s ease,
            border-color 0.15s ease;
    }
    .sidebar-nav-item:hover {
        background: rgba(255,255,255,0.035);
    }
    .sidebar-nav-item.active {
        border-color: var(--orange);
        background:
            linear-gradient(
                135deg,
                rgba(252,82,0,0.16),
                rgba(252,82,0,0.07)
            );
        color: #ffffff;
        box-shadow:
            inset 0 0 0 1px rgba(252,82,0,0.05);
    }
    /* ========================================================
       STREAMLIT SIDEBAR TABS / NAVIGATION
       ======================================================== */
    [data-testid="stSidebarNav"] {
        padding-top: 0.35rem !important;
    }
    [data-testid="stSidebarNav"] ul {
        padding-top: 0 !important;
    }
    [data-testid="stSidebarNav"] a {
        border-radius: 7px !important;
        margin: 2px 8px !important;
        padding: 0 10px !important;
        height: 40px !important;
        min-height: 40px !important;
        box-sizing: border-box !important;
        display: flex !important;
        align-items: center !important;
        color: rgba(255,255,255,0.70) !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        line-height: 1.15 !important;
        transition: background 0.15s ease, border 0.15s ease, color 0.15s ease !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        color: #ffffff !important;
        background: rgba(255,107,26,0.08) !important;
        border: 1px solid rgba(255,107,26,0.20) !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        color: #ffffff !important;
        background: linear-gradient(90deg, rgba(255,107,26,0.20), rgba(255,107,26,0.07)) !important;
        border: 1px solid rgba(255,107,26,0.42) !important;
        box-shadow: inset 3px 0 0 #ff6b1a, 0 4px 12px rgba(0,0,0,0.18) !important;
        padding: 0 10px !important;
        height: 40px !important;
        min-height: 40px !important;
        box-sizing: border-box !important;
        font-weight: 800 !important;
    }
    /* ========================================================
       SIDEBAR DIVIDER
       ======================================================== */
    .sidebar-divider {
        height: 1px;
        background: #292d34;
        margin: 20px 8px 0 8px;
    }
    /* ========================================================
       MAIN CONTENT ALIGNMENT
       ======================================================== */
    .block-container {
        max-width: none !important;
        width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-top: 92px !important;
        /*
         * Keep the content close to the sidebar and viewport edges so
         * wide dashboard sections actually use the available canvas.
         */
        padding-left: 22px !important;
        padding-right: 24px !important;
        padding-bottom: 4rem !important;
    }
    /* ========================================================
       KEEP MAIN CONTENT FROM BECOMING TOO WIDE
       ======================================================== */
    .block-container > div {
        max-width: none !important;
        width: 100% !important;
    }
    /* ========================================================
       HERO
       ======================================================== */
    .activity-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 28px 32px 26px 32px;
        margin: 0 0 18px 0;
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
    .activity-hero::before {
        content: "";
        position: absolute;
        z-index: 0;
        left: -8%;
        top: -90%;
        width: 116%;
        height: 280%;
        background:
            radial-gradient(ellipse at 12% 50%, rgba(38,58,83,0.95) 0%, rgba(38,58,83,0.68) 19%, rgba(38,58,83,0.22) 39%, transparent 62%),
            radial-gradient(ellipse at 83% 43%, rgba(255,72,8,0.92) 0%, rgba(255,72,8,0.66) 18%, rgba(255,72,8,0.25) 39%, transparent 63%),
            radial-gradient(ellipse at 52% 92%, rgba(17,28,43,0.92) 0%, rgba(17,28,43,0.48) 30%, transparent 65%);
        filter: blur(42px);
        transform: scale(1.05);
        opacity: 0.92;
        pointer-events: none;
    }
    .activity-hero::after {
        content: "";
        position: absolute;
        z-index: 1;
        width: 500px;
        height: 500px;
        right: -230px;
        top: -275px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,88,18,0.62) 0%, rgba(255,88,18,0.34) 25%, rgba(255,88,18,0.12) 46%, transparent 72%);
        filter: blur(34px);
        opacity: 0.92;
        pointer-events: none;
    }
    .activity-hero > * {
        position: relative;
        z-index: 3;
    }
    /* ========================================================
       HERO EYEBROW
       ======================================================== */
    .activity-eyebrow {
        color: var(--orange);
        font-size: 9px;
        font-weight: 900;
        letter-spacing: 1.55px;
        text-transform: uppercase;
        margin-bottom: 13px;
    }
    /* ========================================================
       HERO TITLE
       ======================================================== */
    .activity-title-row {
        display: flex;
        align-items: center;
        gap: 13px;
        margin: 0 0 12px 0;
    }
    .activity-logo {
        width: 43px;
        height: 43px;
        min-width: 43px;
        border-radius: 11px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #15191f;
        border: 1px solid #343943;
        box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.015),
            0 8px 20px rgba(0,0,0,0.25);
        overflow: hidden;
    }
    .activity-logo img {
        width: 43px;
        height: 43px;
        object-fit: contain;
        display: block;
    }
    .activity-title {
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
    .activity-description {
        max-width: 1080px;
        color: #aab2bd;
        font-size: 13px;
        line-height: 1.65;
        margin: 0;
    }
    /* ========================================================
       SECTION CONTAINERS
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
        margin: 13px 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0 !important;
    }
    /* Remove Streamlit's default vertical element gap inside the
       bordered dashboard sections. The previous implementation used
       standalone HTML open/close divs, which could not wrap Streamlit
       elements and left artificial blank bands above the controls/KPIs. */
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    /* ========================================================
       SECTION HEADER
       ======================================================== */
    .section-header {
        padding: 18px 20px 2px 20px;
        margin: 0;
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
    }
    .section-content {
        padding: 0 10px 10px 10px;
    }
    /* ========================================================
       FILTERS
       ======================================================== */
    .filter-header {
        padding: 18px 20px 0 20px;
    }
    .filter-label {
        color: var(--orange);
        font-size: 9px;
        font-weight: 900;
        letter-spacing: 1.55px;
        text-transform: uppercase;
        margin-bottom: 7px;
    }
    .filter-title {
        color: white;
        font-size: 21px;
        font-weight: 850;
        letter-spacing: -0.45px;
    }
    .filter-copy {
        color: #747d89;
        font-size: 11px;
        margin-top: 5px;
    }
    .filter-content {
        padding: 0;
    }
    .coverage-note {
        color: #737c88;
        font-size: 10px;
        margin: 2px 0 13px 0;
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
        padding: 0;
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
    .signal-card {
        border: 1px solid var(--border);
        border-left: 3px solid var(--orange);
        border-radius: 0 11px 11px 0;
        background: #11141a;
        padding: 13px 15px;
        color: #cbd1d9;
        font-size: 11px;
        line-height: 1.55;
        min-height: 48px;
        margin-bottom: 8px;
    }
    .signal-card strong {
        color: #ffffff;
    }
    .signal-accent {
        color: var(--orange);
        font-weight: 850;
    }
    /* ========================================================
       INTERPRETATION
       ======================================================== */
    .interpretation-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 28px;
        margin: 4px 20px 18px 20px;
    }
    .interpretation-block {
        color: #b1b8c2;
        font-size: 12px;
        line-height: 1.7;
    }
    .interpretation-heading {
        color: #dbe0e7;
        font-size: 12px;
        font-weight: 800;
        margin-bottom: 5px;
    }
    /* ========================================================
       DATAFRAME
       ======================================================== */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
        margin: 4px 10px 10px 10px;
    }
    /* ========================================================
       PLOTLY
       ======================================================== */
    .stPlotlyChart {
        border-radius: 12px;
    }
    div[data-testid="stPlotlyChart"] {
        padding: 0 !important;
    }
    /* ========================================================
       PAGE LOADING OVERLAY
       ======================================================== */
    .activity-loading-screen {
        position: fixed;
        inset: 0;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(11, 13, 16, 0.82);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        opacity: 1;
        visibility: visible;
        pointer-events: all;
        transition:
            opacity 0.45s ease,
            visibility 0s linear 0s;
    }
    /* The loader is dismissed by the ready marker at the very end of
       the Streamlit page. There is deliberately NO fixed timer. */
    .stApp:has(.activity-dashboard-ready) .activity-loading-screen {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transition:
            opacity 0.45s ease,
            visibility 0s linear 0.45s;
    }
    .activity-loading-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        transform: translateY(-8px);
    }
    .activity-loading-logo {
        width: 82px;
        height: 82px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: transparent;
        border: none;
        box-shadow: none;
        margin-bottom: 20px;
    }
    .activity-loading-logo img {
        width: 82px;
        height: 82px;
        display: block;
        object-fit: contain;
        background: transparent;
        border: none;
        box-shadow: none;
    }
    .activity-loading-ring {
        width: 38px;
        height: 38px;
        margin-bottom: 17px;
        border: 3px solid rgba(252, 82, 0, 0.20);
        border-top-color: #fc5200;
        border-right-color: #fc5200;
        border-radius: 50%;
        animation: activity-loader-spin 0.8s linear infinite;
    }
    @keyframes activity-loader-spin {
        to {
            transform: rotate(360deg);
        }
    }
    .activity-loading-text {
        color: #f5f7fa;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.1px;
        text-shadow: 0 2px 16px rgba(0,0,0,0.35);
    }
    .activity-title .activity-title-orange {
        color: var(--orange);
    }
    .activity-dashboard-ready {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
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
            padding-top: 70px !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .block-container > div {
            max-width: none;
        }
        .activity-hero {
            padding: 23px 22px;
        }
        .interpretation-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """
)

# FULL-SCREEN PAGE LOADER
if logo_data_uri:
    loading_logo_html = f"""
        <img src="{logo_data_uri}" alt="Strava" />
    """
else:
    loading_logo_html = """
        <div style="
            width:82px;
            height:82px;
            border-radius:50%;
            background:rgba(252,82,0,0.12);
            border:1px solid rgba(252,82,0,0.30);
        ""></div>
    """

render_html(
    f"""
    <div class="activity-loading-screen" aria-label="Loading Activity &amp; Calories">
        <div class="activity-loading-content">
            <div class="activity-loading-logo">
                {loading_logo_html}
            </div>
            <div class="activity-loading-ring"></div>
            <div class="activity-loading-text">
                Loading Activity &amp; Calories...
            </div>
        </div>
    </div>
    """
)

# DATA
@st.cache_data(show_spinner=False)
def get_activity_data():
    data = load_data()
    if data is None:
        return pd.DataFrame()
    data = data.copy()
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(
            data["Date"],
            errors="coerce",
        )
    numeric_columns = [
        "TotalSteps",
        "Calories",
        "VeryActiveMinutes",
        "FairlyActiveMinutes",
        "LightlyActiveMinutes",
        "SedentaryMinutes",
        "Total_Active_Minutes",
    ]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )
    if "Total_Active_Minutes" not in data.columns:
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
    return data

try:
    df = get_activity_data()

except Exception as exc:

    st.error(
        "The activity dataset could not be loaded."
    )

    st.caption(
        f"Technical detail: {exc}"
    )
    st.stop()

if df.empty:
    st.warning(
        "No activity records are available."
    )
    st.stop()

# RESPECT GLOBAL FILTERS
global_filtered = st.session_state.get(
    "global_filtered"
)

if (
    global_filtered is not None
    and not global_filtered.empty
):
    base_df = global_filtered.copy()

else:
    base_df = df.copy()

if base_df.empty:
    st.warning(
        "No records match the current application filters."
    )
    st.stop()

# VALIDATE DATA
required_columns = [
    "TotalSteps",
    "Calories",
    "VeryActiveMinutes",
    "FairlyActiveMinutes",
    "LightlyActiveMinutes",
    "SedentaryMinutes",
]
missing_columns = [
    column
    for column in required_columns
    if column not in base_df.columns
]
if missing_columns:
    st.error(
        "The Activity & Calories page is missing "
        "required dataset columns."
    )
    st.code(
        ", ".join(missing_columns),
        language="text",
    )
    st.stop()

# DATE RANGE
if (
    "Date" in base_df.columns
    and base_df["Date"].notna().any()
):
    min_date = (
        base_df["Date"]
        .min()
        .date()
    )
    max_date = (
        base_df["Date"]
        .max()
        .date()
    )
else:
    min_date = pd.Timestamp.today().date()
    max_date = min_date

# HERO
if logo_data_uri:
    logo_html = f"""
        <img
            src="{logo_data_uri}"
            alt="Strava"
        />
    """
else:
    logo_html = """
        <div
            style="
                width:29px;
                height:29px;
                border-radius:7px;
                background:#fc5200;
            "
        ></div>
    """

render_html(
    f"""
    <div class="activity-hero">
        <div class="activity-eyebrow">
            HOME &nbsp;•&nbsp; ACTIVITY PERFORMANCE
        </div>
        <div class="activity-title-row">
            <div class="activity-logo">
                {logo_html}
            </div>
            <h1 class="activity-title">
                <span class="activity-title-orange">Activity</span>
                <span> &amp; Calories</span>
            </h1>
        </div>
        <div class="activity-description">
            Executive view of movement engagement, activity intensity,
            energy expenditure, sedentary exposure, and 10K-step attainment
            across the selected participant-day population.
        </div>
    </div>
    """
)

# ANALYSIS CONTROLS
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
                Apply population, coverage, activity, and goal filters before
                interpreting performance.
            </div>
        </div>
        """
    )

    f1, f2, f3, f4 = st.columns(
        [1.15, 1.05, 1.05, 1.05],
        gap="medium",
    )

    with f1:
        selected_dates = st.date_input(
            "Analysis period",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="activity_analysis_dates",
        )

    with f2:
        coverage_options = [
            "All participants",
            "Complete observation",
            "At least 20 participant-days",
            "At least 25 participant-days",
        ]
        coverage_filter = st.selectbox(
            "Participant coverage",
            coverage_options,
            key="activity_coverage",
        )

    with f3:
        activity_filter = st.selectbox(
            "Activity level",
            [
                "All activity levels",
                "Low Activity",
                "Moderate Activity",
                "High Activity",
            ],
            key="activity_level_filter",
        )

    with f4:
        goal_filter = st.selectbox(
            "Goal attainment",
            [
                "All participant-days",
                "Reached 10K",
                "Below 10K",
            ],
            key="activity_goal_filter",
        )

# APPLY DATE FILTER
filtered = base_df.copy()

if "Date" in filtered.columns:

    if isinstance(selected_dates, tuple):

        if len(selected_dates) == 2:

            selected_start = pd.Timestamp(
                selected_dates[0]
            )

            selected_end = pd.Timestamp(
                selected_dates[1]
            )

            filtered = filtered[
                filtered["Date"].between(
                    selected_start,
                    selected_end,
                    inclusive="both",
                )
            ]

    elif selected_dates:

        selected_day = pd.Timestamp(
            selected_dates
        )

        filtered = filtered[
            filtered["Date"].dt.normalize()
            == selected_day.normalize()
        ]

# PARTICIPANT COVERAGE FILTER
if "Id" in filtered.columns:

    participant_day_counts = (
        filtered.groupby("Id")
        .size()
    )

    if coverage_filter == "Complete observation":

        target_days = (
            filtered["Date"].nunique()
            if "Date" in filtered.columns
            else participant_day_counts.max()
        )

        valid_ids = participant_day_counts[
            participant_day_counts >= target_days
        ].index

        filtered = filtered[
            filtered["Id"].isin(valid_ids)
        ]

    elif coverage_filter == "At least 20 participant-days":

        valid_ids = participant_day_counts[
            participant_day_counts >= 20
        ].index

        filtered = filtered[
            filtered["Id"].isin(valid_ids)
        ]

    elif coverage_filter == "At least 25 participant-days":

        valid_ids = participant_day_counts[
            participant_day_counts >= 25
        ].index

        filtered = filtered[
            filtered["Id"].isin(valid_ids)
        ]

# ACTIVITY LEVEL FILTER
try:

    activity_classified = activity_groups(
        filtered
    )

    if (
        activity_classified is not None
        and not activity_classified.empty
        and "Activity_Level"
        in activity_classified.columns
    ):

        activity_classified = (
            activity_classified.copy()
        )

        if (
            activity_filter
            != "All activity levels"
        ):

            filtered = activity_classified[
                activity_classified[
                    "Activity_Level"
                ].astype(str)
                == activity_filter
            ].copy()

        else:

            filtered = (
                activity_classified.copy()
            )

except Exception:
    pass

# GOAL FILTER
if goal_filter == "Reached 10K":

    filtered = filtered[
        filtered["TotalSteps"] >= 10000
    ]

elif goal_filter == "Below 10K":

    filtered = filtered[
        filtered["TotalSteps"] < 10000
    ]

# EMPTY FILTER STATE
if filtered.empty:

    st.warning(
        "No participant-days match the selected "
        "analysis controls."
    )

    st.stop()

# POPULATION COUNTS
record_count = len(filtered)

participant_count = (
    filtered["Id"].nunique()
    if "Id" in filtered.columns
    else record_count
)


period_start = (
    filtered["Date"].min()
    if (
        "Date" in filtered.columns
        and filtered["Date"].notna().any()
    )
    else None
)

period_end = (
    filtered["Date"].max()
    if (
        "Date" in filtered.columns
        and filtered["Date"].notna().any()
    )
    else None
)


period_text = (
    "All available activity records"
)

if (
    period_start is not None
    and period_end is not None
):

    period_text = (
        f"{period_start:%d %b %Y} — "
        f"{period_end:%d %b %Y}"
    )


render_html(
    f"""
    <div class="coverage-note">
        Showing <strong>{record_count:,}</strong>
        participant-days from
        <strong>{participant_count:,}</strong>
        participants.
        &nbsp; • &nbsp;
        {period_text}
    </div>
    """
)

# CORE METRICS
avg_steps = (
    filtered["TotalSteps"].mean()
)

median_steps = (
    filtered["TotalSteps"].median()
)

avg_active = (
    filtered["Total_Active_Minutes"].mean()
    if "Total_Active_Minutes"
    in filtered.columns
    else np.nan
)

avg_calories = (
    filtered["Calories"].mean()
)

avg_sedentary = (
    filtered["SedentaryMinutes"].mean()
)

goal_rate = (
    filtered["TotalSteps"]
    .ge(10000)
    .mean()
    * 100
)

high_sedentary_rate = (
    filtered["SedentaryMinutes"]
    .ge(900)
    .mean()
    * 100
)

active_share = (
    avg_active
    / (avg_active + avg_sedentary)
    * 100
    if (
        pd.notna(avg_active)
        and pd.notna(avg_sedentary)
        and avg_active + avg_sedentary > 0
    )
    else np.nan
)

# DYNAMIC SIDEBAR SUMMARY
with st.sidebar:
    st.html(
        f"""
        <div class="fitness-sidebar-divider"></div>

        <div class="fitness-sidebar-card">
            <div class="fitness-sidebar-label">ACTIVITY &amp; CALORIES</div>

            <div class="fitness-sidebar-item-title">
                Decision-focused summary
            </div>

            <div class="fitness-sidebar-item-text">
                High-level view of movement, energy expenditure,
                activity intensity, and 10K goal attainment.
            </div>

            <div class="fitness-sidebar-item-title">
                Current view
            </div>

            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">Analysis period:</strong><br>
                {period_text}
            </div>

            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">Participant-days:</strong>
                {record_count:,}
            </div>

            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">Participants:</strong>
                {participant_count:,}
            </div>

            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">Avg steps:</strong>
                {avg_steps:,.0f}
            </div>

            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">Avg calories:</strong>
                {avg_calories:,.0f}
            </div>

            <div class="fitness-sidebar-item-text">
                <strong style="color:#f5f7fa;">10K goal rate:</strong>
                {goal_rate:.1f}%
            </div>
        </div>

        <div class="fitness-sidebar-label">
            CURRENT ANALYTICS
        </div>

        <div class="fitness-sidebar-card fitness-sidebar-tech">
            <div>Active share: {active_share:.1f}%</div>
            <div>Avg active minutes: {avg_active:,.0f}</div>
            <div>Avg sedentary minutes: {avg_sedentary:,.0f}</div>
            <div>High sedentary rate: {high_sedentary_rate:.1f}%</div>
        </div>
        """
    )

# EXECUTIVE SNAPSHOT
with st.container(border=True):
    render_html(
        """
        <div class="section-header">
            <div class="section-label">
                EXECUTIVE READOUT
            </div>
            <div class="section-title">
                Movement performance at a glance
            </div>
            <div class="section-copy">
                The headline measures below describe the selected operating
                population and should be interpreted alongside coverage and trend.
            </div>
        </div>
        """
    )

    k1, k2, k3, k4, k5 = st.columns(
        5,
        gap="medium",
    )

    with k1:
        st.metric(
            "Avg Steps",
            f"{avg_steps:,.0f}",
        )

    with k2:
        st.metric(
            "Median Steps",
            f"{median_steps:,.0f}",
        )

    with k3:
        st.metric(
            "Avg Active Minutes",
            (
                f"{avg_active:,.0f}"
                if pd.notna(avg_active)
                else "—"
            ),
        )

    with k4:
        st.metric(
            "Avg Calories",
            f"{avg_calories:,.0f}",
        )

    with k5:
        st.metric(
            "10K Goal Rate",
            f"{goal_rate:.1f}%",
        )

# BUSINESS SIGNALS
s1, s2, s3 = st.columns(
    3,
    gap="medium",
)

with s1:
    render_html(
        f"""
        <div class="signal-card">
            <strong>Engagement</strong><br>
            <span class="signal-accent">
                {goal_rate:.1f}%
            </span>
            of participant-days reached the 10,000-step benchmark.
        </div>
        """
    )

with s2:
    render_html(
        f"""
        <div class="signal-card">
            <strong>Sedentary exposure</strong><br>
            <span class="signal-accent">
                {high_sedentary_rate:.1f}%
            </span>
            of participant-days recorded at least 900 sedentary minutes.
        </div>
        """
    )

with s3:
    render_html(
        f"""
        <div class="signal-card">
            <strong>Activity mix</strong><br>
            <span class="signal-accent">
                {active_share:.1f}%
            </span>
            of combined active and sedentary minutes were active.
        </div>
        """
    )

# WEEKLY PERFORMANCE TREND
if "Date" in filtered.columns:

    weekly = (
        filtered
        .dropna(subset=["Date"])
        .assign(
            Week=lambda x:
                x["Date"]
                .dt
                .to_period("W")
                .dt
                .start_time
        )
        .groupby(
            "Week",
            as_index=False,
        )
        .agg(
            Avg_Steps=(
                "TotalSteps",
                "mean",
            ),
            Goal_Rate=(
                "TotalSteps",
                lambda x:
                    (x >= 10000).mean()
                    * 100,
            ),
        )
        .sort_values("Week")
    )

else:

    weekly = pd.DataFrame()


with st.container(border=True):

    render_html(
        """
        <div class="section-header">

            <div class="section-label">
                PERFORMANCE TREND
            </div>

            <div class="section-title">
                Weekly movement and goal attainment
            </div>

            <div class="section-copy">
                Weekly aggregation makes changes in participant behavior easier
                to distinguish from day-to-day variation.
            </div>

        </div>
        """
    )

    if not weekly.empty:

        c1, c2 = st.columns(
            2,
            gap="large",
        )

        with c1:

            fig_steps = go.Figure()

            fig_steps.add_trace(
                go.Scatter(
                    x=weekly["Week"],
                    y=weekly["Avg_Steps"],
                    mode="lines+markers",
                    name="Average steps",
                    line=dict(
                        color="#FC5200",
                        width=3,
                    ),
                    marker=dict(
                        size=7,
                    ),
                )
            )

            fig_steps.add_hline(
                y=10000,
                line_dash="dash",
                line_color="#8e98a6",
                annotation_text="10K benchmark",
                annotation_position="top right",
            )

            fig_steps.update_layout(
                height=350,
                margin=dict(
                    l=10,
                    r=10,
                    t=20,
                    b=10,
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="#aeb5c0",
                    size=10,
                ),
                xaxis=dict(
                    title="Week",
                    gridcolor="#292d36",
                    zeroline=False,
                ),
                yaxis=dict(
                    title="Average Steps",
                    gridcolor="#292d36",
                    zeroline=False,
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig_steps,
                use_container_width=True,
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

        with c2:

            fig_goal = go.Figure()

            fig_goal.add_trace(
                go.Scatter(
                    x=weekly["Week"],
                    y=weekly["Goal_Rate"],
                    mode="lines+markers",
                    name="10K Goal Rate",
                    line=dict(
                        color="#79bdf0",
                        width=3,
                    ),
                    marker=dict(
                        size=7,
                    ),
                )
            )

            fig_goal.update_layout(
                height=350,
                margin=dict(
                    l=10,
                    r=10,
                    t=20,
                    b=10,
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="#aeb5c0",
                    size=10,
                ),
                xaxis=dict(
                    title="Week",
                    gridcolor="#292d36",
                    zeroline=False,
                ),
                yaxis=dict(
                    title="10K Goal Rate (%)",
                    gridcolor="#292d36",
                    zeroline=False,
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig_goal,
                use_container_width=True,
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

    else:

        st.info(
            "Weekly trend data is unavailable for the current selection."
        )

# DISTRIBUTION + ENERGY
left, right = st.columns(
    2,
    gap="large",
)

# MOVEMENT DISTRIBUTION
with left:

    with st.container(border=True):

        render_html(
            """
            <div class="section-header">

                <div class="section-label">
                    MOVEMENT DISTRIBUTION
                </div>

                <div class="section-title">
                    Daily steps distribution
                </div>

                <div class="section-copy">
                    Shows how consistently the selected population is performing
                    rather than relying only on the average.
                </div>

            </div>
            """
        )

        fig_hist = px.histogram(
            filtered,
            x="TotalSteps",
            nbins=30,
        )

        fig_hist.update_traces(
            marker_color="#79bdf0",
            marker_line_color="#79bdf0",
        )

        fig_hist.update_layout(
            height=380,
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#aeb5c0",
                size=10,
            ),
            xaxis=dict(
                title="Daily Steps",
                gridcolor="#292d36",
                zeroline=False,
            ),
            yaxis=dict(
                title="Participant-Days",
                gridcolor="#292d36",
                zeroline=False,
            ),
            bargap=0.03,
            showlegend=False,
        )

        st.plotly_chart(
            fig_hist,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

# ENERGY RELATIONSHIP
with right:

    with st.container(border=True):

        render_html(
            """
            <div class="section-header">

                <div class="section-label">
                    ENERGY RELATIONSHIP
                </div>

                <div class="section-title">
                    Steps vs calorie expenditure
                </div>

                <div class="section-copy">
                    Describes the observed relationship between movement volume
                    and recorded energy expenditure.
                </div>

            </div>
            """
        )

        scatter_source = (
            filtered[
                [
                    "TotalSteps",
                    "Calories",
                ]
                + [
                    c
                    for c in [
                        "Id",
                        "Date",
                    ]
                    if c in filtered.columns
                ]
            ]
            .dropna(
                subset=[
                    "TotalSteps",
                    "Calories",
                ]
            )
            .copy()
        )

        fig_scatter = px.scatter(
            scatter_source,
            x="TotalSteps",
            y="Calories",
            opacity=0.65,
            hover_data=[
                c
                for c in [
                    "Id",
                    "Date",
                ]
                if c in scatter_source.columns
            ],
        )

        fig_scatter.update_traces(
            marker=dict(
                color="#FC5200",
                size=7,
                line=dict(
                    width=0.4,
                    color="#ffb08c",
                ),
            )
        )

        if len(scatter_source) >= 2:

            x = scatter_source[
                "TotalSteps"
            ].to_numpy(
                dtype=float
            )

            y = scatter_source[
                "Calories"
            ].to_numpy(
                dtype=float
            )

            if np.ptp(x) > 0:

                slope, intercept = np.polyfit(
                    x,
                    y,
                    1,
                )

                x_line = np.linspace(
                    float(np.nanmin(x)),
                    float(np.nanmax(x)),
                    100,
                )

                y_line = (
                    slope * x_line
                    + intercept
                )

                fig_scatter.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode="lines",
                        name="Observed trend",
                        line=dict(
                            color="#ff9a62",
                            width=2,
                            dash="dash",
                        ),
                        hoverinfo="skip",
                    )
                )

        fig_scatter.update_layout(
            height=380,
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#aeb5c0",
                size=10,
            ),
            xaxis=dict(
                title="Daily Steps",
                gridcolor="#292d36",
                zeroline=False,
            ),
            yaxis=dict(
                title="Calories",
                gridcolor="#292d36",
                zeroline=False,
            ),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="#aeb5c0",
                    size=10,
                ),
            ),
        )

        st.plotly_chart(
            fig_scatter,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

# BEHAVIORAL MIX
with st.container(border=True):

    render_html(
        """
        <div class="section-header">

            <div class="section-label">
                BEHAVIORAL MIX
            </div>

            <div class="section-title">
                Average daily time by behavior
            </div>

            <div class="section-copy">
                Shows where the selected participant-day population is spending
                its recorded time.
            </div>

        </div>
        """
    )

    intensity = (
        filtered[
            [
                "VeryActiveMinutes",
                "FairlyActiveMinutes",
                "LightlyActiveMinutes",
                "SedentaryMinutes",
            ]
        ]
        .mean()
        .reset_index()
    )

    intensity.columns = [
        "Behavior",
        "Minutes",
    ]

    behavior_labels = {
        "VeryActiveMinutes": "Very Active",
        "FairlyActiveMinutes": "Fairly Active",
        "LightlyActiveMinutes": "Lightly Active",
        "SedentaryMinutes": "Sedentary",
    }

    intensity["Behavior"] = (
        intensity["Behavior"]
        .map(behavior_labels)
    )

    fig_intensity = px.bar(
        intensity,
        x="Behavior",
        y="Minutes",
        text_auto=".0f",
    )

    fig_intensity.update_traces(
        marker_color="#FC5200",
        textfont_color="#ffffff",
    )

    fig_intensity.update_layout(
        height=370,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#aeb5c0",
            size=10,
        ),
        xaxis=dict(
            title="",
            gridcolor="#292d36",
            zeroline=False,
        ),
        yaxis=dict(
            title="Average Minutes",
            gridcolor="#292d36",
            zeroline=False,
        ),
        showlegend=False,
    )

    st.plotly_chart(
        fig_intensity,
        use_container_width=True,
        config={
            "displaylogo": False,
            "responsive": True,
        },
    )

# ACTIVITY-LEVEL PERFORMANCE
with st.container(border=True):

    render_html(
        """
        <div class="section-header">

            <div class="section-label">
                BEHAVIORAL SEGMENTATION
            </div>

            <div class="section-title">
                Activity-level performance
            </div>

            <div class="section-copy">
                Compare movement volume, energy expenditure, active time,
                and goal attainment across activity segments.
            </div>

        </div>
        """
    )

    try:

        activity = activity_groups(
            filtered
        )

        if (
            activity is not None
            and not activity.empty
            and "Activity_Level"
            in activity.columns
        ):

            summary = (
                activity
                .groupby(
                    "Activity_Level",
                    observed=True,
                )
                .agg(
                    Participant_Days=(
                        "TotalSteps",
                        "size",
                    ),
                    Avg_Steps=(
                        "TotalSteps",
                        "mean",
                    ),
                    Avg_Calories=(
                        "Calories",
                        "mean",
                    ),
                    Avg_Active_Minutes=(
                        "Total_Active_Minutes",
                        "mean",
                    ),
                    Goal_Rate=(
                        "TotalSteps",
                        lambda x:
                            x.ge(10000)
                            .mean()
                            * 100,
                    ),
                )
                .reset_index()
            )

            summary = summary.rename(
                columns={
                    "Activity_Level":
                        "Activity Level",
                    "Participant_Days":
                        "Participant-Days",
                    "Avg_Steps":
                        "Avg Steps",
                    "Avg_Calories":
                        "Avg Calories",
                    "Avg_Active_Minutes":
                        "Avg Active Minutes",
                    "Goal_Rate":
                        "10K Goal Rate",
                }
            )

            st.dataframe(
                summary.style.format(
                    {
                        "Participant-Days":
                            "{:,.0f}",
                        "Avg Steps":
                            "{:,.0f}",
                        "Avg Calories":
                            "{:,.0f}",
                        "Avg Active Minutes":
                            "{:,.0f}",
                        "10K Goal Rate":
                            "{:.1f}%",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "Activity segmentation is unavailable "
                "for the current selection."
            )

    except Exception:

        st.info(
            "Activity segmentation is unavailable "
            "for the current selection."
        )

# PARTICIPANT-LEVEL CONSISTENCY
with st.container(border=True):

    render_html(
        """
        <div class="section-header">

            <div class="section-label">
                POPULATION CONCENTRATION
            </div>

            <div class="section-title">
                Participant-level consistency
            </div>

            <div class="section-copy">
                Separates population-level averages from participant-level
                behavior so unusually active or inactive participants do not
                dominate the interpretation.
            </div>

        </div>
        """
    )

    if "Id" in filtered.columns:

        participant_summary = (
            filtered
            .groupby("Id")
            .agg(
                Participant_Days=(
                    "TotalSteps",
                    "size",
                ),
                Avg_Steps=(
                    "TotalSteps",
                    "mean",
                ),
                Avg_Calories=(
                    "Calories",
                    "mean",
                ),
                Goal_Rate=(
                    "TotalSteps",
                    lambda x:
                        x.ge(10000)
                        .mean()
                        * 100,
                ),
            )
            .reset_index()
        )

        participant_summary = (
            participant_summary
            .sort_values(
                "Avg_Steps",
                ascending=False,
            )
            .head(10)
        )

        participant_summary = (
            participant_summary.rename(
                columns={
                    "Id":
                        "Participant",
                    "Participant_Days":
                        "Participant-Days",
                    "Avg_Steps":
                        "Avg Steps",
                    "Avg_Calories":
                        "Avg Calories",
                    "Goal_Rate":
                        "10K Goal Rate",
                }
            )
        )

        st.dataframe(
            participant_summary.style.format(
                {
                    "Participant-Days":
                        "{:,.0f}",
                    "Avg Steps":
                        "{:,.0f}",
                    "Avg Calories":
                        "{:,.0f}",
                    "10K Goal Rate":
                        "{:.1f}%",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# EXECUTIVE INTERPRETATION
with st.container(border=True):

    render_html(
        f"""
        <div class="section-header">

            <div class="section-label">
                EXECUTIVE INTERPRETATION
            </div>

            <div class="section-title">
                What leadership should take from this page
            </div>

        </div>

        <div class="interpretation-grid">

            <div class="interpretation-block">

                <div class="interpretation-heading">
                    Engagement
                </div>

                The selected population averages
                <strong>{avg_steps:,.0f}</strong>
                steps per participant-day, with
                <strong>{goal_rate:.1f}%</strong>
                of participant-days reaching the
                10,000-step benchmark.

                <br><br>
                <div class="interpretation-heading">
                    Energy
                </div>
                Recorded calorie expenditure averages
                <strong>{avg_calories:,.0f}</strong>
                calories per participant-day.
            </div>
            <div class="interpretation-block">
                <div class="interpretation-heading">
                    Population
                </div>
                The analysis currently represents
                <strong>{participant_count:,}</strong>
                participants across
                <strong>{record_count:,}</strong>
                participant-days.
                <br><br>
                <div class="interpretation-heading">
                    Behavioral exposure
                </div>
                <strong>{high_sedentary_rate:.1f}%</strong>
                of participant-days recorded at least
                900 sedentary minutes.
            </div>
        </div>
        """
    )

# DATA CONTEXT
with st.container(border=True):
    render_html(
        """
        <div class="section-header">
            <div class="section-label">
                DATA CONTEXT
            </div>
            <div class="section-title">
                Interpretation and coverage
            </div>
            <div class="section-copy">
                These measures describe recorded participant-day activity.
                Coverage, missing observations, device behavior, and the selected
                analysis period can materially affect population-level comparisons.
                Use participant coverage controls when comparing populations with
                different observation completeness.
            </div>
        </div>
        """
    )

# DASHBOARD READY
render_html(
    "<div class=\"activity-dashboard-ready\"></div>"
)
