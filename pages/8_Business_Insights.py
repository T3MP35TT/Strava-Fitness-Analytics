from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data import (
    load_data,
    activity_groups,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Business Insights | Fitness Analytics",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HTML HELPER
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
# ROOT / LOGO
# ============================================================

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

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
# STYLING
# ============================================================

render_html(
    """
    <style>

    .block-container {
        padding-top: 2.8rem !important;
        padding-bottom: 3rem !important;
        max-width: 1500px !important;
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

    /* --------------------------------------------------------
       Hero
       -------------------------------------------------------- */

    .business-hero {
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

        /*
        Move the entire hero tile down.
        Nothing inside the tile is repositioned.
        */
        margin: 30px 0 20px 0;

        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    .business-hero-eyebrow {
        color: #ff6419;
        font-size: 0.56rem;
        font-weight: 900;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .business-hero-row {
        display: flex;
        align-items: center;
        gap: 11px;
    }

    .business-hero-logo {
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

    .business-hero-logo img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
    }

    .business-hero-title {
        color: #ffffff;
        font-size: clamp(2.25rem, 3.15vw, 3.2rem);
        font-weight: 900;
        letter-spacing: -2.1px;
        line-height: 1;
        margin: 0;
    }

    .business-hero-title-accent {
        color: #fc5200;
    }

    .business-hero-description {
        color: #aab2bd;
        font-size: 0.76rem;
        line-height: 1.6;
        max-width: 1150px;
        margin-top: 13px;
    }

    /* --------------------------------------------------------
       Section shells
       -------------------------------------------------------- */

    .section-shell {
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 15px;
        background: rgba(12,14,19,0.72);
        padding: 18px;
        margin-bottom: 14px;
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

    /* --------------------------------------------------------
       KPI cards
       -------------------------------------------------------- */

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

    /* --------------------------------------------------------
       Opportunity cards
       -------------------------------------------------------- */

    .opportunity-card {
        background: #0d0f14;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 12px;
        padding: 15px 16px;
        min-height: 142px;
        margin-bottom: 12px;
    }

    .opportunity-label {
        color: #ff6419;
        font-size: 0.52rem;
        font-weight: 900;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .opportunity-title {
        color: #ffffff;
        font-size: 0.86rem;
        font-weight: 800;
        line-height: 1.3;
        margin-bottom: 7px;
    }

    .opportunity-copy {
        color: rgba(255,255,255,0.62);
        font-size: 0.68rem;
        line-height: 1.5;
        margin: 0;
    }

    .opportunity-block {
        margin-top: 10px;
    }

    .opportunity-field {
        margin-top: 9px;
        padding-top: 8px;
        border-top: 1px solid rgba(255,255,255,0.07);
    }

    .opportunity-field-label {
        color: #7f8792;
        font-size: 0.48rem;
        font-weight: 900;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        margin-bottom: 3px;
    }

    .opportunity-field-value {
        color: rgba(255,255,255,0.72);
        font-size: 0.64rem;
        line-height: 1.42;
    }

    /* --------------------------------------------------------
       Insight / governance cards
       -------------------------------------------------------- */

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
# LOAD DATA
# ============================================================

try:

    df = load_data()

except Exception as exc:

    st.error(
        f"Unable to load the fitness dataset: {exc}"
    )

    st.stop()


filtered = st.session_state.get(
    "global_filtered",
    df,
).copy()


if filtered.empty:

    st.warning(
        "No records match the current filters."
    )

    st.stop()


# ============================================================
# NORMALIZATION
# ============================================================

numeric_columns = [
    "Meets_10k_Steps",
    "SedentaryMinutes",
    "Total_Active_Minutes",
    "Sleep_Minutes",
    "Calories",
    "TotalSteps",
]

for column in numeric_columns:

    if column in filtered.columns:

        filtered[column] = pd.to_numeric(
            filtered[column],
            errors="coerce",
        )


if "Date" in filtered.columns:

    filtered["Date"] = pd.to_datetime(
        filtered["Date"],
        errors="coerce",
    )


# ============================================================
# METRICS
# ============================================================

goal_rate = (
    filtered["Meets_10k_Steps"]
    .mean()
    * 100
    if "Meets_10k_Steps" in filtered.columns
    else np.nan
)

avg_sedentary = (
    filtered["SedentaryMinutes"].mean()
    if "SedentaryMinutes" in filtered.columns
    else np.nan
)

avg_active = (
    filtered["Total_Active_Minutes"].mean()
    if "Total_Active_Minutes" in filtered.columns
    else np.nan
)

avg_sleep = (
    filtered["Sleep_Minutes"].mean() / 60.0
    if "Sleep_Minutes" in filtered.columns
    and filtered["Sleep_Minutes"].notna().any()
    else np.nan
)

sleep_present = (
    filtered["Sleep_Minutes"].notna().mean() * 100
    if "Sleep_Minutes" in filtered.columns
    and len(filtered) > 0
    else np.nan
)

participant_count = (
    filtered["Id"].nunique()
    if "Id" in filtered.columns
    else 0
)

record_count = len(filtered)


def fmt_number(
    value,
    decimals=0,
    suffix="",
):
    if pd.isna(value):
        return "—"

    return (
        f"{float(value):,.{decimals}f}"
        f"{suffix}"
    )


# ============================================================
# ACTIVITY GROUPS
# ============================================================

try:

    activity = activity_groups(
        filtered
    )

except Exception:
    activity = filtered.copy()

if activity is None:
    activity = filtered.copy()


# ============================================================
# HERO
# ============================================================

render_html(
    f"""
    <div class="business-hero">

        <div class="business-hero-eyebrow">
            HOME&nbsp;&nbsp;•&nbsp;&nbsp;BUSINESS INSIGHTS
        </div>

        <div class="business-hero-row">

            <div class="business-hero-logo">
                {logo_html}
            </div>

            <div class="business-hero-title">
                <span class="business-hero-title-accent">
                    Business
                </span>
                <span> Insights</span>
            </div>

        </div>

        <div class="business-hero-description">
            Translate analytical signals into product, engagement,
            and monitoring opportunities across the selected population.
        </div>

    </div>
    """
)


# ============================================================
# EXECUTIVE READOUT
# ============================================================

render_html(
    """
    <div class="section-shell">

        <div class="section-eyebrow">
            EXECUTIVE READOUT
        </div>

        <div class="section-title">
            Current business signals at a glance
        </div>

        <div class="section-description">
            Headline indicators for the currently selected reporting
            population. These are descriptive analytics, not clinical
            recommendations.
        </div>

    </div>
    """
)


k1, k2, k3, k4 = st.columns(
    4,
    gap="medium",
)

with k1:

    render_html(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                10K Goal Rate
            </div>

            <div class="kpi-value">
                {fmt_number(goal_rate, 1, "%")}
            </div>

            <div class="kpi-help">
                Share of observed participant-days meeting 10K steps.
            </div>

        </div>
        """
    )

with k2:

    render_html(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                Avg Sedentary Time
            </div>

            <div class="kpi-value">
                {fmt_number(avg_sedentary, 0, " min")}
            </div>

            <div class="kpi-help">
                Mean recorded sedentary minutes per participant-day.
            </div>

        </div>
        """
    )

with k3:

    render_html(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                Avg Active Time
            </div>

            <div class="kpi-value">
                {fmt_number(avg_active, 0, " min")}
            </div>

            <div class="kpi-help">
                Mean recorded active minutes per participant-day.
            </div>

        </div>
        """
    )

with k4:

    render_html(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                Avg Sleep
            </div>

            <div class="kpi-value">
                {fmt_number(avg_sleep, 1, " hrs")}
            </div>

            <div class="kpi-help">
                Mean recorded sleep duration where sleep data exists.
            </div>

        </div>
        """
    )


# ============================================================
# BUSINESS OPPORTUNITIES
# ============================================================

render_html(
    """
    <div class="section-shell">

        <div class="section-eyebrow">
            BUSINESS OPPORTUNITIES
        </div>

        <div class="section-title">
            Signals → Implications → Actions → KPIs
        </div>

        <div class="section-description">
            Convert observed patterns into testable business opportunities.
            Each item separates what the data shows from what a product or
            engagement team could test and how success could be measured.
        </div>

    </div>
    """
)


business_opportunities = []


# ------------------------------------------------------------
# Goal engagement
# ------------------------------------------------------------

if pd.notna(goal_rate):

    if goal_rate < 50:

        goal_signal = (
            f"{goal_rate:.1f}% of measured participant-days "
            "met the 10K-step benchmark."
        )

        goal_implication = (
            "A substantial share of observed days did not reach "
            "the selected activity benchmark."
        )

        goal_action = (
            "Test personalized progression, streaks, or weekly "
            "progress feedback rather than relying on one fixed goal."
        )

    else:

        goal_signal = (
            f"{goal_rate:.1f}% of measured participant-days "
            "met the 10K-step benchmark."
        )

        goal_implication = (
            "The fixed 10K benchmark is already achieved on a "
            "substantial share of observed days."
        )

        goal_action = (
            "Test progressive or personalized goals to maintain "
            "engagement among participants who already meet the baseline."
        )

    business_opportunities.append(
        {
            "title": "Goal engagement",
            "signal": goal_signal,
            "implication": goal_implication,
            "action": goal_action,
            "kpi": (
                "10K attainment rate · 7-day active participation · "
                "goal completion rate"
            ),
        }
    )


# ------------------------------------------------------------
# Sedentary behavior
# ------------------------------------------------------------

if pd.notna(avg_sedentary):

    business_opportunities.append(
        {
            "title": "Sedentary behavior",
            "signal": (
                f"Average sedentary time is "
                f"{avg_sedentary:,.0f} minutes per participant-day."
            ),
            "implication": (
                "Extended inactivity is a measurable population-level "
                "behavioral signal that may warrant engagement testing."
            ),
            "action": (
                "Test inactivity reminders, movement-break prompts, "
                "or time-based re-engagement experiences."
            ),
            "kpi": (
                "Average sedentary minutes · active minutes · "
                "reminder engagement rate"
            ),
        }
    )


# ------------------------------------------------------------
# Behavioral segmentation
# ------------------------------------------------------------

if (
    not activity.empty
    and "Activity_Level" in activity.columns
    and "Calories" in activity.columns
):

    high_values = pd.to_numeric(
        activity.loc[
            activity["Activity_Level"]
            == "High Activity",
            "Calories",
        ],
        errors="coerce",
    ).dropna()

    low_values = pd.to_numeric(
        activity.loc[
            activity["Activity_Level"]
            == "Low Activity",
            "Calories",
        ],
        errors="coerce",
    ).dropna()

    high = (
        high_values.mean()
        if not high_values.empty
        else np.nan
    )

    low = (
        low_values.mean()
        if not low_values.empty
        else np.nan
    )

    if pd.notna(high) or pd.notna(low):

        low_text = (
            f"{low:,.0f}"
            if pd.notna(low)
            else "—"
        )

        high_text = (
            f"{high:,.0f}"
            if pd.notna(high)
            else "—"
        )

        business_opportunities.append(
            {
                "title": "Behavioral segmentation",
                "signal": (
                    f"Average calorie profiles differ across activity "
                    f"groups: Low Activity ≈ {low_text} and "
                    f"High Activity ≈ {high_text} calories/day."
                ),
                "implication": (
                    "A single engagement experience may not fit all "
                    "observed activity segments."
                ),
                "action": (
                    "Test differentiated challenges, messaging, or "
                    "progression by activity segment."
                ),
                "kpi": (
                    "Engagement rate by segment · challenge completion · "
                    "7-day retention"
                ),
            }
        )


# ------------------------------------------------------------
# Sleep data opportunity
# ------------------------------------------------------------

if pd.notna(sleep_present):

    business_opportunities.append(
        {
            "title": "Sleep data coverage",
            "signal": (
                f"Recorded sleep is available for "
                f"{sleep_present:.1f}% of selected participant-days."
            ),
            "implication": (
                "Sleep-related conclusions are constrained by incomplete "
                "measurement coverage."
            ),
            "action": (
                "Prioritize data-capture coverage and instrumentation "
                "before using sleep signals as a broad product KPI."
            ),
            "kpi": (
                "Sleep-data coverage · valid sleep records · "
                "sleep-feature adoption"
            ),
        }
    )


# ------------------------------------------------------------
# Render opportunities
# ------------------------------------------------------------

for index in range(
    0,
    len(business_opportunities),
    2,
):

    pair = business_opportunities[
        index:index + 2
    ]

    cols = st.columns(
        len(pair),
        gap="medium",
    )

    for col, opportunity in zip(
        cols,
        pair,
    ):

        with col:

            render_html(
                f"""
                <div class="opportunity-card">

                    <div class="opportunity-label">
                        BUSINESS OPPORTUNITY
                    </div>

                    <div class="opportunity-title">
                        {opportunity["title"]}
                    </div>

                    <div class="opportunity-block">

                        <div class="opportunity-field">
                            <div class="opportunity-field-label">
                                Observed signal
                            </div>
                            <div class="opportunity-field-value">
                                {opportunity["signal"]}
                            </div>
                        </div>

                        <div class="opportunity-field">
                            <div class="opportunity-field-label">
                                Business implication
                            </div>
                            <div class="opportunity-field-value">
                                {opportunity["implication"]}
                            </div>
                        </div>

                        <div class="opportunity-field">
                            <div class="opportunity-field-label">
                                Potential action
                            </div>
                            <div class="opportunity-field-value">
                                {opportunity["action"]}
                            </div>
                        </div>

                        <div class="opportunity-field">
                            <div class="opportunity-field-label">
                                Success KPIs
                            </div>
                            <div class="opportunity-field-value">
                                {opportunity["kpi"]}
                            </div>
                        </div>

                    </div>

                </div>
                """
            )


render_html(
    """
    <div class="interpretation">

        <div class="interpretation-title">
            Decision discipline
        </div>

        <p class="interpretation-copy">
            The action and KPI fields describe testable business hypotheses,
            not proven interventions. Product teams should validate them
            using experiment results, user behavior, retention data, and
            additional outcome measures before treating them as successful
            business actions.
        </p>

    </div>
    """
)


# ============================================================
# MONITORING VIEW
# ============================================================

render_html(
    """
    <div class="section-shell">

        <div class="section-eyebrow">
            MONITORING VIEW
        </div>

        <div class="section-title">
            Business metric trend
        </div>

        <div class="section-description">
            Select a metric to inspect how the observed population changed
            across the reporting period. Use the trend as descriptive evidence
            for follow-up analysis rather than as an automated alert.
        </div>

    </div>
    """
)


if (
    "Date" not in filtered.columns
    or filtered["Date"].dropna().empty
):

    st.info(
        "Date information is unavailable for monitoring."
    )

else:

    daily = (
        filtered
        .dropna(
            subset=["Date"]
        )
        .groupby(
            "Date",
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
            Avg_Sedentary=(
                "SedentaryMinutes",
                "mean",
            ),
            Goal_Rate=(
                "Meets_10k_Steps",
                "mean",
            ),
        )
    )

    daily["Goal_Rate"] = (
        daily["Goal_Rate"]
        * 100
    )

    metric = st.selectbox(
        "Operational metric",
        [
            "Avg_Steps",
            "Avg_Calories",
            "Avg_Sedentary",
            "Goal_Rate",
        ],
        format_func=lambda value: {
            "Avg_Steps": "Average Steps",
            "Avg_Calories": "Average Calories",
            "Avg_Sedentary": "Average Sedentary Minutes",
            "Goal_Rate": "10K Goal Rate (%)",
        }[value],
        key="business_insights_metric",
    )

    chart_titles = {
        "Avg_Steps": "Average Steps",
        "Avg_Calories": "Average Calories",
        "Avg_Sedentary": "Average Sedentary Minutes",
        "Goal_Rate": "10K Goal Rate",
    }

    y_title = (
        "Percentage"
        if metric == "Goal_Rate"
        else chart_titles[metric]
    )

    fig = px.line(
        daily,
        x="Date",
        y=metric,
        markers=True,
        title=chart_titles[metric],
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=410,
        margin=dict(
            l=30,
            r=25,
            t=45,
            b=35,
        ),
        font=dict(
            family="Inter, Arial, sans-serif",
            color="#e8ebef",
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
    )

    fig.update_yaxes(
        title_text=y_title,
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# BUSINESS INTERPRETATION
# ============================================================

render_html(
    """
    <div class="interpretation">

        <div class="interpretation-title">
            How to use these signals
        </div>

        <p class="interpretation-copy">
            The opportunity areas identify patterns worth validating with
            additional product, user, retention, and outcome data. They are
            not causal conclusions and should not be treated as clinical
            recommendations.
        </p>

    </div>
    """
)


# ============================================================
# DATA CONTEXT
# ============================================================

render_html(
    f"""
    <div class="section-shell">

        <div class="section-eyebrow">
            DATA CONTEXT
        </div>

        <div class="section-title">
            Current reporting population
        </div>

        <div class="section-description">
            The business insights above reflect the current application
            filters and selected reporting population.
        </div>

    </div>
    """
)


d1, d2, d3 = st.columns(
    3,
    gap="medium",
)

with d1:

    render_html(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                Participants
            </div>

            <div class="kpi-value">
                {participant_count:,}
            </div>

            <div class="kpi-help">
                Unique participants in the current selection.
            </div>

        </div>
        """
    )

with d2:

    render_html(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                Participant-days
            </div>

            <div class="kpi-value">
                {record_count:,}
            </div>

            <div class="kpi-help">
                Records contributing to these observations.
            </div>

        </div>
        """
    )

with d3:

    render_html(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                Sleep coverage
            </div>

            <div class="kpi-value">
                {fmt_number(sleep_present, 1, "%")}
            </div>

            <div class="kpi-help">
                Participant-days with recorded sleep duration.
            </div>

        </div>
        """
    )


# ============================================================
# GOVERNANCE
# ============================================================

render_html(
    """
    <div class="governance">

        <strong>Reporting discipline:</strong>
        These insights are descriptive analytics derived from the selected
        dataset. Validate population coverage, missing-data treatment,
        observation period, and additional product or outcome evidence
        before using an insight to support an operational decision.

    </div>
    """
)