
# pages/4_Participant_Analysis.py
import base64
import textwrap
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data import load_data

# PAGE CONFIG
st.set_page_config(
    page_title="Participant Analysis | Fitness Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# HELPERS
def find_strava_logo():
    candidates = [
        Path("images/strava_logo.png"),
        Path(__file__).resolve().parent / "images" / "strava_logo.png",
        Path(__file__).resolve().parent.parent / "images" / "strava_logo.png",
        Path(__file__).resolve().parent.parent.parent / "images" / "strava_logo.png",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def render_html(markup):
    """Render HTML directly. Never use markdown for these UI cards."""
    st.html(textwrap.dedent(markup).strip())


def render_sidebar_html(markup):
    """Render sidebar HTML directly so markup cannot appear as text."""
    st.sidebar.html(textwrap.dedent(markup).strip())


def fmt_number(value, decimals=0):
    if pd.isna(value):
        return "—"
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def fmt_pct(value, decimals=0):
    if pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}%"

# STRAVA LOGO
STRAVA_LOGO_PATH = find_strava_logo()

if STRAVA_LOGO_PATH:
    STRAVA_LOGO_B64 = base64.b64encode(
        STRAVA_LOGO_PATH.read_bytes()
    ).decode("utf-8")

    STRAVA_LOGO_HTML = (
        f'<img class="hero-logo" '
        f'src="data:image/png;base64,{STRAVA_LOGO_B64}" '
        f'alt="Strava logo">'
    )
else:
    STRAVA_LOGO_HTML = (
        '<div class="hero-logo-fallback">A</div>'
    )

# THEME / CSS
st.markdown(
    """
<style>
:root {
    --bg: #090b0e;
    --surface: #101318;
    --surface-2: #14181e;
    --surface-3: #1a1f27;
    --border: #292f38;
    --text: #f5f7fa;
    --muted: #9ba4b0;
    --muted-2: #6f7885;
    --orange: #fc5200;
    --orange-soft: rgba(252,82,0,.12);
    --blue: #65a9d8;
    --green: #62c596;
    --yellow: #d6ad62;
    --red: #d87878;
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 88% 0%,
            rgba(252,82,0,.055),
            transparent 25%
        ),
        #090b0e;
    color: var(--text);
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: #0b0d10 !important;
    border-right: 1px solid #252a31 !important;
}

[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    background: #0b0d10 !important;
}

[data-testid="stSidebarNav"] {
    padding-top: .35rem !important;
}

[data-testid="stSidebarNav"] ul {
    padding-top: 0 !important;
}

[data-testid="stSidebarNav"] li {
    margin: 0 !important;
}

[data-testid="stSidebarNav"] a {
    color: #eef1f5 !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    border-radius: 7px !important;
    margin: 2px 8px !important;
    padding: 6px 10px !important;
    min-height: 28px !important;
}

[data-testid="stSidebarNav"] a:hover {
    color: #ffffff !important;
    background: rgba(252,82,0,.08) !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    color: #ffffff !important;
    background: rgba(252,82,0,.16) !important;
    border: 1px solid rgba(252,82,0,.80) !important;
    box-shadow: inset 3px 0 0 #fc5200 !important;
    padding: 5px 9px !important;
    min-height: 28px !important;
    margin: 2px 22px 2px 8px !important;
    font-size: 11.5px !important;
}

.block-container {
    max-width: none !important;
    width: 100% !important;
    margin: 0 !important;
    padding-top: 68px !important;
    padding-left: 28px !important;
    padding-right: 28px !important;
    padding-bottom: 4rem !important;
}

/* =========================================================
   SECTION TILES
   ========================================================= */

[data-testid="stVerticalBlockBorderWrapper"] {
    background:
        linear-gradient(
            145deg,
            rgba(20,24,30,.96),
            rgba(12,15,19,.96)
        ) !important;
    border: 1px solid #292f38 !important;
    border-radius: 11px !important;
    box-shadow: 0 8px 24px rgba(0,0,0,.12) !important;
    overflow: hidden !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 11px !important;
}

/* =========================================================
   HERO / TITLE TILE — SELF-CONTAINED FROSTED GLASS
   ========================================================= */

/*
   Do not rely on Streamlit's border-wrapper for the hero visual.
   The hero is a real HTML tile with its own blurred atmospheric
   layers, so the effect remains visible regardless of Streamlit
   DOM changes.
*/
.participant-hero-tile {
    position: relative !important;
    isolation: isolate !important;
    width: 100% !important;
    min-height: 164px !important;
    margin: 0 0 10px 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    border: 1px solid rgba(76, 84, 96, 0.72) !important;
    border-radius: 15px !important;
    background: #101318 !important;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.055),
        inset 0 -1px 0 rgba(0,0,0,.28),
        0 16px 42px rgba(0,0,0,.22) !important;
}

/* The actual blurred color field. */
.participant-hero-blur {
    position: absolute !important;
    z-index: 0 !important;
    inset: -70px !important;
    pointer-events: none !important;
    background:
        radial-gradient(ellipse 44% 115% at 96% 8%,
            rgba(252,82,0,.42) 0%,
            rgba(252,82,0,.20) 30%,
            transparent 68%),
        radial-gradient(ellipse 42% 95% at 70% 115%,
            rgba(120,48,22,.28) 0%,
            transparent 70%),
        radial-gradient(ellipse 58% 80% at 10% 12%,
            rgba(72,86,104,.24) 0%,
            transparent 72%),
        linear-gradient(110deg,
            rgba(22,27,34,.98) 0%,
            rgba(15,19,25,.86) 48%,
            rgba(53,27,17,.82) 100%);
    filter: blur(34px) saturate(135%) !important;
    -webkit-filter: blur(34px) saturate(135%) !important;
    transform: scale(1.10) !important;
    opacity: 1 !important;
}

/* Frosted glass veil over the blurred field. */
.participant-hero-glass {
    position: absolute !important;
    z-index: 1 !important;
    inset: 0 !important;
    pointer-events: none !important;
    background:
        linear-gradient(135deg,
            rgba(255,255,255,.055) 0%,
            rgba(255,255,255,.018) 36%,
            rgba(0,0,0,.055) 72%,
            rgba(252,82,0,.045) 100%);
    backdrop-filter: blur(15px) saturate(125%) !important;
    -webkit-backdrop-filter: blur(15px) saturate(125%) !important;
    border-radius: inherit !important;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,.018) !important;
}

/* Hero content always stays crisp above the glass. */
.participant-hero-content {
    position: relative !important;
    z-index: 2 !important;
    box-sizing: border-box !important;
    padding: 27px 18px 27px 18px !important;
}

@media (max-width: 900px) {
    .participant-hero-tile {
        min-height: 150px !important;
    }

    .participant-hero-blur {
        filter: blur(28px) saturate(125%) !important;
        -webkit-filter: blur(28px) saturate(125%) !important;
    }
}

/* =========================================================
   TYPOGRAPHY
   ========================================================= */

h1 {
    color: #ffffff !important;
    font-size: clamp(2.2rem, 3.2vw, 3.15rem) !important;
    font-weight: 900 !important;
    letter-spacing: -2px !important;
    line-height: 1 !important;
    margin: 0 !important;
}

h2 {
    color: #ffffff !important;
    font-size: 22px !important;
    font-weight: 850 !important;
    letter-spacing: -.65px !important;
    margin: 0 !important;
}

h3 {
    color: #ffffff !important;
    font-weight: 800 !important;
}

.hero-eyebrow,
.section-label {
    color: var(--orange);
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1.65px;
    text-transform: uppercase;
}

.hero-eyebrow {
    margin-bottom: 14px;
}

.section-label {
    margin-bottom: 7px;
}

.hero-description {
    color: #aab2bd;
    font-size: 12px;
    line-height: 1.6;
    max-width: 1120px;
    margin-top: 14px;
}

.section-copy {
    color: #747d89;
    font-size: 10.5px;
    line-height: 1.55;
    max-width: 1100px;
    margin-top: 6px;
    margin-bottom: 13px;
}

.report-meta {
    color: #68717d;
    font-size: 9.5px;
    line-height: 1.5;
    margin-top: 11px;
}

/* =========================================================
   HERO CONTENT
   ========================================================= */

.hero-panel {
    position: relative;
    z-index: 3;
    padding: 27px 14px 27px 14px;
}

.hero-eyebrow {
    color: #fc5200 !important;
    font-size: 9px !important;
    font-weight: 900 !important;
    letter-spacing: 1.65px !important;
    line-height: 1.2 !important;
    text-transform: uppercase !important;
    margin: 0 0 14px 0 !important;
}

.hero-title-row {
    display: flex;
    align-items: center;
    min-height: 47px;
    white-space: nowrap;
}

.hero-logo {
    display: block;
    width: 42px;
    height: 42px;
    min-width: 42px;
    max-width: 42px;
    object-fit: contain;
    margin-right: 13px;
    border-radius: 50%;
}

.hero-logo-fallback {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    min-width: 42px;
    margin-right: 13px;
    border-radius: 50%;
    background: #fc5200;
    color: #ffffff;
    font-size: 22px;
    font-weight: 900;
    line-height: 1;
}

.hero-title {
    display: inline-block;
    color: #ffffff;
    font-size: clamp(2.25rem, 3.3vw, 3.3rem);
    font-weight: 900;
    letter-spacing: -2.35px;
    line-height: .98;
    white-space: nowrap;
}

.hero-title-accent {
    color: #fc5200;
}

.hero-title-rest {
    color: #ffffff;
}

.hero-description {
    color: #aab2bd !important;
    font-size: 12px !important;
    line-height: 1.6 !important;
    max-width: 1120px !important;
    margin: 15px 0 0 0 !important;
}

/* =========================================================
   CONTROL TYPOGRAPHY
   ========================================================= */

.control-heading {
    color: #ffffff;
    font-size: 19px;
    font-weight: 850;
    letter-spacing: -.45px;
}

.control-copy {
    color: #747d89;
    font-size: 10px;
    line-height: 1.5;
    margin-top: 4px;
    margin-bottom: 13px;
}

/* =========================================================
   METRICS
   ========================================================= */

div[data-testid="stMetric"] {
    border: 1px solid #292f38 !important;
    border-radius: 11px !important;
    background:
        linear-gradient(
            145deg,
            #14181e,
            #101318
        ) !important;
    padding: 15px 16px !important;
    min-height: 96px !important;
    box-shadow: none !important;
}

div[data-testid="stMetricLabel"] {
    color: #858e9b !important;
    font-size: 9px !important;
    font-weight: 800 !important;
    letter-spacing: .7px !important;
    text-transform: uppercase !important;
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 25px !important;
    font-weight: 900 !important;
    letter-spacing: -.7px !important;
}

div[data-testid="stMetricDelta"] {
    font-size: 9px !important;
}

/* =========================================================
   SIGNAL CARDS
   ========================================================= */

.signal-card {
    min-height: 125px;
    padding: 15px 16px;
    border: 1px solid #292f38;
    border-radius: 10px;
    background: linear-gradient(145deg,#15191f,#101318);
    box-sizing: border-box;
}

.signal-card.accent {
    border-top: 2px solid #fc5200;
}

.signal-card.blue {
    border-top: 2px solid #65a9d8;
}

.signal-card.green {
    border-top: 2px solid #62c596;
}

.signal-card.yellow {
    border-top: 2px solid #d6ad62;
}

.signal-label {
    color: #7d8793;
    font-size: 8px;
    font-weight: 850;
    letter-spacing: 1.05px;
    text-transform: uppercase;
    margin-bottom: 7px;
}

.signal-value {
    color: #ffffff;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: -.7px;
    margin-bottom: 6px;
}

.signal-copy {
    color: #9ba4b0;
    font-size: 9.5px;
    line-height: 1.48;
}

/* =========================================================
   COVERAGE
   ========================================================= */

.coverage-strip {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    padding: 9px 11px;
    border: 1px solid #242a32;
    border-radius: 8px;
    background: rgba(255,255,255,.018);
    color: #89929e;
    font-size: 9.5px;
    line-height: 1.45;
}

.coverage-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #62c596;
    flex: 0 0 auto;
}

/* =========================================================
   SUBHEADS
   ========================================================= */

.mini-heading {
    color: #ffffff;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 7px;
}

.mini-label {
    color: #89929e;
    font-size: 8px;
    font-weight: 850;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

/* =========================================================
   FORM CONTROLS
   ========================================================= */

label {
    color: #9ca5b1 !important;
    font-size: 10px !important;
    font-weight: 750 !important;
}

div[data-baseweb="select"] > div {
    background: #1b1f26 !important;
    border-color: #303640 !important;
}

div[data-baseweb="select"] * {
    color: #f3f5f8 !important;
}

[data-testid="stDateInput"] input {
    background: #1b1f26 !important;
    color: #f3f5f8 !important;
    border-color: #303640 !important;
}

/* =========================================================
   CHARTS / TABLES
   ========================================================= */

div[data-testid="stPlotlyChart"] {
    padding: 0 !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #292f38 !important;
    border-radius: 9px !important;
    overflow: hidden !important;
}

.stDownloadButton button {
    background: #171b21 !important;
    color: #f5f7fa !important;
    border: 1px solid #303640 !important;
    border-radius: 8px !important;
    font-size: 10px !important;
    font-weight: 750 !important;
}

.stDownloadButton button:hover {
    border-color: #fc5200 !important;
    color: #ffffff !important;
}

.report-footnote {
    color: #626b77;
    font-size: 9px;
    line-height: 1.55;
    padding-top: 12px;
    border-top: 1px solid #20252c;
}

/* =========================================================
   STREAMLIT HTML RESET
   ========================================================= */

[data-testid="stHtml"] {
    width: 100% !important;
}

[data-testid="stHtml"] > div {
    width: 100% !important;
}

[data-testid="stHtml"] p,
[data-testid="stHtml"] div {
    box-sizing: border-box;
}

/* =========================================================
   SPACING
   ========================================================= */

div[data-testid="stVerticalBlock"] > div {
    gap: .5rem;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    margin-bottom: 10px !important;
}

/* =========================================================
   DYNAMIC SIDEBAR
   ========================================================= */

/*
   The sidebar card is deliberately rendered with st.sidebar.html().
   Do not replace it with st.sidebar.markdown(), otherwise a markdown
   code fence or escaped markup can make the HTML appear as text.
*/

.context-sidebar {
    margin: 18px 8px 0 8px;
    padding: 14px;
    border: 1px solid #2b313a;
    border-radius: 11px;
    background:
        linear-gradient(
            145deg,
            rgba(23,27,34,.96),
            rgba(14,17,21,.96)
        );
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.025),
        0 10px 25px rgba(0,0,0,.16);
}

.context-sidebar-kicker {
    color: #fc5200;
    font-size: 8px;
    font-weight: 900;
    letter-spacing: 1.45px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.context-sidebar-title {
    color: #ffffff;
    font-size: 16px;
    line-height: 1.15;
    font-weight: 900;
    letter-spacing: -.35px;
    margin-bottom: 13px;
}

.context-sidebar-rule {
    height: 1px;
    background: #272d35;
    margin: 10px 0 12px 0;
}

.context-sidebar-label {
    color: #737d89;
    font-size: 7.5px;
    font-weight: 850;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 3px;
}

.context-sidebar-value {
    color: #e9edf2;
    font-size: 9.5px;
    line-height: 1.35;
    font-weight: 700;
    word-break: break-word;
}

.context-sidebar-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 10px;
}

.context-sidebar-stat {
    padding: 8px 8px 9px 8px;
    border: 1px solid #272d35;
    border-radius: 8px;
    background: rgba(255,255,255,.018);
}

.context-sidebar-stat-label {
    color: #737d89;
    font-size: 7px;
    font-weight: 850;
    letter-spacing: .7px;
    text-transform: uppercase;
    margin-bottom: 3px;
}

.context-sidebar-stat-value {
    color: #ffffff;
    font-size: 13px;
    line-height: 1.1;
    font-weight: 900;
}

.context-sidebar-status {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #7f8995;
    font-size: 7.5px;
    line-height: 1.4;
    margin-top: 11px;
}

.context-sidebar-dot {
    width: 5px;
    height: 5px;
    min-width: 5px;
    border-radius: 50%;
    background: #62c596;
}

/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 900px) {

    .block-container {
        padding-top: 48px !important;
        padding-left: 14px !important;
        padding-right: 14px !important;
    }

    .hero-panel {
        padding: 24px 10px 25px 10px;
    }

    .hero-title {
        font-size: clamp(2rem, 7vw, 2.75rem);
        letter-spacing: -1.8px;
    }

    .hero-logo,
    .hero-logo-fallback {
        width: 38px;
        height: 38px;
        min-width: 38px;
        max-width: 38px;
        margin-right: 11px;
    }

    .hero-title-row {
        min-height: 42px;
    }
}

@media (max-width: 600px) {

    .block-container {
        padding-top: 36px !important;
    }

    .hero-title {
        font-size: 2rem;
    }

    .hero-title-row {
        white-space: normal;
    }

    .hero-description {
        font-size: 11px !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# LOAD DATA
df = load_data()

df = st.session_state.get(
    "global_filtered",
    df,
).copy()

# REQUIRED COLUMNS
required_columns = [
    "Id",
    "TotalSteps",
    "Calories",
    "Total_Active_Minutes",
    "SedentaryMinutes",
    "Sleep_Minutes",
    "HeartRate_Avg",
    "Date",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        "Participant Analysis cannot be rendered because "
        "the dataset is missing: "
        + ", ".join(missing_columns)
    )
    st.stop()

# CLEAN DATA
numeric_columns = [
    "TotalSteps",
    "Calories",
    "Total_Active_Minutes",
    "SedentaryMinutes",
    "Sleep_Minutes",
    "HeartRate_Avg",
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce",
    )

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce",
)

df = df[df["Id"].notna()].copy()

if df.empty:
    st.warning(
        "No participant records are available for the current filters."
    )
    st.stop()

# SUMMARY FUNCTIONS
def build_summary(source_df):

    result = (
        source_df
        .groupby("Id", as_index=False)
        .agg(
            Avg_Steps=("TotalSteps", "mean"),
            Avg_Calories=("Calories", "mean"),
            Avg_Active_Minutes=(
                "Total_Active_Minutes",
                "mean",
            ),
            Avg_Sedentary_Minutes=(
                "SedentaryMinutes",
                "mean",
            ),
            Avg_Sleep_Minutes=(
                "Sleep_Minutes",
                "mean",
            ),
            Avg_Heart_Rate=(
                "HeartRate_Avg",
                "mean",
            ),
            Observation_Days=(
                "Date",
                "nunique",
            ),
        )
    )

    result["Avg_Sleep_Hours"] = (
        result["Avg_Sleep_Minutes"] / 60
    )

    return result


def engagement_segment(steps):

    if pd.isna(steps):
        return "Insufficient Data"

    if steps < 5000:
        return "Lower Activity"

    if steps < 7500:
        return "Moderate Activity"

    if steps < 10000:
        return "Active"

    return "Highly Active"

# DATA RANGE
date_series = df["Date"].dropna()

if not date_series.empty:
    data_min_date = date_series.min().date()
    data_max_date = date_series.max().date()
else:
    data_min_date = None
    data_max_date = None

# HERO
render_html(
    f"""
    <div class="participant-hero-tile">

        <div class="participant-hero-blur"></div>
        <div class="participant-hero-glass"></div>

        <div class="participant-hero-content">

            <div class="hero-eyebrow">
                HOME&nbsp;&nbsp;•&nbsp;&nbsp;PARTICIPANT ANALYSIS
            </div>

            <div class="hero-title-row">
                {STRAVA_LOGO_HTML}

                <span class="hero-title">
                    <span class="hero-title-accent">
                        Participant
                    </span>
                    <span class="hero-title-rest">
                        &nbsp;Analysis
                    </span>
                </span>
            </div>

            <div class="hero-description">
                Executive view of participant activity, energy
                expenditure, sedentary behavior, sleep, engagement,
                and population-level operating patterns across the
                selected reporting population.
            </div>

        </div>
    </div>
    """
)

# ANALYSIS CONTROLS
with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            ANALYSIS CONTROLS
        </div>

        <div class="control-heading">
            Define the operating population
        </div>

        <div class="control-copy">
            Narrow the reporting population by observation period,
            participant, activity level, and the 10K step threshold.
        </div>
        """
    )

    control_cols = st.columns(
        [1.35, 1.0, 1.0, 1.0],
        gap="small",
    )

    with control_cols[0]:

        if data_min_date and data_max_date:

            selected_dates = st.date_input(
                "Analysis period",
                value=(
                    data_min_date,
                    data_max_date,
                ),
                min_value=data_min_date,
                max_value=data_max_date,
                key="participant_analysis_dates_v130",
            )

            if isinstance(selected_dates, (tuple, list)):

                if len(selected_dates) == 2:
                    start_date, end_date = selected_dates

                elif len(selected_dates) == 1:
                    start_date = selected_dates[0]
                    end_date = selected_dates[0]

                else:
                    start_date = data_min_date
                    end_date = data_max_date

            else:
                start_date = selected_dates
                end_date = selected_dates

            filtered_df = df[
                df["Date"].between(
                    pd.Timestamp(start_date),
                    pd.Timestamp(end_date),
                )
            ].copy()

        else:

            st.info("Date information is unavailable.")

            filtered_df = df.copy()
            start_date = data_min_date
            end_date = data_max_date

    with control_cols[1]:

        participant_options = (
            ["All participants"]
            + sorted(
                filtered_df["Id"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

        selected_participant = st.selectbox(
            "Participant",
            participant_options,
            key="participant_analysis_participant_v130",
        )

        if selected_participant != "All participants":
            filtered_df = filtered_df[
                filtered_df["Id"].astype(str)
                == selected_participant
            ].copy()

    with control_cols[2]:

        selected_activity = st.selectbox(
            "Activity level",
            [
                "All activity levels",
                "Lower Activity",
                "Moderate Activity",
                "Active",
                "Highly Active",
            ],
            key="participant_analysis_activity_v130",
        )

    with control_cols[3]:

        selected_goal = st.selectbox(
            "10K step goal",
            [
                "All participants",
                "Participants averaging ≥10K",
                "Participants averaging <10K",
            ],
            key="participant_analysis_goal_v130",
        )

# SUMMARY + FILTERS
summary = build_summary(filtered_df)

if summary.empty:
    st.warning(
        "No participant records match the selected analysis controls."
    )
    st.stop()

summary["Engagement Segment"] = (
    summary["Avg_Steps"].apply(engagement_segment)
)

if selected_activity != "All activity levels":
    summary = summary[
        summary["Engagement Segment"] == selected_activity
    ].copy()

if selected_goal == "Participants averaging ≥10K":

    summary = summary[
        summary["Avg_Steps"] >= 10000
    ].copy()

elif selected_goal == "Participants averaging <10K":

    summary = summary[
        summary["Avg_Steps"] < 10000
    ].copy()

if summary.empty:
    st.warning(
        "No participants match the selected activity and 10K goal filters."
    )
    st.stop()

# POPULATION METRICS
participant_count = int(summary["Id"].nunique())

avg_steps = summary["Avg_Steps"].mean()
avg_calories = summary["Avg_Calories"].mean()
avg_active = summary["Avg_Active_Minutes"].mean()
avg_sedentary = summary["Avg_Sedentary_Minutes"].mean()
avg_sleep = summary["Avg_Sleep_Hours"].mean()

median_observation_days = summary["Observation_Days"].median()
max_observation_days = summary["Observation_Days"].max()

sleep_coverage_pct = (
    summary["Avg_Sleep_Hours"].notna().mean() * 100
)

heart_rate_coverage_pct = (
    summary["Avg_Heart_Rate"].notna().mean() * 100
)

# SEGMENTATION
segment_order = [
    "Lower Activity",
    "Moderate Activity",
    "Active",
    "Highly Active",
    "Insufficient Data",
]

segment_counts = (
    summary["Engagement Segment"]
    .value_counts()
    .reindex(segment_order, fill_value=0)
)

lower_activity_pct = (
    summary["Engagement Segment"]
    .eq("Lower Activity")
    .mean()
    * 100
)

moderate_activity_pct = (
    summary["Engagement Segment"]
    .eq("Moderate Activity")
    .mean()
    * 100
)

active_pct = (
    summary["Engagement Segment"]
    .eq("Active")
    .mean()
    * 100
)

high_activity_pct = (
    summary["Engagement Segment"]
    .eq("Highly Active")
    .mean()
    * 100
)

# SEDENTARY DISTRIBUTION
sedentary_valid = (
    summary["Avg_Sedentary_Minutes"].dropna()
)

if sedentary_valid.empty:

    sedentary_q75 = float("nan")
    high_sedentary_pct = 0.0

else:

    sedentary_q75 = sedentary_valid.quantile(.75)

    high_sedentary_pct = (
        summary["Avg_Sedentary_Minutes"]
        .ge(sedentary_q75)
        .mean()
        * 100
    )

# DATE META
if (
    data_min_date
    and data_max_date
    and start_date is not None
    and end_date is not None
):

    date_meta = (
        f"{start_date.strftime('%d %b %Y')} – "
        f"{end_date.strftime('%d %b %Y')}"
    )

else:

    date_meta = "Available observation period"

# DYNAMIC CONTEXT SIDEBAR
sidebar_participant = (
    "All participants"
    if selected_participant == "All participants"
    else f"Participant {selected_participant}"
)

sidebar_activity = (
    "All activity levels"
    if selected_activity == "All activity levels"
    else selected_activity
)

sidebar_goal = (
    "All participant-days"
    if selected_goal == "All participants"
    else selected_goal.replace("Participants averaging ", "")
)

render_sidebar_html(
    f"""
    <div class="context-sidebar">

        <div class="context-sidebar-kicker">
            CURRENT VIEW
        </div>

        <div class="context-sidebar-title">
            Participant Analysis
        </div>

        <div class="context-sidebar-label">
            Reporting population
        </div>

        <div class="context-sidebar-value">
            {sidebar_participant}
        </div>

        <div class="context-sidebar-rule"></div>

        <div class="context-sidebar-label">
            Analysis period
        </div>

        <div class="context-sidebar-value">
            {date_meta}
        </div>

        <div style="height:8px;"></div>

        <div class="context-sidebar-label">
            Activity filter
        </div>

        <div class="context-sidebar-value">
            {sidebar_activity}
        </div>

        <div style="height:8px;"></div>

        <div class="context-sidebar-label">
            10K step filter
        </div>

        <div class="context-sidebar-value">
            {sidebar_goal}
        </div>

        <div class="context-sidebar-grid">

            <div class="context-sidebar-stat">
                <div class="context-sidebar-stat-label">
                    Participants
                </div>
                <div class="context-sidebar-stat-value">
                    {participant_count:,}
                </div>
            </div>

            <div class="context-sidebar-stat">
                <div class="context-sidebar-stat-label">
                    Avg Steps
                </div>
                <div class="context-sidebar-stat-value">
                    {fmt_number(avg_steps)}
                </div>
            </div>

            <div class="context-sidebar-stat">
                <div class="context-sidebar-stat-label">
                    Avg Active
                </div>
                <div class="context-sidebar-stat-value">
                    {fmt_number(avg_active)} min
                </div>
            </div>

            <div class="context-sidebar-stat">
                <div class="context-sidebar-stat-label">
                    Avg Sleep
                </div>
                <div class="context-sidebar-stat-value">
                    {fmt_number(avg_sleep, 1)} h
                </div>
            </div>

        </div>

        <div class="context-sidebar-status">
            <span class="context-sidebar-dot"></span>
            <span>
                Sidebar reflects the current analysis controls.
            </span>
        </div>

    </div>
    """
)

# EXECUTIVE READOUT
with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            EXECUTIVE READOUT
        </div>

        <div class="control-heading">
            Participant performance at a glance
        </div>

        <div class="section-copy">
            Headline participant-level measures for the currently
            selected operating population. Values represent
            participant-level averages rather than totals across
            recorded days.
        </div>
        """
    )

    kpi_cols = st.columns(5, gap="small")

    with kpi_cols[0]:
        st.metric(
            "Participants",
            f"{participant_count:,}",
            help=(
                "Unique participants represented "
                "in the current selection."
            ),
        )

    with kpi_cols[1]:
        st.metric(
            "Avg Daily Steps",
            (
                f"{avg_steps:,.0f}"
                if pd.notna(avg_steps)
                else "—"
            ),
            help=(
                "Mean participant-level "
                "average daily steps."
            ),
        )

    with kpi_cols[2]:
        st.metric(
            "Avg Active Minutes",
            (
                f"{avg_active:,.0f}"
                if pd.notna(avg_active)
                else "—"
            ),
            help=(
                "Mean participant-level "
                "average daily active minutes."
            ),
        )

    with kpi_cols[3]:
        st.metric(
            "Avg Sedentary Minutes",
            (
                f"{avg_sedentary:,.0f}"
                if pd.notna(avg_sedentary)
                else "—"
            ),
            help=(
                "Mean participant-level "
                "average daily sedentary minutes."
            ),
        )

    with kpi_cols[4]:
        st.metric(
            "Avg Sleep",
            (
                f"{avg_sleep:.1f} h"
                if pd.notna(avg_sleep)
                else "—"
            ),
            help=(
                "Mean participant-level "
                "average sleep duration."
            ),
        )

    render_html(
        f"""
        <div class="coverage-strip">
            <span class="coverage-dot"></span>
            <span>
                Analysis period: {date_meta}
                &nbsp;•&nbsp;
                Median observation coverage:
                {median_observation_days:.0f} days
                &nbsp;•&nbsp;
                Sleep coverage:
                {sleep_coverage_pct:.0f}%
                &nbsp;•&nbsp;
                Heart-rate coverage:
                {heart_rate_coverage_pct:.0f}%
            </span>
        </div>
        """
    )

# BUSINESS SIGNALS
with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            BUSINESS SIGNALS
        </div>

        <div class="control-heading">
            Participant operating signals
        </div>

        <div class="section-copy">
            Descriptive indicators that summarize activity
            distribution, high engagement, sedentary exposure,
            and measurement coverage for the selected population.
        </div>
        """
    )

    signal_cols = st.columns(4, gap="small")

    with signal_cols[0]:
        render_html(
            f"""
            <div class="signal-card accent">
                <div class="signal-label">
                    Lower Activity
                </div>
                <div class="signal-value">
                    {lower_activity_pct:.1f}%
                </div>
                <div class="signal-copy">
                    Participants averaging fewer than
                    5,000 daily steps.
                </div>
            </div>
            """
        )

    with signal_cols[1]:
        render_html(
            f"""
            <div class="signal-card blue">
                <div class="signal-label">
                    10K Step Segment
                </div>
                <div class="signal-value">
                    {high_activity_pct:.1f}%
                </div>
                <div class="signal-copy">
                    Participants averaging at least
                    10,000 daily steps.
                </div>
            </div>
            """
        )

    with signal_cols[2]:
        render_html(
            f"""
            <div class="signal-card yellow">
                <div class="signal-label">
                    Sedentary Exposure
                </div>
                <div class="signal-value">
                    {high_sedentary_pct:.1f}%
                </div>
                <div class="signal-copy">
                    Participants at or above the
                    participant-level 75th percentile
                    for sedentary minutes.
                </div>
            </div>
            """
        )

    with signal_cols[3]:
        render_html(
            f"""
            <div class="signal-card green">
                <div class="signal-label">
                    Sleep Coverage
                </div>
                <div class="signal-value">
                    {sleep_coverage_pct:.0f}%
                </div>
                <div class="signal-copy">
                    Participants with usable average
                    sleep-duration observations.
                </div>
            </div>
            """
        )

# POPULATION STRUCTURE
with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            POPULATION STRUCTURE
        </div>

        <div class="control-heading">
            Activity mix
        </div>

        <div class="section-copy">
            Participant distribution by average daily steps.
            Thresholds are descriptive reporting bands used
            consistently throughout the dashboard.
        </div>
        """
    )

    segment_df = segment_counts.reset_index()

    segment_df.columns = [
        "Engagement Segment",
        "Participants",
    ]

    segment_df["Share"] = (
        segment_df["Participants"]
        / participant_count
        * 100
    )

    fig_segment = px.bar(
        segment_df,
        x="Engagement Segment",
        y="Participants",
        text="Share",
        category_orders={
            "Engagement Segment": segment_order
        },
    )

    fig_segment.update_traces(
        marker_color="#fc5200",
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )

    fig_segment.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=330,
        showlegend=False,
        margin=dict(
            l=20,
            r=25,
            t=25,
            b=55,
        ),
        font=dict(color="#dfe4ea"),
        xaxis=dict(
            title=None,
            gridcolor="rgba(255,255,255,.025)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Participants",
            gridcolor="rgba(255,255,255,.055)",
            zeroline=False,
        ),
    )

    st.plotly_chart(
        fig_segment,
        use_container_width=True,
    )

# BEHAVIORAL RELATIONSHIP
with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            BEHAVIORAL RELATIONSHIP
        </div>

        <div class="control-heading">
            Activity vs. sedentary exposure
        </div>

        <div class="section-copy">
            Each point represents one participant. Horizontal position
            shows average sedentary minutes, vertical position shows
            average active minutes, and point size represents
            observation coverage.
        </div>
        """
    )

    scatter_df = summary.dropna(
        subset=[
            "Avg_Sedentary_Minutes",
            "Avg_Active_Minutes",
            "Observation_Days",
            "Avg_Steps",
        ]
    ).copy()

    if scatter_df.empty:

        st.info(
            "Insufficient complete data for the "
            "activity-versus-sedentary chart."
        )

    else:

        fig_scatter = px.scatter(
            scatter_df,
            x="Avg_Sedentary_Minutes",
            y="Avg_Active_Minutes",
            size="Observation_Days",
            color="Avg_Steps",
            hover_name="Id",
            color_continuous_scale=[
                "#123d63",
                "#2c75aa",
                "#6caed6",
            ],
            labels={
                "Avg_Sedentary_Minutes":
                    "Average Sedentary Minutes",
                "Avg_Active_Minutes":
                    "Average Active Minutes",
                "Avg_Steps":
                    "Average Daily Steps",
                "Observation_Days":
                    "Observation Days",
            },
        )

        fig_scatter.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=420,
            margin=dict(
                l=25,
                r=25,
                t=20,
                b=55,
            ),
            font=dict(color="#dfe4ea"),
            xaxis=dict(
                gridcolor="rgba(255,255,255,.055)",
                zeroline=False,
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,.055)",
                zeroline=False,
            ),
            coloraxis_colorbar=dict(
                title="Avg Steps",
                thickness=10,
                len=.65,
            ),
        )

        st.plotly_chart(
            fig_scatter,
            use_container_width=True,
        )

# PARTICIPANT EXCEPTIONS
ranked_steps = (
    summary
    .sort_values(
        "Avg_Steps",
        ascending=False,
        na_position="last",
    )
    .reset_index(drop=True)
)

top_participants = ranked_steps.head(8).copy()

bottom_participants = (
    ranked_steps
    .sort_values(
        "Avg_Steps",
        ascending=True,
        na_position="last",
    )
    .head(8)
    .copy()
)


with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            PARTICIPANT EXCEPTIONS
        </div>

        <div class="control-heading">
            Activity distribution by participant
        </div>

        <div class="section-copy">
            The upper and lower ends of the observed activity
            distribution are shown below. The complete participant
            record remains available in the appendix.
        </div>
        """
    )

    exception_cols = st.columns(2, gap="medium")

    with exception_cols[0]:

        render_html(
            """
            <div class="mini-label">
                Higher activity participants
            </div>
            """
        )

        top_plot_df = (
            top_participants
            .sort_values("Avg_Steps", ascending=True)
            .copy()
        )

        top_plot_df["Participant"] = (
            top_plot_df["Id"].astype(str)
        )

        fig_top = px.bar(
            top_plot_df,
            x="Avg_Steps",
            y="Participant",
            orientation="h",
            text="Avg_Steps",
        )

        fig_top.update_traces(
            marker_color="#65a9d8",
            texttemplate="%{text:,.0f}",
            textposition="outside",
            cliponaxis=False,
        )

        fig_top.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350,
            showlegend=False,
            margin=dict(
                l=15,
                r=55,
                t=10,
                b=35,
            ),
            xaxis=dict(
                title="Average Daily Steps",
                gridcolor="rgba(255,255,255,.05)",
                zeroline=False,
            ),
            yaxis=dict(
                title=None,
                gridcolor="rgba(255,255,255,.02)",
                zeroline=False,
            ),
        )

        st.plotly_chart(
            fig_top,
            use_container_width=True,
        )

    with exception_cols[1]:

        render_html(
            """
            <div class="mini-label">
                Lower activity participants
            </div>
            """
        )

        bottom_plot_df = (
            bottom_participants
            .sort_values("Avg_Steps", ascending=False)
            .copy()
        )

        bottom_plot_df["Participant"] = (
            bottom_plot_df["Id"].astype(str)
        )

        fig_bottom = px.bar(
            bottom_plot_df,
            x="Avg_Steps",
            y="Participant",
            orientation="h",
            text="Avg_Steps",
        )

        fig_bottom.update_traces(
            marker_color="#d87878",
            texttemplate="%{text:,.0f}",
            textposition="outside",
            cliponaxis=False,
        )

        fig_bottom.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350,
            showlegend=False,
            margin=dict(
                l=15,
                r=55,
                t=10,
                b=35,
            ),
            xaxis=dict(
                title="Average Daily Steps",
                gridcolor="rgba(255,255,255,.05)",
                zeroline=False,
            ),
            yaxis=dict(
                title=None,
                gridcolor="rgba(255,255,255,.02)",
                zeroline=False,
            ),
        )

        st.plotly_chart(
            fig_bottom,
            use_container_width=True,
        )

# WELLNESS CONTEXT
with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            WELLNESS CONTEXT
        </div>

        <div class="control-heading">
            Sleep and measurement coverage
        </div>

        <div class="section-copy">
            Sleep and heart-rate measures are shown alongside their
            observed coverage so that population patterns can be
            distinguished from incomplete measurement.
        </div>
        """
    )

    wellness_cols = st.columns(4, gap="small")

    with wellness_cols[0]:
        st.metric(
            "Avg Sleep",
            (
                f"{avg_sleep:.1f} h"
                if pd.notna(avg_sleep)
                else "—"
            ),
        )

    with wellness_cols[1]:
        st.metric(
            "Sleep Coverage",
            f"{sleep_coverage_pct:.0f}%",
        )

    with wellness_cols[2]:
        st.metric(
            "Heart Rate Coverage",
            f"{heart_rate_coverage_pct:.0f}%",
        )

    with wellness_cols[3]:
        st.metric(
            "Median Observation Days",
            f"{median_observation_days:.0f}",
        )

# REPORTING INDICATORS
with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            REPORTING INDICATORS
        </div>

        <div class="control-heading">
            Population signals
        </div>

        <div class="section-copy">
            Descriptive indicators for reporting and segmentation.
            They describe the observed population and do not establish
            causality or clinical significance.
        </div>
        """
    )

    signal_data = pd.DataFrame(
        {
            "Indicator": [
                "Lower activity",
                "Moderate activity",
                "Active",
                "Highly active",
                "Higher sedentary exposure",
            ],
            "Population": [
                lower_activity_pct,
                moderate_activity_pct,
                active_pct,
                high_activity_pct,
                high_sedentary_pct,
            ],
        }
    )

    fig_signals = px.bar(
        signal_data,
        x="Population",
        y="Indicator",
        orientation="h",
        text="Population",
    )

    fig_signals.update_traces(
        marker_color="#fc5200",
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )

    signal_max = float(signal_data["Population"].max())

    signal_range_max = max(
        signal_max * 1.18,
        10,
    )

    fig_signals.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=290,
        showlegend=False,
        margin=dict(
            l=20,
            r=60,
            t=15,
            b=35,
        ),
        xaxis=dict(
            title="Share of Participants",
            ticksuffix="%",
            range=[0, signal_range_max],
            gridcolor="rgba(255,255,255,.055)",
            zeroline=False,
        ),
        yaxis=dict(
            title=None,
            gridcolor="rgba(255,255,255,.02)",
            zeroline=False,
        ),
    )

    st.plotly_chart(
        fig_signals,
        use_container_width=True,
    )

# PARTICIPANT DETAIL
with st.container(border=True):

    render_html(
        """
        <div class="section-label">
            SUPPORTING DETAIL
        </div>

        <div class="control-heading">
            Participant-level appendix
        </div>

        <div class="section-copy">
            Detailed participant-level averages are retained for
            operational review and auditability after the executive
            reporting layer.
        </div>
        """
    )
    display_df = ranked_steps[
        [
            "Id",
            "Avg_Steps",
            "Avg_Calories",
            "Avg_Active_Minutes",
            "Avg_Sedentary_Minutes",
            "Avg_Sleep_Hours",
            "Avg_Heart_Rate",
            "Observation_Days",
            "Engagement Segment",
        ]
    ].copy()

    display_df.columns = [
        "Participant",
        "Avg Steps",
        "Avg Calories",
        "Avg Active Min",
        "Avg Sedentary Min",
        "Avg Sleep Hours",
        "Avg Heart Rate",
        "Observation Days",
        "Activity Segment",
    ]

    st.dataframe(
        display_df.style.format(
            {
                "Avg Steps": "{:,.0f}",
                "Avg Calories": "{:,.0f}",
                "Avg Active Min": "{:,.0f}",
                "Avg Sedentary Min": "{:,.0f}",
                "Avg Sleep Hours": "{:.1f}",
                "Avg Heart Rate": "{:.1f}",
                "Observation Days": "{:,.0f}",
            },
            na_rep="—",
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="Download participant summary",
        data=display_df.to_csv(index=False),
        file_name="participant_summary_v131.csv",
        mime="text/csv",
    )

# REPORTING NOTE
render_html(
    """
    <div class="report-footnote">
        Reporting note: participant averages are calculated from
        records available under the current dashboard filters.
        Activity segmentation uses average daily steps with thresholds
        of &lt;5,000, 5,000–7,499, 7,500–9,999, and ≥10,000 steps.
        Higher sedentary exposure is defined relative to the
        participant-level 75th percentile. These measures are
        descriptive and should be interpreted together with
        observation coverage and data completeness.
    </div>
    """
)
