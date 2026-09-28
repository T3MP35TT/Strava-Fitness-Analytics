from pathlib import Path
from textwrap import dedent
import base64

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Home | Strava Fitness Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
MASTER_PATH = BASE_DIR / "data" / "processed" / "fitness_daily_master.csv"
LOGO_PATH = BASE_DIR / "images" / "strava_logo.png"


# ============================================================
# LOAD MASTER DATASET
# ============================================================

@st.cache_data
def load_master_data(path):
    df = pd.read_csv(path)

    if "Date" not in df.columns:
        raise ValueError(
            "fitness_daily_master.csv must contain a 'Date' column."
        )

    if "Id" not in df.columns:
        raise ValueError(
            "fitness_daily_master.csv must contain an 'Id' column."
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["Date"]
    ).copy()

    numeric_columns = [
        "TotalSteps",
        "Calories",
        "VeryActiveMinutes",
        "FairlyActiveMinutes",
        "LightlyActiveMinutes",
        "SedentaryMinutes",
        "Total_Active_Minutes",
        "Sleep_Minutes",
        "Sleep_Efficiency_Pct",
        "HeartRate_Avg",
        "BMI",
        "Weight_Kg",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    if "Total_Active_Minutes" not in df.columns:

        active_columns = [
            column
            for column in [
                "VeryActiveMinutes",
                "FairlyActiveMinutes",
                "LightlyActiveMinutes",
            ]
            if column in df.columns
        ]

        if active_columns:
            df["Total_Active_Minutes"] = (
                df[active_columns]
                .fillna(0)
                .sum(axis=1)
            )

    if "Day_Of_Week" not in df.columns:
        df["Day_Of_Week"] = df["Date"].dt.day_name()

    if "Is_Weekend" not in df.columns:
        df["Is_Weekend"] = (
            df["Date"].dt.dayofweek >= 5
        )

    if "Meets_10k_Steps" not in df.columns:

        if "TotalSteps" in df.columns:
            df["Meets_10k_Steps"] = (
                df["TotalSteps"] >= 10000
            )

    if "Sleep_7h_Target" not in df.columns:

        if "Sleep_Minutes" in df.columns:
            df["Sleep_7h_Target"] = (
                df["Sleep_Minutes"] >= 420
            )

    return (
        df
        .sort_values(
            ["Date", "Id"]
        )
        .reset_index(drop=True)
    )


try:

    df = load_master_data(
        MASTER_PATH
    )

except FileNotFoundError:

    st.error(
        "The master dataset was not found.\n\n"
        f"Expected location: `{MASTER_PATH}`\n\n"
        "Place `fitness_daily_master.csv` inside "
        "`data/processed/` and restart the application."
    )

    st.stop()

except Exception as exc:

    st.error(
        f"Unable to load the master dataset: {exc}"
    )

    st.stop()


# ============================================================
# LOGO
# ============================================================

logo_html = ""

if LOGO_PATH.exists():

    try:

        logo_bytes = LOGO_PATH.read_bytes()

        logo_base64 = base64.b64encode(
            logo_bytes
        ).decode("utf-8")

        logo_html = f"""
        <img
            src="data:image/png;base64,{logo_base64}"
            class="fitness-home-title-logo"
            alt="Strava logo"
        >
        """

    except Exception:

        logo_html = ""


# ============================================================
# STYLING
# ============================================================

st.html(
    dedent(
        """
        <style>

        /* ==================================================
           GLOBAL
           ================================================== */

        .stApp {
            background:
                radial-gradient(
                    circle at 82% 8%,
                    rgba(255, 107, 26, 0.055),
                    transparent 28%
                ),
                #0b0d11;
        }


        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    circle at 82% 8%,
                    rgba(255, 107, 26, 0.04),
                    transparent 30%
                ),
                #0b0d11;
        }


        [data-testid="stHeader"] {
            background: transparent;
        }


        /*
         * Desktop top spacing.
         *
         * Increased to create the same breathing room
         * above the hero as shown in the reference image.
         *
         * Previous:
         *     padding-top: 1.45rem;
         *
         * Current:
         *     padding-top: 4.8rem;
         *
         * This moves the complete landing-page content
         * downward without changing the hero dimensions.
         */
        .block-container {
            max-width: 1450px;

            padding-top: 4.8rem;
            padding-bottom: 4rem;
        }


        h1,
        h2,
        h3,
        h4,
        h5,
        h6,
        p,
        li,
        label {
            color: #ffffff;
        }


        /* ==================================================
           SIDEBAR
           ================================================== */

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(
                    180deg,
                    #101218 0%,
                    #0b0d11 100%
                );

            border-right:
                1px solid
                rgba(255,255,255,0.07);
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
            border-radius: 7px !important;

            margin: 2px 8px !important;

            padding: 0 10px !important;

            height: 40px !important;

            min-height: 40px !important;

            box-sizing: border-box !important;

            display: flex !important;

            align-items: center !important;

            color:
                rgba(255,255,255,0.70) !important;

            font-size: 13px !important;

            font-weight: 700 !important;

            line-height: 1.15 !important;

            transition:
                background 0.15s ease,
                border 0.15s ease,
                color 0.15s ease !important;
        }


        [data-testid="stSidebarNav"] a:hover {
            color: #ffffff !important;

            background:
                rgba(255,107,26,0.08) !important;

            border:
                1px solid
                rgba(255,107,26,0.20) !important;
        }


        [data-testid="stSidebarNav"]
        a[aria-current="page"] {
            color: #ffffff !important;

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

            padding:
                0 10px !important;

            height: 40px !important;

            min-height: 40px !important;

            box-sizing: border-box !important;

            font-weight: 800 !important;
        }


        /* ==================================================
           SIDEBAR CONTENT
           ================================================== */

        .fitness-sidebar-divider {
            height: 1px;

            margin:
                14px 0 17px 0;

            background:
                rgba(255,255,255,0.12);
        }


        .fitness-sidebar-label {
            color: #ff6b1a;

            font-size: 0.54rem;

            font-weight: 850;

            letter-spacing: 0.14em;

            margin:
                15px 2px 7px 2px;

            text-transform: uppercase;
        }


        .fitness-sidebar-card {
            padding:
                10px 11px;

            border-radius: 8px;

            background:
                rgba(14,16,22,0.82);

            border:
                1px solid
                rgba(255,255,255,0.10);

            margin-bottom: 12px;
        }


        .fitness-sidebar-item-title {
            color:
                rgba(255,255,255,0.90);

            font-size: 0.62rem;

            font-weight: 750;

            margin-top: 4px;
        }


        .fitness-sidebar-item-text {
            color:
                rgba(255,255,255,0.45);

            font-size: 0.53rem;

            line-height: 1.4;

            margin:
                2px 0 6px 0;
        }


        .fitness-sidebar-tech {
            color:
                rgba(255,255,255,0.72);

            font-size: 0.61rem;

            line-height: 1.7;
        }


        .fitness-sidebar-author {
            margin-top: 2px;
        }


        .fitness-sidebar-label-small {
            color:
                rgba(255,255,255,0.36);

            font-size: 0.46rem;

            font-weight: 800;

            letter-spacing: 0.13em;

            margin-bottom: 4px;
        }


        .fitness-sidebar-author-name {
            color: #ffffff;

            font-size: 0.64rem;

            font-weight: 750;
        }


        .fitness-sidebar-author-role {
            color:
                rgba(255,255,255,0.40);

            font-size: 0.51rem;

            margin-top: 2px;
        }


        .fitness-sidebar-footer {
            margin-top: 14px;

            padding-top: 10px;

            border-top:
                1px solid
                rgba(255,255,255,0.08);

            color:
                rgba(255,255,255,0.24);

            font-size: 0.44rem;

            font-weight: 800;

            letter-spacing: 0.12em;

            text-align: center;
        }


        /* ==================================================
           HOME HERO
           COMPACT FROSTED / BLURRED GLASS TILE
           ================================================== */

        .fitness-home-hero {
            position: relative;

            isolation: isolate;

            padding:
                27px 48px 29px 48px;

            margin-bottom: 22px;

            min-height: 0;

            border-radius: 20px;

            background:
                linear-gradient(
                    110deg,
                    rgba(21,29,40,0.60),
                    rgba(14,18,26,0.52) 48%,
                    rgba(39,20,13,0.48) 100%
                );

            border:
                1px solid
                rgba(255,255,255,0.14);

            box-shadow:
                0 18px 48px
                rgba(0,0,0,0.34),
                inset 0 1px 0
                rgba(255,255,255,0.07);

            overflow: hidden;

            backdrop-filter:
                blur(24px)
                saturate(145%);

            -webkit-backdrop-filter:
                blur(24px)
                saturate(145%);
        }


        .fitness-home-hero::before {
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

            filter:
                blur(42px);

            transform:
                scale(1.05);

            opacity: 0.92;

            pointer-events: none;
        }


        .fitness-home-hero::after {
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

            filter:
                blur(34px);

            opacity: 0.92;

            pointer-events: none;
        }


        .fitness-home-hero > .fitness-glass-highlight {
            position: absolute;

            z-index: 1;

            left: -5%;
            top: -55%;

            width: 70%;
            height: 160%;

            background:
                linear-gradient(
                    115deg,
                    rgba(255,255,255,0.065),
                    transparent 48%
                );

            transform:
                rotate(-3deg);

            filter:
                blur(22px);

            pointer-events: none;
        }


        .fitness-home-hero > *:not(.fitness-glass-highlight) {
            position: relative;

            z-index: 3;
        }


        /* ==================================================
           HERO BADGE
           ================================================== */

        .fitness-badge {
            display: inline-block;

            padding:
                6px 13px;

            margin-bottom: 11px;

            border-radius: 30px;

            background:
                rgba(255,107,26,0.075);

            border:
                1px solid
                rgba(255,107,26,0.30);

            color:
                rgba(255,255,255,0.92);

            font-size: 0.65rem;

            font-weight: 800;

            letter-spacing: 0.115em;

            line-height: 1.25;

            box-shadow:
                inset 0 1px 0
                rgba(255,255,255,0.045);
        }


        /* ==================================================
           HERO TITLE
           ================================================== */

        .fitness-home-title {
            margin: 0;

            color: #ffffff;

            font-size: 2.72rem;

            font-weight: 900;

            line-height: 1.02;

            letter-spacing: -0.035em;

            display: flex;

            align-items: center;

            gap: 14px;
        }


        .fitness-home-title-logo {
            width: 49px;
            height: 49px;

            object-fit: contain;

            flex-shrink: 0;

            display: block;

            filter:
                drop-shadow(
                    0 6px 16px
                    rgba(255,107,26,0.22)
                );
        }


        .fitness-orange {
            color: #ff6b1a;
        }


        /* ==================================================
           HERO SUBTITLE
           ================================================== */

        .fitness-home-subtitle {
            margin-top: 10px;

            margin-bottom: 0;

            color:
                rgba(255,255,255,0.76);

            font-size: 0.91rem;

            line-height: 1.45;

            max-width: 870px;
        }


        /* ==================================================
           HERO TAGLINE
           ================================================== */

        .fitness-home-tagline {
            margin-top: 12px;

            color:
                rgba(255,255,255,0.58);

            font-size: 0.65rem;

            font-weight: 750;

            letter-spacing: 0.075em;

            line-height: 1.3;
        }


        /* ==================================================
           MAIN CARDS
           ================================================== */

        .fitness-card {
            padding:
                26px 28px;

            margin-bottom: 22px;

            border-radius: 14px;

            background:
                rgba(14,16,22,0.76);

            border:
                1px solid
                rgba(255,255,255,0.09);

            box-shadow:
                0 8px 30px
                rgba(0,0,0,0.16);
        }


        .fitness-section-label {
            color: #ff6b1a;

            font-size: 0.65rem;

            font-weight: 850;

            letter-spacing: 0.16em;

            text-transform: uppercase;

            margin-bottom: 7px;
        }


        .fitness-section-title {
            color: #ffffff;

            font-size: 1.72rem;

            font-weight: 850;

            line-height: 1.2;

            margin-bottom: 14px;
        }


        .fitness-card-text {
            color:
                rgba(255,255,255,0.72);

            font-size: 0.94rem;

            line-height: 1.7;
        }


        /* ==================================================
           KPI CARDS
           ================================================== */

        .fitness-kpi-grid {
            display: grid;

            grid-template-columns:
                repeat(5, minmax(0, 1fr));

            gap: 14px;

            margin-top: 18px;
        }


        .fitness-kpi {
            min-height: 108px;

            padding:
                17px 17px 15px 17px;

            border-radius: 12px;

            background:
                linear-gradient(
                    145deg,
                    rgba(23,26,34,0.96),
                    rgba(15,17,23,0.96)
                );

            border:
                1px solid
                rgba(255,255,255,0.085);

            box-shadow:
                inset 0 1px 0
                rgba(255,255,255,0.025),
                0 7px 20px
                rgba(0,0,0,0.13);
        }


        .fitness-kpi-label {
            color:
                rgba(255,255,255,0.50);

            font-size: 0.60rem;

            font-weight: 800;

            letter-spacing: 0.10em;

            text-transform: uppercase;

            margin-bottom: 12px;
        }


        .fitness-kpi-value {
            color: #ffffff;

            font-size: 1.55rem;

            font-weight: 900;

            line-height: 1.1;

            letter-spacing: -0.025em;
        }


        .fitness-kpi-accent {
            color: #ff6b1a;
        }


        /* ==================================================
           FEATURE ROWS
           ================================================== */

        .fitness-feature {
            padding:
                12px 0;

            border-bottom:
                1px solid
                rgba(255,255,255,0.07);

            color:
                rgba(255,255,255,0.82);

            font-size: 0.91rem;

            line-height: 1.5;
        }


        .fitness-feature:last-child {
            border-bottom: none;
        }


        .fitness-feature-icon {
            display: inline-block;

            width: 30px;

            color: #ff6b1a;

            font-weight: 800;
        }


        /* ==================================================
           TECHNOLOGY
           ================================================== */

        .fitness-tech-row {
            display: flex;

            flex-wrap: wrap;

            gap: 9px;

            margin-top: 16px;
        }


        .fitness-tech-chip {
            display: inline-block;

            padding:
                8px 13px;

            border-radius: 8px;

            background:
                rgba(255,107,26,0.07);

            border:
                1px solid
                rgba(255,107,26,0.22);

            color:
                rgba(255,255,255,0.88);

            font-size: 0.76rem;

            font-weight: 750;
        }


        /* ==================================================
           DATA SOURCE
           ================================================== */

        .fitness-source {
            padding:
                13px 16px;

            border-radius: 9px;

            background:
                rgba(255,107,26,0.055);

            border:
                1px solid
                rgba(255,107,26,0.18);

            color:
                rgba(255,255,255,0.82);

            font-size: 0.86rem;
        }


        /* ==================================================
           FOLDER STRUCTURE
           ================================================== */

        .fitness-code {
            padding:
                20px 22px;

            border-radius: 10px;

            background: #15181f;

            border:
                1px solid
                rgba(255,255,255,0.08);

            color:
                rgba(255,255,255,0.82);

            font-family:
                Consolas,
                "Cascadia Code",
                monospace;

            font-size: 0.78rem;

            line-height: 1.65;

            overflow-x: auto;

            white-space: pre;
        }


        /* ==================================================
           STEPS
           ================================================== */

        .fitness-step {
            display: flex;

            gap: 14px;

            padding:
                11px 0;

            color:
                rgba(255,255,255,0.80);

            font-size: 0.91rem;

            line-height: 1.5;
        }


        .fitness-step-number {
            flex:
                0 0 27px;

            width: 27px;

            height: 27px;

            display: flex;

            align-items: center;

            justify-content: center;

            border-radius: 50%;

            background:
                rgba(255,107,26,0.12);

            border:
                1px solid
                rgba(255,107,26,0.35);

            color: #ff6b1a;

            font-size: 0.75rem;

            font-weight: 850;
        }


        .fitness-inline-code {
            display: inline-block;

            padding:
                3px 7px;

            border-radius: 5px;

            background:
                rgba(255,255,255,0.06);

            color: #ff9a62;

            font-family:
                Consolas,
                monospace;

            font-size: 0.82rem;
        }


        /* ==================================================
           STREAMLIT METRICS
           ================================================== */

        div[data-testid="stMetric"] {
            background:
                rgba(14,16,22,0.72);

            border:
                1px solid
                rgba(255,255,255,0.09);

            border-radius: 12px;

            padding:
                0.75rem 0.85rem;
        }


        div[data-testid="stMetricLabel"] {
            color:
                rgba(255,255,255,0.62)
                !important;
        }


        div[data-testid="stMetricValue"] {
            color:
                #ffffff !important;
        }


        /* ==================================================
           RESPONSIVE
           ================================================== */

        @media (max-width: 1100px) {

            .fitness-kpi-grid {
                grid-template-columns:
                    repeat(3, minmax(0, 1fr));
            }
        }


        @media (max-width: 900px) {

            .block-container {
                padding-top: 1rem;
            }


            .fitness-home-hero {
                padding:
                    24px 28px 26px 28px;
            }


            .fitness-home-title {
                font-size: 2.25rem;
            }


            .fitness-home-title-logo {
                width: 44px;
                height: 44px;
            }
        }


        @media (max-width: 650px) {

            .fitness-kpi-grid {
                grid-template-columns:
                    repeat(2, minmax(0, 1fr));
            }


            .fitness-home-title {
                gap: 10px;

                font-size: 1.9rem;
            }


            .fitness-home-title-logo {
                width: 39px;
                height: 39px;
            }


            .fitness-home-hero {
                padding:
                    22px 22px 24px 22px;

                border-radius: 17px;
            }


            .fitness-home-subtitle {
                font-size: 0.82rem;
            }


            .fitness-home-tagline {
                font-size: 0.57rem;

                line-height: 1.6;
            }
        }

        </style>
        """
    )
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.html(
        dedent(
            """
            <div class="fitness-sidebar-divider"></div>

            <div class="fitness-sidebar-label">
                PROJECT OVERVIEW
            </div>

            <div class="fitness-sidebar-card">

                <div class="fitness-sidebar-item-title">
                    🏃 Activity Analytics
                </div>

                <div class="fitness-sidebar-item-text">
                    Activity, steps, calories, intensity, and sedentary behavior.
                </div>

                <div class="fitness-sidebar-item-title">
                    😴 Sleep & Wellness
                </div>

                <div class="fitness-sidebar-item-text">
                    Sleep, heart rate, and wellness patterns.
                </div>

                <div class="fitness-sidebar-item-title">
                    👥 Participant Analysis
                </div>

                <div class="fitness-sidebar-item-text">
                    Participant-level behavior and engagement analysis.
                </div>

                <div class="fitness-sidebar-item-title">
                    📊 Statistical Analysis
                </div>

                <div class="fitness-sidebar-item-text">
                    Statistical testing and relationship analysis.
                </div>

                <div class="fitness-sidebar-item-title">
                    🤖 Predictive Insights
                </div>

                <div class="fitness-sidebar-item-text">
                    Predictive modeling and analytical insights.
                </div>

                <div class="fitness-sidebar-item-title">
                    💼 Business Insights
                </div>

                <div class="fitness-sidebar-item-text">
                    Business-oriented findings and recommendations.
                </div>

            </div>

            <div class="fitness-sidebar-label">
                TECH STACK
            </div>

            <div class="fitness-sidebar-card fitness-sidebar-tech">

                <div>🐍 Python</div>
                <div>📊 Pandas</div>
                <div>📈 Plotly</div>
                <div>🎨 Streamlit</div>
                <div>📐 Statistics</div>
                <div>🤖 Machine Learning</div>

            </div>

            <div class="fitness-sidebar-card fitness-sidebar-author">

                <div class="fitness-sidebar-label-small">
                    PROJECT AUTHOR
                </div>

                <div class="fitness-sidebar-author-name">
                    Kartikey Singh
                </div>

                <div class="fitness-sidebar-author-role">
                    Data Analytics • Python • SQL
                </div>

            </div>

            <div class="fitness-sidebar-footer">
                STRAVA FITNESS ANALYTICS
            </div>
            """
        )
    )


# ============================================================
# HOME HERO
# ============================================================

hero_html = f"""
<div class="fitness-home-hero">

    <div class="fitness-glass-highlight"></div>

    <div class="fitness-badge">
        🏃 HOME • FITNESS ANALYTICS ARENA
    </div>

    <div class="fitness-home-title">

        {logo_html}

        <span>
            <span class="fitness-orange">Strava</span>
            Fitness Analytics
        </span>

    </div>

    <div class="fitness-home-subtitle">

        End-to-end analysis of activity, calorie expenditure,
        sedentary behavior, sleep, heart rate, and participant
        behavior using a validated daily fitness master dataset.

    </div>

    <div class="fitness-home-tagline">

        🐍 PYTHON
        &nbsp; • &nbsp;
        📊 PANDAS
        &nbsp; • &nbsp;
        📈 PLOTLY
        &nbsp; • &nbsp;
        🎨 STREAMLIT
        &nbsp; • &nbsp;
        🤖 MACHINE LEARNING

    </div>

</div>
"""

st.html(hero_html)


# ============================================================
# DATASET SNAPSHOT
# ============================================================

participant_days = len(df)

participants = df["Id"].nunique()

avg_steps = (
    f"{df['TotalSteps'].mean():,.0f}"
    if "TotalSteps" in df.columns
    else "—"
)

avg_calories = (
    f"{df['Calories'].mean():,.0f}"
    if "Calories" in df.columns
    else "—"
)

goal_rate = (
    f"{df['Meets_10k_Steps'].mean() * 100:.1f}%"
    if "Meets_10k_Steps" in df.columns
    else "—"
)


dataset_snapshot_html = f"""
<div class="fitness-card">

    <div class="fitness-section-label">
        DATASET SNAPSHOT
    </div>

    <div class="fitness-section-title">
        Fitness data at a glance
    </div>

    <div class="fitness-card-text">

        A concise view of the current analytical dataset,
        participant coverage, activity volume, calorie expenditure,
        and 10K activity-target attainment.

    </div>

    <div class="fitness-kpi-grid">

        <div class="fitness-kpi">

            <div class="fitness-kpi-label">
                Participant-Days
            </div>

            <div class="fitness-kpi-value">
                {participant_days:,}
            </div>

        </div>


        <div class="fitness-kpi">

            <div class="fitness-kpi-label">
                Participants
            </div>

            <div class="fitness-kpi-value">
                {participants:,}
            </div>

        </div>


        <div class="fitness-kpi">

            <div class="fitness-kpi-label">
                Avg Daily Steps
            </div>

            <div class="fitness-kpi-value">
                {avg_steps}
            </div>

        </div>


        <div class="fitness-kpi">

            <div class="fitness-kpi-label">
                Avg Calories
            </div>

            <div class="fitness-kpi-value">
                {avg_calories}
            </div>

        </div>


        <div class="fitness-kpi">

            <div class="fitness-kpi-label">
                10K Goal Rate
            </div>

            <div class="fitness-kpi-value fitness-kpi-accent">
                {goal_rate}
            </div>

        </div>

    </div>

</div>
"""

st.html(dataset_snapshot_html)


# ============================================================
# ANALYTICAL SOURCE
# ============================================================

start_date = df["Date"].min()

end_date = df["Date"].max()


analytical_source_html = f"""
<div class="fitness-card">

    <div class="fitness-section-label">
        ANALYTICAL SOURCE
    </div>

    <div class="fitness-section-title">
        Single source of truth
    </div>

    <div class="fitness-source">

        <strong>
            fitness_daily_master.csv
        </strong>

        <br>

        All dashboard calculations are performed from this
        validated participant-date master dataset.

        <br><br>

        Coverage:

        <strong>
            {start_date:%d %b %Y}
        </strong>

        →

        <strong>
            {end_date:%d %b %Y}
        </strong>

        &nbsp; • &nbsp;

        <strong>
            {participant_days:,}
        </strong>

        participant-day records

        &nbsp; • &nbsp;

        <strong>
            {participants:,}
        </strong>

        participants

    </div>

</div>
"""

st.html(analytical_source_html)


# ============================================================
# PROJECT OVERVIEW
# ============================================================

left_col, right_col = st.columns(
    2,
    gap="large",
)


with left_col:

    st.html(
        dedent(
            """
            <div class="fitness-card">

                <div class="fitness-section-label">
                    PROJECT OVERVIEW
                </div>

                <div class="fitness-section-title">
                    About this project
                </div>

                <div class="fitness-card-text">

                    This project transforms integrated fitness-tracker data
                    into a participant-date analytical layer and an
                    interactive business-style analytics application.

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        ✓
                    </span>

                    Validated participant-date master dataset

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        ✓
                    </span>

                    Activity, steps, calories, intensity, and sedentary analysis

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        ✓
                    </span>

                    Sleep and heart-rate analysis

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        ✓
                    </span>

                    Participant-level behavioral analysis

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        ✓
                    </span>

                    Statistical and predictive analysis

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        ✓
                    </span>

                    Business-oriented insights and recommendations

                </div>

            </div>
            """
        )
    )


with right_col:

    st.html(
        dedent(
            """
            <div class="fitness-card">

                <div class="fitness-section-label">
                    ANALYTICAL WORKFLOW
                </div>

                <div class="fitness-section-title">
                    From data to insight
                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        01
                    </span>

                    Data Cleaning & Validation

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        02
                    </span>

                    Exploratory Data Analysis

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        03
                    </span>

                    Activity & Wellness Analysis

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        04
                    </span>

                    Participant Segmentation

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        05
                    </span>

                    Statistical Analysis

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        06
                    </span>

                    Predictive Insights

                </div>

                <div class="fitness-feature">

                    <span class="fitness-feature-icon">
                        07
                    </span>

                    Business Interpretation

                </div>

            </div>
            """
        )
    )


# ============================================================
# TECHNOLOGY
# ============================================================

st.html(
    dedent(
        """
        <div class="fitness-card">

            <div class="fitness-section-label">
                TECHNOLOGY
            </div>

            <div class="fitness-section-title">
                Tools used
            </div>

            <div class="fitness-card-text">

                The application uses Python for data preparation and analysis,
                Pandas for data manipulation, Plotly for interactive
                visualization, Streamlit for the dashboard layer, and
                statistical and machine-learning methods for deeper analysis.

            </div>

            <div class="fitness-tech-row">

                <span class="fitness-tech-chip">
                    🐍 Python
                </span>

                <span class="fitness-tech-chip">
                    📊 Pandas
                </span>

                <span class="fitness-tech-chip">
                    📈 Plotly
                </span>

                <span class="fitness-tech-chip">
                    🎨 Streamlit
                </span>

                <span class="fitness-tech-chip">
                    📐 Statistics
                </span>

                <span class="fitness-tech-chip">
                    🤖 Machine Learning
                </span>

            </div>

        </div>
        """
    )
)


# ============================================================
# PROJECT STRUCTURE
# ============================================================

folder_structure = """Strava Fitness App Project/
├── app.py
├── requirements.txt
│
├── data/
│   └── processed/
│       └── fitness_daily_master.csv
│
├── notebooks/
│   └── 01_Fitness_Data_Cleaning_and_Merging.ipynb
│
├── pages/
│   ├── 1_Executive_Overview.py
│   ├── 2_Activity_and_Calories.py
│   ├── 3_Sleep_and_Wellness.py
│   ├── 4_Participant_Analysis.py
│   ├── 5_Statistical_Analysis.py
│   ├── 6_Predictive_Insights.py
│   ├── 7_SQL_Playground.py
│   ├── 8_Data_Quality.py
│   └── 9_Business_Insights.py
│
├── utils/
│   ├── data.py
│   └── theme.py
│
├── images/
│   └── strava_logo.png
│
├── .gitignore
├── BRANDING_NOTE.md
└── README.md"""


project_structure_html = f"""
<div class="fitness-card">

    <div class="fitness-section-label">
        PROJECT STRUCTURE
    </div>

    <div class="fitness-section-title">
        Folder structure
    </div>

    <div class="fitness-card-text">

        The dashboard uses the cleaned master dataset as the
        single analytical source. The source CSVs used during
        the cleaning stage are not required by the dashboard
        runtime.

    </div>

    <div style="height:18px;"></div>

    <div class="fitness-code">{folder_structure}</div>

</div>
"""

st.html(project_structure_html)


# ============================================================
# GETTING STARTED
# ============================================================

st.html(
    dedent(
        """
        <div class="fitness-card">

            <div class="fitness-section-label">
                GETTING STARTED
            </div>

            <div class="fitness-section-title">
                Run the dashboard
            </div>

            <div class="fitness-step">

                <div class="fitness-step-number">
                    1
                </div>

                <div>

                    Install the project dependencies using

                    <span class="fitness-inline-code">
                        pip install -r requirements.txt
                    </span>

                </div>

            </div>

            <div class="fitness-step">

                <div class="fitness-step-number">
                    2
                </div>

                <div>

                    Confirm that

                    <span class="fitness-inline-code">
                        data/processed/fitness_daily_master.csv
                    </span>

                    exists.

                </div>

            </div>

            <div class="fitness-step">

                <div class="fitness-step-number">
                    3
                </div>

                <div>

                    Start the application using

                    <span class="fitness-inline-code">
                        streamlit run app.py
                    </span>

                </div>

            </div>

            <div class="fitness-step">

                <div class="fitness-step-number">
                    4
                </div>

                <div>

                    Use the native Streamlit navigation on the left
                    to explore the analytical pages.

                </div>

            </div>

        </div>
        """
    )
)


# ============================================================
# AUTHOR
# ============================================================

st.html(
    dedent(
        """
        <div class="fitness-card">

            <div class="fitness-section-label">
                PROJECT AUTHOR
            </div>

            <div class="fitness-section-title">
                Kartikey Singh
            </div>

            <div class="fitness-card-text">
                Data Analytics • Python • SQL • Streamlit • Business Intelligence
            </div>

        </div>
        """
    )
)


# ============================================================
# FOOTER
# ============================================================

st.html(
    dedent(
        """
        <div style="
            text-align:center;
            padding:10px 0 20px 0;
            color:rgba(255,255,255,0.30);
            font-size:0.68rem;
            letter-spacing:0.10em;
            font-weight:700;
        ">
            STRAVA FITNESS ANALYTICS
        </div>
        """
    )
)