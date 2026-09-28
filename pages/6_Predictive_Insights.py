# PREDICTIVE INSIGHTS
#
# Complete replacement
#
# This page reads the production prediction store:
# data/processed/predictions.csv
#
# It does not generate the routine next-day participant predictions itself.
#
# Supported targets:
# - Next-Day Calorie Expenditure
# - Next-Day 10K Step Target
# - Next-Day 7-Hour Sleep Target
#
# Historical prediction evidence is read from the persisted model artifacts:
# models/predictive_models/<target>/holdout_predictions.csv
# models/predictive_models/<target>/walk_forward_predictions.csv
#
# Interactive calorie scenario planning intentionally uses the persisted
# calorie model directly because it is a hypothetical, user-controlled
# model response rather than a routine production forecast.

from __future__ import annotations

import base64
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from utils.data import load_data


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Predictive Insights | Fitness Analytics",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    ROOT_DIR
    / "data"
    / "processed"
    / "fitness_daily_master.csv"
)

PREDICTION_STORE_PATH = (
    ROOT_DIR
    / "data"
    / "processed"
    / "predictions.csv"
)

MODEL_ROOT = (
    ROOT_DIR
    / "models"
    / "predictive_models"
)

LOGO_PATH = (
    ROOT_DIR
    / "images"
    / "strava_logo.png"
)


# ============================================================
# TARGET CONFIGURATION
# ============================================================

TARGETS = {
    "calories": {
        "label": "Next-Day Calorie Expenditure",
        "short_label": "Calories",
        "icon": "🔥",
        "type": "regression",
        "question": (
            "How many calories is this participant likely "
            "to expend tomorrow?"
        ),
        "target_column": "Calories",
        "prediction_store_column": "calories_Prediction",
        "model_version_column": "Model_Version_Calories",
        "unit": "kcal",
    },
    "activity_target": {
        "label": "Next-Day 10K Step Target",
        "short_label": "10K Steps",
        "icon": "🏃",
        "type": "classification",
        "question": (
            "Is this participant likely to reach "
            "10,000 steps tomorrow?"
        ),
        "target_column": "Meets_10k_Steps",
        "prediction_store_column": "activity_target_Prediction",
        "probability_store_column": "Steps_Positive_Probability",
        "model_version_column": "Model_Version_ActivityTarget",
        "unit": "",
    },
    "sleep_target": {
        "label": "Next-Day 7-Hour Sleep Target",
        "short_label": "7h Sleep",
        "icon": "😴",
        "type": "classification",
        "question": (
            "Is this participant likely to achieve at least "
            "7 hours of sleep tomorrow?"
        ),
        "target_column": "Sleep_7h_Target",
        "prediction_store_column": "sleep_target_Prediction",
        "probability_store_column": "Sleep_Positive_Probability",
        "model_version_column": "Model_Version_SleepTarget",
        "unit": "",
    },
}


FEATURE_LABELS = {
    "Lag1_TotalSteps": "Previous-day steps",
    "Lag1_TotalDistance": "Previous-day distance",
    "Lag1_VeryActiveMinutes": "Previous-day very active minutes",
    "Lag1_FairlyActiveMinutes": "Previous-day fairly active minutes",
    "Lag1_LightlyActiveMinutes": "Previous-day lightly active minutes",
    "Lag1_SedentaryMinutes": "Previous-day sedentary minutes",
    "Lag1_Total_Active_Minutes": "Previous-day active minutes",
    "Lag1_Active_Minutes_Pct": "Previous-day active-minute %",
    "Lag1_Very_Active_Pct": "Previous-day very-active %",
    "Lag1_METs_Avg": "Previous-day average METs",
    "Lag1_METs_Max": "Previous-day maximum METs",
    "Lag1_Hourly_Avg_Intensity": "Previous-day hourly intensity",
    "Lag1_Hourly_Steps_Avg": "Previous-day hourly steps",
    "Lag1_Minute_Intensity_Avg": "Previous-day minute intensity",
    "Lag1_Minute_Active_Step_Minutes": "Previous-day active step minutes",
    "Lag1_Sleep_Minutes": "Previous-day sleep minutes",
    "Lag1_Time_In_Bed_Minutes": "Previous-day time in bed",
    "Lag1_Sleep_Efficiency_Pct": "Previous-day sleep efficiency",
    "Lag1_Calories": "Previous-day calories",
    "Target_Day_Of_Week_Num": "Target day of week",
    "Target_Is_Weekend": "Target weekend flag",
}


# ============================================================
# HELPERS
# ============================================================

def render_html(html: str) -> None:
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(
            html,
            unsafe_allow_html=True,
        )


def fmt_number(value, decimals: int = 0) -> str:
    if value is None:
        return "—"

    try:
        if pd.isna(value):
            return "—"
    except Exception:
        pass

    return f"{float(value):,.{decimals}f}"


def fmt_percent(value, decimals: int = 1) -> str:
    if value is None:
        return "—"

    try:
        if pd.isna(value):
            return "—"
    except Exception:
        pass

    return f"{float(value) * 100:.{decimals}f}%"


def feature_label(feature: str) -> str:
    return FEATURE_LABELS.get(
        feature,
        feature.replace("_", " "),
    )


def model_status(metadata: dict) -> str:
    return str(
        metadata.get(
            "approval_status",
            "shadow",
        )
    ).upper()


def selected_metrics(metadata: dict) -> dict:
    return (
        metadata.get("selected_holdout_metrics")
        or metadata.get("selected_metrics")
        or {}
    )


def metric_value(
    metrics: dict,
    *names: str,
):
    for name in names:
        if name in metrics and metrics[name] is not None:
            return metrics[name]
    return None


def section_header(
    kicker: str,
    title: str,
    description: str,
) -> None:
    render_html(
        f"""
        <div class="section-header">
            <div class="section-kicker">{kicker}</div>
            <div class="section-title">{title}</div>
            <div class="section-description">{description}</div>
        </div>
        """
    )


def metric_card(
    title: str,
    value: str,
    helper: str,
    accent: bool = False,
) -> None:
    value_class = (
        "metric-value accent"
        if accent
        else "metric-value"
    )

    render_html(
        f"""
        <div class="metric-card">
            <div class="metric-label">{title}</div>
            <div class="{value_class}">{value}</div>
            <div class="metric-help">{helper}</div>
        </div>
        """
    )


def insight_box(
    title: str,
    copy: str,
    meta: str = "",
    tone: str = "normal",
) -> None:
    tone_class = (
        f" insight-{tone}"
        if tone
        else ""
    )

    meta_html = (
        f'<div class="insight-meta">{meta}</div>'
        if meta
        else ""
    )

    render_html(
        f"""
        <div class="insight-box{tone_class}">
            <div class="insight-title">{title}</div>
            <div class="insight-copy">{copy}</div>
            {meta_html}
        </div>
        """
    )


def chart_layout(
    fig,
    y_title: str | None = None,
    height: int = 400,
):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(
            l=20,
            r=20,
            t=28,
            b=20,
        ),
        height=height,
        legend_title_text="",
        font=dict(
            family="Inter, Arial, sans-serif",
            color="#e8ebef",
        ),
        hovermode="x unified",
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

    return fig


def status_class(status: str) -> str:
    value = str(status).lower()

    if (
        "review" in value
        or "alert" in value
        or "drift" in value
        or "error" in value
    ):
        return "status-alert"

    if (
        "watch" in value
        or "monitor" in value
    ):
        return "status-watch"

    return "status-good"


def load_json(path: Path) -> dict:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def format_prediction_timestamp(value) -> str:
    """
    Display stored UTC timestamps in India Standard Time with the
    timezone explicitly labelled.
    """
    if value is None:
        return "—"

    try:
        timestamp = pd.Timestamp(value)

        if pd.isna(timestamp):
            return "—"

        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")

        return timestamp.tz_convert(
            "Asia/Kolkata"
        ).strftime(
            "%d %b %Y %H:%M IST"
        )

    except Exception:
        return str(value)


def calculate_backtest_metrics(
    backtest: pd.DataFrame,
    target_type: str,
) -> dict:
    """
    Compute walk-forward metrics directly from the persisted
    predictions when metadata does not contain backtest_metrics.
    """
    required = {
        "Actual",
        "Prediction",
    }

    if backtest.empty or not required.issubset(
        backtest.columns
    ):
        return {}

    work = backtest[
        [
            "Actual",
            "Prediction",
        ]
    ].copy()

    work["Actual"] = pd.to_numeric(
        work["Actual"],
        errors="coerce",
    )

    work["Prediction"] = pd.to_numeric(
        work["Prediction"],
        errors="coerce",
    )

    work = work.dropna(
        subset=[
            "Actual",
            "Prediction",
        ]
    )

    if work.empty:
        return {}

    if target_type == "regression":
        from sklearn.metrics import (
            mean_absolute_error,
            mean_squared_error,
            r2_score,
        )

        return {
            "MAE": float(
                mean_absolute_error(
                    work["Actual"],
                    work["Prediction"],
                )
            ),
            "RMSE": float(
                np.sqrt(
                    mean_squared_error(
                        work["Actual"],
                        work["Prediction"],
                    )
                )
            ),
            "R2": float(
                r2_score(
                    work["Actual"],
                    work["Prediction"],
                )
            ),
        }

    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    actual = (
        work["Actual"]
        .round()
        .astype(int)
    )

    predicted = (
        work["Prediction"]
        .round()
        .astype(int)
    )

    metrics = {
        "Accuracy": float(
            accuracy_score(
                actual,
                predicted,
            )
        ),
        "Precision": float(
            precision_score(
                actual,
                predicted,
                zero_division=0,
            )
        ),
        "Recall": float(
            recall_score(
                actual,
                predicted,
                zero_division=0,
            )
        ),
        "F1": float(
            f1_score(
                actual,
                predicted,
                zero_division=0,
            )
        ),
    }

    if actual.nunique() >= 2:
        probabilities = None

        if (
            "Positive_Probability"
            in backtest.columns
        ):
            probabilities = pd.to_numeric(
                backtest[
                    "Positive_Probability"
                ],
                errors="coerce",
            )

            aligned = pd.concat(
                [
                    actual.rename("Actual"),
                    probabilities.rename(
                        "Probability"
                    ),
                ],
                axis=1,
            ).dropna()

            if (
                not aligned.empty
                and aligned["Actual"].nunique() >= 2
            ):
                try:
                    metrics["ROC_AUC"] = float(
                        roc_auc_score(
                            aligned["Actual"],
                            aligned["Probability"],
                        )
                    )
                except Exception:
                    pass

    return metrics


def load_artifacts() -> dict[str, dict]:
    artifacts = {}

    for key, config in TARGETS.items():
        model_dir = MODEL_ROOT / key

        model_path = model_dir / "model.joblib"
        metadata_path = model_dir / "metadata.json"
        holdout_path = model_dir / "holdout_predictions.csv"
        backtest_path = model_dir / "walk_forward_predictions.csv"

        artifact = {
            "available": False,
            "model": None,
            "metadata": {},
            "holdout": pd.DataFrame(),
            "backtest": pd.DataFrame(),
            "error": None,
        }

        if not model_path.exists() or not metadata_path.exists():
            artifacts[key] = artifact
            continue

        try:
            artifact["model"] = joblib.load(
                model_path
            )

            artifact["metadata"] = load_json(
                metadata_path
            )

            if holdout_path.exists():
                artifact["holdout"] = pd.read_csv(
                    holdout_path
                )

            if backtest_path.exists():
                artifact["backtest"] = pd.read_csv(
                    backtest_path
                )

            for frame_name in ["holdout", "backtest"]:
                frame = artifact[frame_name]

                if not frame.empty:
                    for column in [
                        "Feature_Date",
                        "Target_Date",
                    ]:
                        if column in frame.columns:
                            frame[column] = pd.to_datetime(
                                frame[column],
                                errors="coerce",
                            )

                    if "Id" in frame.columns:
                        frame["Id"] = frame["Id"].astype(str)

                    artifact[frame_name] = frame

            artifact["available"] = True

        except Exception as exc:
            artifact["error"] = str(exc)

        artifacts[key] = artifact

    return artifacts


def load_prediction_store() -> pd.DataFrame:
    if not PREDICTION_STORE_PATH.exists():
        return pd.DataFrame()

    prediction_store = pd.read_csv(
        PREDICTION_STORE_PATH
    )

    if "Id" in prediction_store.columns:
        prediction_store["Id"] = (
            prediction_store["Id"].astype(str)
        )

    for column in [
        "Feature_Date",
        "Target_Date",
        "Prediction_Timestamp",
    ]:
        if column in prediction_store.columns:
            prediction_store[column] = pd.to_datetime(
                prediction_store[column],
                errors="coerce",
            )

    return prediction_store


def latest_usable_row(
    participant_df: pd.DataFrame,
) -> pd.Series | None:
    if participant_df.empty:
        return None

    ordered = participant_df.sort_values(
        "Date"
    ).copy()

    signal_columns = [
        "TotalSteps",
        "Calories",
        "Total_Active_Minutes",
        "Sleep_Minutes",
    ]

    for _, row in ordered.iloc[::-1].iterrows():
        values = []

        for column in signal_columns:
            if column not in row.index:
                continue

            value = pd.to_numeric(
                pd.Series([row[column]]),
                errors="coerce",
            ).iloc[0]

            if pd.notna(value):
                values.append(float(value))

        if not values:
            continue

        if any(value > 0 for value in values):
            return row

    return ordered.iloc[-1]


def model_version_for_store(
    prediction_row: pd.Series,
    key: str,
) -> str:
    column = TARGETS[key].get(
        "model_version_column"
    )

    if not column:
        return "—"

    value = prediction_row.get(
        column
    )

    if value is None or pd.isna(value):
        return "—"

    return str(value)


def prediction_store_value(
    prediction_row: pd.Series,
    key: str,
):
    column = TARGETS[key][
        "prediction_store_column"
    ]

    if column not in prediction_row.index:
        return np.nan

    return pd.to_numeric(
        pd.Series(
            [prediction_row[column]]
        ),
        errors="coerce",
    ).iloc[0]


def prediction_store_probability(
    prediction_row: pd.Series,
    key: str,
):
    column = TARGETS[key].get(
        "probability_store_column"
    )

    if not column or column not in prediction_row.index:
        return None

    value = pd.to_numeric(
        pd.Series(
            [prediction_row[column]]
        ),
        errors="coerce",
    ).iloc[0]

    return (
        None
        if pd.isna(value)
        else float(value)
    )


def get_target_holdout(
    artifacts: dict[str, dict],
    key: str,
) -> pd.DataFrame:
    artifact = artifacts.get(key)

    if not artifact or not artifact["available"]:
        return pd.DataFrame()

    holdout = artifact["holdout"].copy()

    if holdout.empty:
        return holdout

    if "Id" in holdout.columns:
        holdout["Id"] = holdout["Id"].astype(str)

    if "Target_Date" in holdout.columns:
        holdout["Target_Date"] = pd.to_datetime(
            holdout["Target_Date"],
            errors="coerce",
        )

    return holdout.sort_values(
        "Target_Date"
    )


def get_target_backtest(
    artifacts: dict[str, dict],
    key: str,
) -> pd.DataFrame:
    artifact = artifacts.get(key)

    if not artifact or not artifact["available"]:
        return pd.DataFrame()

    backtest = artifact["backtest"].copy()

    if backtest.empty:
        return backtest

    if "Id" in backtest.columns:
        backtest["Id"] = backtest["Id"].astype(str)

    if "Target_Date" in backtest.columns:
        backtest["Target_Date"] = pd.to_datetime(
            backtest["Target_Date"],
            errors="coerce",
        )

    return backtest.sort_values(
        "Target_Date"
    )


def monitoring_key(
    model_version: str,
) -> str:
    text = str(model_version).lower()

    if text.startswith("calories-"):
        return "calories"

    if text.startswith("activity_target-"):
        return "activity_target"

    if text.startswith("sleep_target-"):
        return "sleep_target"

    return "unknown"


def load_monitoring_log() -> pd.DataFrame:
    path = MODEL_ROOT / "monitoring_log.csv"

    if not path.exists():
        return pd.DataFrame()

    monitoring = pd.read_csv(path)

    if monitoring.empty:
        return monitoring

    for column in [
        "timestamp_utc",
        "observation_date",
        "feature_date",
        "target_date",
    ]:
        if column in monitoring.columns:
            monitoring[column] = pd.to_datetime(
                monitoring[column],
                errors="coerce",
            )

    if "model_key" not in monitoring.columns:
        if "model_version" in monitoring.columns:
            monitoring["model_key"] = (
                monitoring["model_version"]
                .apply(monitoring_key)
            )
        else:
            monitoring["model_key"] = "unknown"

    return monitoring


# ============================================================
# GLOBAL THEME
# ============================================================

render_html(
    """
    <style>

    :root {
        --bg: #0b0d10;
        --surface: #101318;
        --surface-2: #151920;
        --border: rgba(255,255,255,0.09);
        --text: #f5f7fa;
        --muted: #9aa2ae;
        --orange: #fc5200;
        --orange-light: #ff7840;
        --green: #2fd48a;
        --amber: #f5b94c;
        --red: #ff5d66;
        --blue: #62b6f7;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 88% 3%,
                rgba(252,82,0,0.06),
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

    .block-container {
        max-width: none !important;
        width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-top: 70px !important;
        padding-left: 22px !important;
        padding-right: 24px !important;
        padding-bottom: 4rem !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    p, label {
        color: rgba(255,255,255,0.82);
    }

    /* ========================================================
       SIDEBAR
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
        border-right:
            1px solid
            #292d34 !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 320px !important;
        background: transparent !important;
        padding: 0 !important;
    }

    [data-testid="stSidebarContent"] {
        padding: 0 16px 28px 16px !important;
    }

    [data-testid="stSidebarNav"] {
        padding-top: 0.35rem !important;
    }

    [data-testid="stSidebarNav"] a {
        border-radius: 7px !important;
        margin: 2px 8px !important;
        padding: 0 10px !important;
        height: 40px !important;
        min-height: 40px !important;
        display: flex !important;
        align-items: center !important;
        color: rgba(255,255,255,0.70) !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        color: #ffffff !important;
        background: rgba(255,107,26,0.08) !important;
        border:
            1px solid
            rgba(255,107,26,0.20)
            !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        color: #ffffff !important;
        background:
            linear-gradient(
                90deg,
                rgba(255,107,26,0.20),
                rgba(255,107,26,0.07)
            ) !important;
        border:
            1px solid
            rgba(255,107,26,0.42)
            !important;
        box-shadow:
            inset 3px 0 0 #ff6b1a,
            0 4px 12px rgba(0,0,0,0.18)
            !important;
    }

    .sidebar-divider {
        height: 1px;
        margin: 14px 0 17px 0;
        background: rgba(255,255,255,0.12);
    }

    .sidebar-label {
        color: #ff6b1a;
        font-size: 0.54rem;
        font-weight: 850;
        letter-spacing: 0.14em;
        margin: 15px 2px 7px 2px;
        text-transform: uppercase;
    }

    .sidebar-card {
        padding: 11px 12px;
        border-radius: 9px;
        background: rgba(14,16,22,0.82);
        border:
            1px solid
            rgba(255,255,255,0.10);
        margin-bottom: 12px;
    }

    .sidebar-title {
        color: rgba(255,255,255,0.92);
        font-size: 0.64rem;
        font-weight: 800;
        margin: 4px 0;
    }

    .sidebar-copy {
        color: rgba(255,255,255,0.47);
        font-size: 0.54rem;
        line-height: 1.45;
        margin: 3px 0 7px 0;
    }

    /* ========================================================
       HERO
       ======================================================== */

    .hero {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        border:
            1px solid
            rgba(255,255,255,0.14);
        border-radius: 20px;
        padding: 28px 30px;
        margin-bottom: 22px;
        background:
            linear-gradient(
                110deg,
                rgba(21,29,40,0.78),
                rgba(14,18,26,0.64) 48%,
                rgba(39,20,13,0.62) 100%
            );
        box-shadow:
            0 18px 48px rgba(0,0,0,0.34),
            inset 0 1px 0 rgba(255,255,255,0.07);
        backdrop-filter:
            blur(24px)
            saturate(145%);
    }

    .hero::before {
        content: "";
        position: absolute;
        inset: -80% -5%;
        background:
            radial-gradient(
                ellipse at 12% 50%,
                rgba(38,58,83,0.85),
                transparent 62%
            ),
            radial-gradient(
                ellipse at 83% 43%,
                rgba(255,72,8,0.72),
                transparent 63%
            );
        filter: blur(42px);
        opacity: 0.85;
        pointer-events: none;
    }

    .hero > * {
        position: relative;
        z-index: 3;
    }

    .eyebrow {
        color: #ff6b1a;
        font-size: 0.56rem;
        font-weight: 900;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .hero-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 9px;
    }

    .hero-logo {
        width: 42px;
        height: 42px;
        min-width: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: transparent;
        border: none;
        overflow: visible;
    }

    .hero-logo img {
        width: 42px;
        height: 42px;
        object-fit: contain;
        display: block;
    }

    .hero-title {
        margin: 0;
        color: #ffffff;
        font-size: 2.25rem;
        font-weight: 900;
        line-height: 1.05;
    }

    .hero-title-orange {
        color: #ff6b1a;
    }

    .hero-copy {
        color: rgba(255,255,255,0.62);
        font-size: 0.70rem;
        line-height: 1.55;
        max-width: 1120px;
    }

    .shadow-pill {
        display: inline-block;
        margin-top: 15px;
        padding: 5px 10px;
        border-radius: 999px;
        background: rgba(245,185,76,0.10);
        color: #ffd58a;
        border:
            1px solid
            rgba(245,185,76,0.20);
        font-size: 0.46rem;
        font-weight: 900;
        letter-spacing: 0.08em;
    }

    /* ========================================================
       SECTION
       ======================================================== */

    .section-header {
        border:
            1px solid
            rgba(255,255,255,0.09);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 14px 0 10px 0;
        background:
            rgba(13,15,20,0.68);
    }

    .section-kicker {
        color: #ff6b1a;
        font-size: 0.50rem;
        font-weight: 900;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    .section-title {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 850;
        margin-top: 3px;
    }

    .section-description {
        color: rgba(255,255,255,0.44);
        font-size: 0.56rem;
        line-height: 1.45;
        margin-top: 4px;
    }

    /* ========================================================
       CARDS
       ======================================================== */

    .metric-card,
    .info-card,
    .monitor-card {
        min-height: 96px;
        padding: 13px 14px;
        border:
            1px solid
            rgba(255,255,255,0.09);
        border-radius: 11px;
        background:
            rgba(12,14,19,0.78);
        box-shadow:
            inset 0 1px 0
            rgba(255,255,255,0.025);
    }

    .info-card {
        min-height: 138px;
    }

    .monitor-card {
        min-height: 126px;
    }

    .metric-label,
    .info-kicker,
    .monitor-kicker {
        color: rgba(255,255,255,0.48);
        font-size: 0.49rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .info-kicker {
        color: #ff6b1a;
        font-weight: 900;
        letter-spacing: 0.10em;
    }

    .metric-value,
    .info-value,
    .monitor-value {
        color: #f4f6f8;
        font-size: 1.35rem;
        font-weight: 850;
        line-height: 1.08;
    }

    .metric-value.accent {
        color: #ff7840;
    }

    .info-title,
    .monitor-title {
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 850;
        margin-bottom: 7px;
    }

    .info-copy,
    .monitor-copy {
        color: rgba(255,255,255,0.48);
        font-size: 0.54rem;
        line-height: 1.48;
    }

    .performance-card {
        min-height: 175px;
        padding: 14px;
        border:
            1px solid
            rgba(255,255,255,0.08);
        border-radius: 11px;
        background:
            rgba(14,16,22,0.78);
    }

    .performance-title {
        color: #ffffff;
        font-size: 0.74rem;
        font-weight: 850;
        line-height: 1.25;
        margin-bottom: 4px;
    }

    .performance-meta {
        color: rgba(255,255,255,0.38);
        font-size: 0.50rem;
        line-height: 1.4;
        margin-bottom: 12px;
    }

    .performance-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 7px;
        margin-top: 8px;
    }

    .performance-grid.classification {
        grid-template-columns: repeat(5, minmax(0, 1fr));
    }

    .metric-mini-label {
        color: rgba(255,255,255,0.38);
        font-size: 0.43rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 3px;
    }

    .metric-mini-value {
        color: #f5f7fa;
        font-size: 0.82rem;
        font-weight: 850;
        line-height: 1.1;
    }

    .performance-foot {
        color: rgba(255,255,255,0.30);
        font-size: 0.47rem;
        line-height: 1.35;
        margin-top: 13px;
    }

    .metric-help {
        color: rgba(255,255,255,0.31);
        font-size: 0.48rem;
        line-height: 1.3;
        margin-top: 5px;
    }

    .status-pill {
        display: inline-block;
        margin-top: 9px;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 0.46rem;
        font-weight: 850;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .status-good {
        color: #8ff1c4;
        background: rgba(47,212,138,0.10);
        border:
            1px solid
            rgba(47,212,138,0.24);
    }

    .status-watch {
        color: #ffd58a;
        background: rgba(245,185,76,0.10);
        border:
            1px solid
            rgba(245,185,76,0.24);
    }

    .status-alert {
        color: #ff9ca2;
        background: rgba(255,93,102,0.10);
        border:
            1px solid
            rgba(255,93,102,0.24);
    }

    .insight-box {
        border:
            1px solid
            rgba(255,255,255,0.08);
        border-left:
            3px solid
            #ff6b1a;
        border-radius: 9px;
        background:
            rgba(16,18,24,0.80);
        padding: 11px 14px;
        margin: 5px 0 18px 0;
    }

    .insight-watch {
        border-left-color: #f5b94c;
    }

    .insight-alert {
        border-left-color: #ff5d66;
    }

    .insight-good {
        border-left-color: #2fd48a;
    }

    .insight-title {
        color: #ffffff;
        font-size: 0.61rem;
        font-weight: 850;
        margin-bottom: 4px;
    }

    .insight-copy {
        color: rgba(255,255,255,0.50);
        font-size: 0.55rem;
        line-height: 1.48;
    }

    .insight-meta {
        color: rgba(255,107,26,0.90);
        font-size: 0.47rem;
        font-weight: 850;
        letter-spacing: 0.04em;
        margin-top: 6px;
    }

    /* ========================================================
       SCENARIO
       ======================================================== */

    .scenario-result {
        min-height: 230px;
        padding: 20px;
        border:
            1px solid
            rgba(255,107,26,0.40);
        border-radius: 14px;
        background:
            linear-gradient(
                145deg,
                rgba(45,24,15,0.72),
                rgba(18,15,14,0.78)
            );
    }

    .scenario-kicker {
        color: #ff6b1a;
        font-size: 0.50rem;
        font-weight: 900;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 7px;
    }

    .scenario-value {
        color: #ffffff;
        font-size: 2.05rem;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 8px;
    }

    .scenario-delta {
        color: #ff7840;
        font-size: 0.72rem;
        font-weight: 850;
        margin-bottom: 11px;
    }

    .scenario-copy {
        color: rgba(255,255,255,0.52);
        font-size: 0.56rem;
        line-height: 1.5;
    }

    /* ========================================================
       STREAMLIT CONTROLS
       ======================================================== */

    div[data-baseweb="select"] > div {
        background: #24252f !important;
        border:
            1px solid
            rgba(255,255,255,0.06) !important;
    }

    [data-testid="stExpander"] {
        background: rgba(14,16,22,0.62);
        border:
            1px solid
            rgba(255,255,255,0.08);
        border-radius: 10px;
    }

    [data-testid="stDataFrame"] {
        border-radius: 10px;
    }

    /* ========================================================
       FOOTER
       ======================================================== */

    .footer-note {
        margin-top: 18px;
        padding-top: 12px;
        border-top:
            1px solid
            rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.30);
        font-size: 0.49rem;
        line-height: 1.55;
    }

    </style>
    """
)


# ============================================================
# LOAD LOGO
# ============================================================

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


# ============================================================
# LOAD CANONICAL DATA
# ============================================================

try:
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
    else:
        df = load_data()

except Exception as exc:
    st.error(
        f"Unable to load the canonical fitness dataset: {exc}"
    )
    st.stop()


if df.empty:
    st.error(
        "The canonical fitness dataset is empty."
    )
    st.stop()


if "Date" not in df.columns or "Id" not in df.columns:
    st.error(
        "The canonical dataset must contain both Date and Id columns."
    )
    st.stop()


df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce",
)

df = df.dropna(
    subset=["Date", "Id"]
).copy()

df["Id"] = df["Id"].astype(str)

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
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
            .fillna(0)
            .sum(axis=1)
        )
    else:
        df["Total_Active_Minutes"] = np.nan


# ============================================================
# LOAD MODELS + PREDICTION STORE + MONITORING
# ============================================================

artifacts = load_artifacts()

prediction_store = load_prediction_store()

monitoring_log = load_monitoring_log()

available_model_count = sum(
    artifact["available"]
    for artifact in artifacts.values()
)


# ============================================================
# PARTICIPANTS
# ============================================================

participants = (
    df["Id"]
    .dropna()
    .drop_duplicates()
    .sort_values()
    .tolist()
)

if not participants:
    st.error(
        "No participants are available."
    )
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    render_html(
        """
        <div class="sidebar-divider"></div>

        <div class="sidebar-label">
            PREDICTIVE INSIGHTS
        </div>

        <div class="sidebar-card">

            <div class="sidebar-title">
                Business use case
            </div>

            <div class="sidebar-copy">
                Participant-level next-day predictive analytics
                using observed fitness behavior.
            </div>

            <div class="sidebar-title">
                Decision supported
            </div>

            <div class="sidebar-copy">
                Compare expected outcomes, historical predictive
                performance, errors, and model-health signals.
            </div>

        </div>
        """
    )

    st.markdown(
        "### Prediction Controls"
    )

    selected_participant = st.selectbox(
        "Participant",
        participants,
        key="predictive_participant",
    )

    selected_participant_df = (
        df[
            df["Id"].astype(str)
            == str(selected_participant)
        ]
        .sort_values("Date")
        .copy()
    )

    selected_latest_row = latest_usable_row(
        selected_participant_df
    )

    if selected_latest_row is None:
        st.error(
            "No usable observation is available for the selected participant."
        )
        st.stop()

    selected_latest_date = pd.Timestamp(
        selected_latest_row["Date"]
    )

    st.caption(
        f"Latest observed day: "
        f"{selected_latest_date:%d %b %Y}"
    )

    st.caption(
        f"Participants: {df['Id'].nunique():,}"
    )

    st.caption(
        f"Source rows: {len(df):,}"
    )

    st.caption(
        f"Models available: "
        f"{available_model_count}/3"
    )

    if prediction_store.empty:
        st.caption(
            "Prediction store: NOT FOUND"
        )
    else:
        latest_prediction_timestamp = (
            prediction_store["Prediction_Timestamp"].max()
            if "Prediction_Timestamp" in prediction_store.columns
            else pd.NaT
        )

        if pd.notna(latest_prediction_timestamp):
            st.caption(
                f"Prediction store updated: "
                f"{format_prediction_timestamp(latest_prediction_timestamp)}"
            )


# ============================================================
# HERO
# ============================================================

render_html(
    f"""
    <div class="hero">

        <div class="eyebrow">
            HOME &nbsp;•&nbsp; PREDICTIVE INSIGHTS
        </div>

        <div class="hero-row">

            <div class="hero-logo">
                {logo_html}
            </div>

            <h1 class="hero-title">
                <span class="hero-title-orange">
                    Predictive
                </span>
                <span> Insights</span>
            </h1>

        </div>

        <div class="hero-copy">
            Participant-level next-day predictions across
            calorie expenditure, activity achievement, and
            sleep attainment. Routine forecasts are produced
            by the prediction pipeline and read here from the
            persisted prediction store.
        </div>

        <div class="shadow-pill">
            SHADOW MODE — ANALYTICAL FORECASTS
        </div>

    </div>
    """
)


# ============================================================
# MODEL STATUS
# ============================================================

section_header(
    "00 · MODEL STATUS",
    "Predictive models currently available",
    (
        "The page reads persisted model artifacts and the "
        "production prediction store. Loading this page does "
        "not retrain models or regenerate routine forecasts."
    ),
)


status_cols = st.columns(3)

for column, (key, config) in zip(
    status_cols,
    TARGETS.items(),
):
    artifact = artifacts[key]

    with column:
        if artifact["available"]:
            metadata = artifact["metadata"]
            algorithm = metadata.get(
                "algorithm",
                "Unknown",
            )
            version = metadata.get(
                "model_version",
                "Unknown",
            )

            render_html(
                f"""
                <div class="info-card">

                    <div class="info-kicker">
                        {config["icon"]} {config["short_label"]}
                    </div>

                    <div class="info-title">
                        {config["label"]}
                    </div>

                    <div class="info-value">
                        {algorithm}
                    </div>

                    <div class="info-copy">
                        Artifact loaded successfully.<br>
                        Version: {version}
                    </div>

                    <span class="status-pill status-good">
                        AVAILABLE · {model_status(metadata)}
                    </span>

                </div>
                """
            )

        else:
            error_text = artifact.get(
                "error"
            ) or "No saved artifact is available."

            render_html(
                f"""
                <div class="info-card">

                    <div class="info-kicker">
                        {config["icon"]} {config["short_label"]}
                    </div>

                    <div class="info-title">
                        {config["label"]}
                    </div>

                    <div class="info-value">
                        Unavailable
                    </div>

                    <div class="info-copy">
                        {error_text}
                    </div>

                    <span class="status-pill status-alert">
                        UNAVAILABLE
                    </span>

                </div>
                """
            )


# ============================================================
# ROUTINE NEXT-DAY OUTLOOK
# ============================================================

section_header(
    "01 · TOMORROW'S OUTLOOK",
    "What does the production prediction store estimate next?",
    (
        "These routine next-day values come from "
        "data/processed/predictions.csv, generated by "
        "scripts/run_predictive_predictions.py."
    ),
)


participant_prediction = pd.DataFrame()

if not prediction_store.empty and "Id" in prediction_store.columns:
    participant_prediction = (
        prediction_store[
            prediction_store["Id"].astype(str)
            == str(selected_participant)
        ]
        .sort_values("Target_Date")
        .tail(1)
    )


if participant_prediction.empty:

    insight_box(
        "Prediction record unavailable",
        (
            "No stored prediction record was found for the selected "
            "participant. Run the prediction pipeline before using "
            "the routine next-day outlook."
        ),
        "RUN: python scripts/run_predictive_predictions.py",
        tone="watch",
    )

else:

    prediction_row = participant_prediction.iloc[0]

    forecast_target_date = pd.Timestamp(
        prediction_row["Target_Date"]
    )

    outlook_cols = st.columns(3)

    for column, (key, config) in zip(
        outlook_cols,
        TARGETS.items(),
    ):
        with column:

            stored_value = prediction_store_value(
                prediction_row,
                key,
            )

            version = model_version_for_store(
                prediction_row,
                key,
            )

            if pd.isna(stored_value):
                render_html(
                    f"""
                    <div class="info-card">

                        <div class="info-kicker">
                            {config["icon"]} {config["short_label"]}
                        </div>

                        <div class="info-title">
                            {config["label"]}
                        </div>

                        <div class="info-value">
                            —
                        </div>

                        <div class="info-copy">
                            Stored forecast value is unavailable.
                        </div>

                        <span class="status-pill status-alert">
                            REVIEW
                        </span>

                    </div>
                    """
                )
                continue

            if config["type"] == "regression":

                prediction_text = (
                    f"{float(stored_value):,.0f} kcal"
                )

                probability_text = (
                    "Continuous model prediction"
                )

            else:

                predicted_class = int(
                    round(
                        float(stored_value)
                    )
                )

                probability = prediction_store_probability(
                    prediction_row,
                    key,
                )

                prediction_text = (
                    "Likely to achieve"
                    if predicted_class == 1
                    else "Not likely to achieve"
                )

                if probability is not None:
                    probability_text = (
                        f"Positive probability: "
                        f"{probability:.1%}"
                    )
                else:
                    probability_text = (
                        "Probability unavailable"
                    )

            render_html(
                f"""
                <div class="info-card">

                    <div class="info-kicker">
                        {config["icon"]} {config["short_label"]}
                    </div>

                    <div class="info-title">
                        {config["question"]}
                    </div>

                    <div class="info-value">
                        {prediction_text}
                    </div>

                    <div class="info-copy">
                        {probability_text}<br>
                        Model: {version}
                    </div>

                    <span class="status-pill status-good">
                        STORED FORECAST
                    </span>

                </div>
                """
            )

    st.caption(
        f"Forecast target date: "
        f"{forecast_target_date:%d %b %Y} · "
        f"Feature date: "
        f"{pd.Timestamp(prediction_row['Feature_Date']):%d %b %Y}"
    )


# ============================================================
# CURRENT PARTICIPANT PROFILE
# ============================================================

section_header(
    "02 · CURRENT PROFILE",
    "What information is represented by the latest observed day?",
    (
        "These values describe the selected participant's latest "
        "usable observation. They provide context for the stored "
        "next-day forecast and are not themselves predictions."
    ),
)


profile_values = [
    (
        "Steps",
        selected_latest_row.get(
            "TotalSteps",
            np.nan,
        ),
        "steps",
        0,
    ),
    (
        "Distance",
        selected_latest_row.get(
            "TotalDistance",
            np.nan,
        ),
        "distance",
        2,
    ),
    (
        "Active minutes",
        selected_latest_row.get(
            "Total_Active_Minutes",
            np.nan,
        ),
        "minutes",
        0,
    ),
    (
        "Sleep",
        (
            pd.to_numeric(
                pd.Series(
                    [selected_latest_row.get("Sleep_Minutes")]
                ),
                errors="coerce",
            ).iloc[0] / 60
            if pd.notna(
                pd.to_numeric(
                    pd.Series(
                        [selected_latest_row.get("Sleep_Minutes")]
                    ),
                    errors="coerce",
                ).iloc[0]
            )
            else np.nan
        ),
        "hours",
        1,
    ),
    (
        "Calories",
        selected_latest_row.get(
            "Calories",
            np.nan,
        ),
        "kcal",
        0,
    ),
]


profile_cols = st.columns(5)

for column, (
    title,
    value,
    unit,
    decimals,
) in zip(
    profile_cols,
    profile_values,
):
    with column:
        metric_card(
            title,
            fmt_number(
                value,
                decimals,
            ),
            f"Latest observed · {unit}",
        )


# ============================================================
# MODEL PERFORMANCE
# ============================================================

section_header(
    "03 · MODEL PERFORMANCE",
    "How did the persisted models perform on unseen data?",
    (
        "Each target uses metrics appropriate to its problem type. "
        "Regression is reported with MAE, RMSE and R². "
        "Classification is reported with Accuracy, Precision, "
        "Recall, F1 and ROC-AUC."
    ),
)


performance_cols = st.columns(3)

for column, (key, config) in zip(
    performance_cols,
    TARGETS.items(),
):
    artifact = artifacts[key]

    with column:

        if not artifact["available"]:

            render_html(
                f"""
                <div class="info-card">
                    <div class="info-kicker">
                        {config["icon"]} {config["short_label"]}
                    </div>

                    <div class="info-title">
                        {config["label"]}
                    </div>

                    <div class="info-value">
                        Unavailable
                    </div>

                    <div class="info-copy">
                        No trained artifact is available.
                    </div>

                    <span class="status-pill status-alert">
                        UNAVAILABLE
                    </span>
                </div>
                """
            )

            continue

        metadata = artifact["metadata"]
        metrics = selected_metrics(metadata)

        algorithm = metadata.get(
            "algorithm",
            "Unknown",
        )

        approval = model_status(
            metadata
        )

        if config["type"] == "regression":

            mae = metric_value(
                metrics,
                "MAE",
                "mae",
            )

            rmse = metric_value(
                metrics,
                "RMSE",
                "rmse",
            )

            r2 = metric_value(
                metrics,
                "R2",
                "R²",
                "r2",
                "r_squared",
            )

            metric_html = f"""
                <div class="performance-grid">
                    <div>
                        <div class="metric-mini-label">MAE</div>
                        <div class="metric-mini-value">
                            {fmt_number(mae, 2)}
                        </div>
                    </div>

                    <div>
                        <div class="metric-mini-label">RMSE</div>
                        <div class="metric-mini-value">
                            {fmt_number(rmse, 2)}
                        </div>
                    </div>

                    <div>
                        <div class="metric-mini-label">R²</div>
                        <div class="metric-mini-value">
                            {fmt_number(r2, 3)}
                        </div>
                    </div>
                </div>
            """

        else:

            accuracy = metric_value(
                metrics,
                "Accuracy",
                "accuracy",
            )

            precision = metric_value(
                metrics,
                "Precision",
                "precision",
            )

            recall = metric_value(
                metrics,
                "Recall",
                "recall",
            )

            f1 = metric_value(
                metrics,
                "F1",
                "f1",
            )

            roc_auc = metric_value(
                metrics,
                "ROC_AUC",
                "ROC-AUC",
                "roc_auc",
                "ROC AUC",
            )

            metric_html = f"""
                <div class="performance-grid classification">
                    <div>
                        <div class="metric-mini-label">Accuracy</div>
                        <div class="metric-mini-value">
                            {fmt_percent(accuracy)}
                        </div>
                    </div>

                    <div>
                        <div class="metric-mini-label">Precision</div>
                        <div class="metric-mini-value">
                            {fmt_percent(precision)}
                        </div>
                    </div>

                    <div>
                        <div class="metric-mini-label">Recall</div>
                        <div class="metric-mini-value">
                            {fmt_percent(recall)}
                        </div>
                    </div>

                    <div>
                        <div class="metric-mini-label">F1</div>
                        <div class="metric-mini-value">
                            {fmt_number(f1, 3)}
                        </div>
                    </div>

                    <div>
                        <div class="metric-mini-label">ROC-AUC</div>
                        <div class="metric-mini-value">
                            {fmt_number(roc_auc, 3)}
                        </div>
                    </div>
                </div>
            """

        render_html(
            f"""
            <div class="performance-card">

                <div class="info-kicker">
                    {config["icon"]} {config["short_label"]}
                </div>

                <div class="performance-title">
                    {config["label"]}
                </div>

                <div class="performance-meta">
                    {algorithm}
                    ·
                    {approval}
                </div>

                {metric_html}

                <div class="performance-foot">
                    Training:
                    {metadata.get("training_rows", "—"):,}
                    rows
                    ·
                    Holdout:
                    {metadata.get("holdout_rows", "—"):,}
                    rows
                </div>

            </div>
            """
        )


# ============================================================
# HISTORICAL PREDICTION TRENDS
# ============================================================

# ============================================================
# HISTORICAL PREDICTION TRENDS
# ============================================================

section_header(
    "04 · PREDICTION TRENDS",
    "How did the model prediction track the actual outcome over previous days?",
    (
        "The default view is Calories Trend. Select Steps Trend or "
        "Sleep Trend to replace the current chart. Each view uses "
        "participant-specific chronological holdout predictions. "
        "For classification targets, actual and predicted classes are "
        "shown as discrete markers while positive probability is shown "
        "as the continuous prediction trend."
    ),
)


trend_options = [
    "Calories Trend",
    "Steps Trend",
    "Sleep Trend",
]


trend_label = st.radio(
    "Historical trend",
    trend_options,
    horizontal=True,
    index=0,
    key="predictive_trend_selector",
)


trend_key = {
    "Calories Trend": "calories",
    "Steps Trend": "activity_target",
    "Sleep Trend": "sleep_target",
}[trend_label]


trend_config = TARGETS[trend_key]

trend_holdout = get_target_holdout(
    artifacts,
    trend_key,
)

if (
    not trend_holdout.empty
    and "Id" in trend_holdout.columns
):
    participant_trend = trend_holdout[
        trend_holdout["Id"].astype(str)
        == str(selected_participant)
    ].copy()
else:
    participant_trend = pd.DataFrame()


if participant_trend.empty:

    insight_box(
        "Historical trend unavailable",
        (
            f"No saved holdout predictions are available for "
            f"participant {selected_participant} for the selected "
            f"{trend_config['short_label']} target."
        ),
        "HISTORICAL EVIDENCE REQUIRES SAVED PARTICIPANT-LEVEL HOLDOUT PREDICTIONS",
        tone="watch",
    )

else:

    participant_trend = (
        participant_trend
        .dropna(
            subset=[
                "Target_Date",
                "Actual",
                "Prediction",
            ]
        )
        .sort_values("Target_Date")
    )

    if trend_config["type"] == "regression":

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=participant_trend["Target_Date"],
                y=participant_trend["Actual"],
                mode="lines+markers",
                name="Actual",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=participant_trend["Target_Date"],
                y=participant_trend["Prediction"],
                mode="lines+markers",
                name="Predicted",
            )
        )

        fig = chart_layout(
            fig,
            y_title="Calories",
            height=400,
        )

        fig.update_layout(
            title=(
                f"Calories Trend · Participant "
                f"{selected_participant}"
            ),
        )

    else:

        actual_values = pd.to_numeric(
            participant_trend["Actual"],
            errors="coerce",
        )

        predicted_values = pd.to_numeric(
            participant_trend["Prediction"],
            errors="coerce",
        )

        fig = go.Figure()

        # Classification targets are binary outcomes (0/1).
        # Plot the observed and predicted classes as discrete markers
        # and use positive probability as the continuous trend line.
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=participant_trend["Target_Date"],
                y=actual_values,
                mode="markers",
                name="Actual class",
                marker=dict(
                    symbol="circle",
                    size=9,
                ),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=participant_trend["Target_Date"],
                y=predicted_values,
                mode="markers",
                name="Predicted class",
                marker=dict(
                    symbol="x",
                    size=9,
                ),
            )
        )

        if "Positive_Probability" in participant_trend.columns:
            probabilities = pd.to_numeric(
                participant_trend[
                    "Positive_Probability"
                ],
                errors="coerce",
            )

            if probabilities.notna().any():
                fig.add_trace(
                    go.Scatter(
                        x=participant_trend["Target_Date"],
                        y=probabilities,
                        mode="lines+markers",
                        name="Positive probability",
                        line=dict(
                            dash="dot",
                            width=2,
                        ),
                        marker=dict(
                            size=5,
                        ),
                    )
                )

        fig = chart_layout(
            fig,
            y_title="Class / positive probability",
            height=400,
        )

        fig.update_yaxes(
            range=[-0.05, 1.05]
        )

        fig.update_layout(
            title=(
                f"{trend_config['short_label']} Trend · "
                f"Participant {selected_participant}"
            ),
        )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )

    insight_box(
        "Historical prediction evidence",
        (
            f"The chart contains {len(participant_trend):,} saved "
            f"participant-level holdout predictions from "
            f"{participant_trend['Target_Date'].min():%d %b %Y} "
            f"through {participant_trend['Target_Date'].max():%d %b %Y}. "
            "The model did not see these target observations during "
            "chronological training."
        ),
        "READ AS: OUT-OF-SAMPLE HISTORICAL EVIDENCE",
    )


# ============================================================
# MODEL MONITORING
# ============================================================

section_header(
    "05 · PREDICTION MONITORING",
    "What is the latest operational signal from the monitoring pipeline?",
    (
        "Monitoring is read from the persisted monitoring log. "
        "A review signal describes model behavior that deserves "
        "inspection; it is not itself a business or health decision."
    ),
)


latest_monitoring = pd.DataFrame()

if not monitoring_log.empty:
    latest_monitoring = (
        monitoring_log
        .sort_values(
            [
                "timestamp_utc"
            ]
            if "timestamp_utc" in monitoring_log.columns
            else monitoring_log.columns.tolist()
        )
        .groupby(
            "model_key",
            as_index=False,
        )
        .tail(1)
        .sort_values(
            "model_key"
        )
        .reset_index(drop=True)
    )


if latest_monitoring.empty:

    insight_box(
        "No monitoring events recorded",
        (
            "The prediction monitoring log has not produced a "
            "readable event for the current model set."
        ),
        "RUN: python scripts/run_predictive_monitoring.py --model all",
        tone="watch",
    )

else:

    monitoring_cols = st.columns(3)

    for column, key in zip(
        monitoring_cols,
        TARGETS,
    ):
        with column:

            row = latest_monitoring[
                latest_monitoring["model_key"]
                == key
            ]

            if row.empty:
                render_html(
                    f"""
                    <div class="monitor-card">

                        <div class="monitor-kicker">
                            {TARGETS[key]["icon"]} {TARGETS[key]["short_label"]}
                        </div>

                        <div class="monitor-title">
                            Monitoring signal
                        </div>

                        <div class="monitor-value">
                            —
                        </div>

                        <div class="monitor-copy">
                            No monitoring event is available.
                        </div>

                    </div>
                    """
                )
                continue

            event = row.iloc[-1]

            operational_status = str(
                event.get(
                    "operational_status",
                    "—",
                )
            )

            prediction_status = str(
                event.get(
                    "prediction_status",
                    "—",
                )
            )

            drift_status = str(
                event.get(
                    "drift_status",
                    "—",
                )
            )

            predicted = event.get(
                "predicted",
                np.nan,
            )

            actual = event.get(
                "actual",
                np.nan,
            )

            max_drift = event.get(
                "max_abs_z",
                np.nan,
            )

            render_html(
                f"""
                <div class="monitor-card">

                    <div class="monitor-kicker">
                        {TARGETS[key]["icon"]}
                        {TARGETS[key]["short_label"]}
                    </div>

                    <div class="monitor-title">
                        Latest monitoring result
                    </div>

                    <div class="monitor-value">
                        {operational_status}
                    </div>

                    <div class="monitor-copy">
                        Prediction status:
                        {prediction_status}<br>
                        Drift status:
                        {drift_status}<br>
                        Predicted:
                        {fmt_number(predicted, 2)}
                        · Actual:
                        {fmt_number(actual, 2)}<br>
                        Max drift:
                        {fmt_number(max_drift, 2)}σ
                    </div>

                    <span class="status-pill {status_class(operational_status)}">
                        {prediction_status}
                    </span>

                </div>
                """
            )


    display_monitoring = latest_monitoring.copy()

    rename_map = {
        "model_key": "Model",
        "model_version": "Version",
        "feature_date": "Feature Date",
        "target_date": "Target Date",
        "observation_date": "Observation Date",
        "predicted": "Predicted",
        "actual": "Actual",
        "prediction_status": "Prediction Status",
        "drift_status": "Drift Status",
        "max_abs_z": "Max Drift",
        "operational_status": "Operational Status",
        "review_required": "Review Required",
    }

    display_monitoring = display_monitoring.rename(
        columns={
            key: value
            for key, value in rename_map.items()
            if key in display_monitoring.columns
        }
    )

    preferred_monitoring_columns = [
        column
        for column in [
            "Model",
            "Version",
            "Feature Date",
            "Target Date",
            "Observation Date",
            "Predicted",
            "Actual",
            "Prediction Status",
            "Drift Status",
            "Max Drift",
            "Operational Status",
            "Review Required",
        ]
        if column in display_monitoring.columns
    ]

    st.dataframe(
        display_monitoring[
            preferred_monitoring_columns
        ],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# WALK-FORWARD VALIDATION
# ============================================================

section_header(
    "06 · WALK-FORWARD VALIDATION",
    "How did the models behave under sequential historical testing?",
    (
        "Walk-forward predictions are generated during training "
        "using earlier observations to predict later observations. "
        "This provides another historical check beyond the single "
        "chronological holdout."
    ),
)


available_backtests = [
    key
    for key in TARGETS
    if (
        artifacts[key]["available"]
        and not artifacts[key]["backtest"].empty
    )
]


if available_backtests:

    selected_backtest = st.selectbox(
        "Backtest target",
        available_backtests,
        format_func=lambda key: TARGETS[key]["label"],
        key="predictive_backtest_target",
    )

    backtest = get_target_backtest(
        artifacts,
        selected_backtest,
    )

    if {
        "Target_Date",
        "Actual",
        "Prediction",
    }.issubset(
        backtest.columns
    ):

        selected_config = TARGETS[
            selected_backtest
        ]

        # Walk-forward artifacts are participant-level. Aggregate
        # them by target date for a readable daily monitoring view.
        if selected_config["type"] == "regression":

            daily_backtest = (
                backtest
                .groupby(
                    "Target_Date",
                    as_index=False,
                )[
                    [
                        "Actual",
                        "Prediction",
                    ]
                ]
                .mean()
                .sort_values("Target_Date")
            )

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=daily_backtest["Target_Date"],
                    y=daily_backtest["Actual"],
                    mode="lines+markers",
                    name="Actual",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=daily_backtest["Target_Date"],
                    y=daily_backtest["Prediction"],
                    mode="lines+markers",
                    name="Prediction",
                )
            )

            y_title = "Daily mean target value"

        else:

            class_columns = [
                "Actual",
                "Prediction",
            ]

            if "Positive_Probability" in backtest.columns:
                class_columns.append(
                    "Positive_Probability"
                )

            daily_backtest = (
                backtest
                .groupby(
                    "Target_Date",
                    as_index=False,
                )[class_columns]
                .mean()
                .sort_values("Target_Date")
            )

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=daily_backtest["Target_Date"],
                    y=daily_backtest["Actual"],
                    mode="lines+markers",
                    name="Observed positive rate",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=daily_backtest["Target_Date"],
                    y=daily_backtest["Prediction"],
                    mode="lines+markers",
                    name="Predicted positive rate",
                )
            )

            if "Positive_Probability" in daily_backtest.columns:
                fig.add_trace(
                    go.Scatter(
                        x=daily_backtest["Target_Date"],
                        y=daily_backtest[
                            "Positive_Probability"
                        ],
                        mode="lines+markers",
                        name="Positive probability",
                        line=dict(
                            dash="dot"
                        ),
                    )
                )

            y_title = "Positive rate / probability"

        fig = chart_layout(
            fig,
            y_title=y_title,
            height=380,
        )

        fig.update_layout(
            title=(
                f"Walk-forward · "
                f"{selected_config['label']} · Daily summary"
            ),
        )

        if selected_config["type"] == "classification":
            fig.update_yaxes(
                range=[-0.05, 1.05]
            )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

        st.caption(
            "The chart aggregates participant-level walk-forward "
            "predictions by target date for readability. The metrics "
            "below are calculated from the underlying participant-level "
            "walk-forward prediction records."
        )

    backtest_metadata = artifacts[
        selected_backtest
    ]["metadata"]

    backtest_metrics = (
        backtest_metadata.get(
            "backtest_metrics",
            {},
        )
        or backtest_metadata.get(
            "backtest_metrics_selected",
            {},
        )
    )

    # Some persisted artifacts contain the walk-forward predictions
    # but do not persist their aggregate metrics. Calculate them from
    # the saved predictions so the dashboard never shows blank values.
    if not backtest_metrics:
        backtest_metrics = calculate_backtest_metrics(
            backtest=backtest,
            target_type=selected_config["type"],
        )

    if backtest_metrics:

        metric_rows = []

        preferred_metrics = (
            (
                [
                    "MAE",
                    "RMSE",
                    "R2",
                ]
            )
            if selected_config["type"] == "regression"
            else (
                [
                    "Accuracy",
                    "Precision",
                    "Recall",
                    "F1",
                    "ROC_AUC",
                ]
            )
        )

        for metric in preferred_metrics:
            if metric not in backtest_metrics:
                continue

            value = backtest_metrics[
                metric
            ]

            if not isinstance(
                value,
                (int, float),
            ):
                continue

            if pd.isna(value):
                continue

            metric_rows.append(
                {
                    "Metric": metric,
                    "Value": (
                        f"{float(value):.4f}"
                        if selected_config["type"]
                        == "regression"
                        else (
                            f"{float(value):.2%}"
                            if metric
                            in {
                                "Accuracy",
                                "Precision",
                                "Recall",
                            }
                            else f"{float(value):.4f}"
                        )
                    ),
                }
            )

        if metric_rows:
            st.dataframe(
                pd.DataFrame(metric_rows),
                use_container_width=True,
                hide_index=True,
            )

else:

    insight_box(
        "Walk-forward evidence unavailable",
        (
            "No saved walk-forward prediction artifacts are available "
            "for the current model set."
        ),
        tone="watch",
    )


# ============================================================
# CALORIE SCENARIO PLANNING
# ============================================================

section_header(
    "07 · SCENARIO PLANNING",
    "How does the persisted calorie model respond to a different activity profile?",
    (
        "This is an interactive hypothetical scenario, not the "
        "routine production forecast. Changing a slider does not "
        "overwrite the prediction store."
    ),
)


calorie_artifact = artifacts[
    "calories"
]


if calorie_artifact["available"]:

    calorie_model = calorie_artifact[
        "model"
    ]

    calorie_metadata = calorie_artifact[
        "metadata"
    ]

    calorie_features = list(
        calorie_metadata.get(
            "feature_columns",
            calorie_metadata.get(
                "features",
                [],
            ),
        )
    )

    scenario_left, scenario_right = st.columns(
        [1.25, 0.75]
    )

    latest_steps = pd.to_numeric(
        pd.Series(
            [selected_latest_row.get("TotalSteps")]
        ),
        errors="coerce",
    ).iloc[0]

    latest_active = pd.to_numeric(
        pd.Series(
            [selected_latest_row.get("Total_Active_Minutes")]
        ),
        errors="coerce",
    ).iloc[0]

    latest_sedentary = pd.to_numeric(
        pd.Series(
            [selected_latest_row.get("SedentaryMinutes")]
        ),
        errors="coerce",
    ).iloc[0]

    with scenario_left:

        scenario_steps = st.slider(
            "Previous-day steps",
            min_value=0,
            max_value=25000,
            value=int(
                np.clip(
                    0 if pd.isna(latest_steps) else latest_steps,
                    0,
                    25000,
                )
            ),
            step=250,
            key="predictive_scenario_steps",
        )

        scenario_active = st.slider(
            "Previous-day active minutes",
            min_value=0,
            max_value=600,
            value=int(
                np.clip(
                    0 if pd.isna(latest_active) else latest_active,
                    0,
                    600,
                )
            ),
            step=5,
            key="predictive_scenario_active",
        )

        scenario_sedentary = st.slider(
            "Previous-day sedentary minutes",
            min_value=0,
            max_value=1200,
            value=int(
                np.clip(
                    0 if pd.isna(latest_sedentary) else latest_sedentary,
                    0,
                    1200,
                )
            ),
            step=10,
            key="predictive_scenario_sedentary",
        )

        st.caption(
            "All other calorie-model inputs remain at the selected "
            "participant's latest usable observation."
        )

    if calorie_features:

        scenario_input = pd.DataFrame(
            [
                {
                    feature: np.nan
                    for feature in calorie_features
                }
            ]
        )

        latest_feature_values = {}

        for feature in calorie_features:
            if feature.startswith("Lag1_"):
                raw_column = feature[len("Lag1_"):]

                value = pd.to_numeric(
                    pd.Series(
                        [selected_latest_row.get(raw_column)]
                    ),
                    errors="coerce",
                ).iloc[0]

                latest_feature_values[
                    feature
                ] = value

            else:
                if feature == "Target_Day_Of_Week_Num":
                    latest_feature_values[
                        feature
                    ] = float(
                        (
                            selected_latest_date
                            + pd.Timedelta(days=1)
                        ).dayofweek
                    )
                elif feature == "Target_Is_Weekend":
                    latest_feature_values[
                        feature
                    ] = float(
                        (
                            selected_latest_date
                            + pd.Timedelta(days=1)
                        ).dayofweek
                        >= 5
                    )
                else:
                    latest_feature_values[
                        feature
                    ] = pd.to_numeric(
                        pd.Series(
                            [selected_latest_row.get(feature)]
                        ),
                        errors="coerce",
                    ).iloc[0]

        for feature, value in latest_feature_values.items():
            scenario_input.loc[
                scenario_input.index[0],
                feature,
            ] = value

        baseline_input = scenario_input.copy()

        scenario_input.loc[
            scenario_input.index[0],
            "Lag1_TotalSteps",
        ] = scenario_steps

        scenario_input.loc[
            scenario_input.index[0],
            "Lag1_Total_Active_Minutes",
        ] = scenario_active

        scenario_input.loc[
            scenario_input.index[0],
            "Lag1_SedentaryMinutes",
        ] = scenario_sedentary

        try:

            baseline_prediction = float(
                calorie_model.predict(
                    baseline_input[
                        calorie_features
                    ]
                )[0]
            )

            scenario_prediction = float(
                calorie_model.predict(
                    scenario_input[
                        calorie_features
                    ]
                )[0]
            )

            delta = (
                scenario_prediction
                - baseline_prediction
            )

            delta_pct = (
                delta
                / baseline_prediction
                * 100
                if baseline_prediction != 0
                else np.nan
            )

            with scenario_right:

                render_html(
                    f"""
                    <div class="scenario-result">

                        <div class="scenario-kicker">
                            MODEL RESPONSE
                        </div>

                        <div class="scenario-value">
                            {scenario_prediction:,.0f}
                        </div>

                        <div class="scenario-delta">
                            {delta:+,.0f} kcal
                            ({delta_pct:+.1f}%)
                            vs current-profile model response
                        </div>

                        <div class="scenario-copy">
                            Current-profile model response:
                            {baseline_prediction:,.0f} kcal.

                            <br><br>

                            The scenario changes selected inputs and
                            observes the response of the persisted
                            calorie model. It does not claim that the
                            changed inputs cause the displayed outcome.
                        </div>

                    </div>
                    """
                )

        except Exception as exc:

            with scenario_right:

                insight_box(
                    "Scenario unavailable",
                    (
                        "The hypothetical scenario could not be "
                        f"calculated: {exc}"
                    ),
                    tone="watch",
                )

else:

    insight_box(
        "Scenario planning unavailable",
        "The persisted calorie model is not available.",
        tone="watch",
    )


# ============================================================
# MODEL DRIVERS
# ============================================================

section_header(
    "08 · MODEL DRIVERS",
    "What inputs do the persisted models rely on most?",
    (
        "For tree-based models, feature importance shows relative "
        "predictive contribution. For linear models, absolute "
        "coefficient magnitude provides a comparable descriptive "
        "view. Neither measure establishes causation."
    ),
)


available_driver_targets = [
    key
    for key in TARGETS
    if artifacts[key]["available"]
]


if available_driver_targets:

    selected_driver = st.selectbox(
        "Model driver",
        available_driver_targets,
        format_func=lambda key: TARGETS[key]["label"],
        key="predictive_driver_target",
    )

    driver_model = artifacts[
        selected_driver
    ]["model"]

    driver_metadata = artifacts[
        selected_driver
    ]["metadata"]

    driver_features = list(
        driver_metadata.get(
            "feature_columns",
            driver_metadata.get(
                "features",
                [],
            ),
        )
    )

    values = None
    value_label = None

    inner_model = (
        driver_model.named_steps.get("model")
        if hasattr(
            driver_model,
            "named_steps",
        )
        else driver_model
    )

    if hasattr(
        inner_model,
        "feature_importances_",
    ):
        values = np.asarray(
            inner_model.feature_importances_
        )
        value_label = (
            "Relative feature importance"
        )

    elif hasattr(
        inner_model,
        "coef_",
    ):
        coefficients = np.asarray(
            inner_model.coef_
        )

        if coefficients.ndim > 1:
            coefficients = np.abs(
                coefficients[0]
            )
        else:
            coefficients = np.abs(
                coefficients
            )

        values = coefficients
        value_label = (
            "Absolute coefficient magnitude"
        )

    if (
        values is not None
        and len(values) == len(driver_features)
    ):

        driver_df = pd.DataFrame(
            {
                "Feature": [
                    feature_label(feature)
                    for feature in driver_features
                ],
                "Value": values,
            }
        )

        driver_df = (
            driver_df
            .sort_values(
                "Value",
                ascending=False,
            )
            .head(15)
            .sort_values(
                "Value",
                ascending=True,
            )
        )

        fig = px.bar(
            driver_df,
            x="Value",
            y="Feature",
            orientation="h",
        )

        fig = chart_layout(
            fig,
            y_title=None,
            height=420,
        )

        fig.update_xaxes(
            title_text=value_label
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    else:
        insight_box(
            "Driver information unavailable",
            (
                "The selected persisted model does not expose "
                "feature-level driver information in a compatible form."
            ),
            tone="watch",
        )


# ============================================================
# TECHNICAL APPENDIX
# ============================================================

section_header(
    "09 · TECHNICAL APPENDIX",
    "Model artifacts, prediction store, validation, and reproducibility",
    (
        "The technical layer exposes the evidence behind the "
        "dashboard without retraining or regenerating routine forecasts."
    ),
)


with st.expander(
    "Prediction store",
    expanded=False,
):

    if prediction_store.empty:

        st.info(
            "Prediction store is unavailable."
        )

    else:

        store_display = prediction_store.copy()

        st.dataframe(
            store_display,
            use_container_width=True,
            hide_index=True,
        )


with st.expander(
    "Model metadata",
    expanded=False,
):

    metadata_rows = []

    for key, config in TARGETS.items():

        artifact = artifacts[key]

        if not artifact["available"]:
            continue

        metadata = artifact["metadata"]

        metadata_rows.append(
            {
                "Target": config["label"],
                "Model version": metadata.get(
                    "model_version",
                    "—",
                ),
                "Algorithm": metadata.get(
                    "algorithm",
                    "—",
                ),
                "Target type": metadata.get(
                    "target_type",
                    config["type"],
                ),
                "Forecast horizon": metadata.get(
                    "forecast_horizon",
                    "next participant-day",
                ),
                "Source rows": metadata.get(
                    "source_rows",
                    "—",
                ),
                "Forecast rows": metadata.get(
                    "forecast_rows",
                    "—",
                ),
                "Training rows": metadata.get(
                    "training_rows",
                    "—",
                ),
                "Holdout rows": metadata.get(
                    "holdout_rows",
                    "—",
                ),
                "Backtest rows": metadata.get(
                    "backtest_rows",
                    "—",
                ),
                "Approval": model_status(metadata),
            }
        )

    if metadata_rows:
        st.dataframe(
            pd.DataFrame(
                metadata_rows
            ),
            use_container_width=True,
            hide_index=True,
        )


with st.expander(
    "Selected model metrics",
    expanded=False,
):

    metric_rows = []

    for key, config in TARGETS.items():

        artifact = artifacts[key]

        if not artifact["available"]:
            continue

        metadata = artifact["metadata"]

        metrics = selected_metrics(
            metadata
        )

        for metric, value in metrics.items():

            if not isinstance(
                value,
                (int, float),
            ):
                continue

            if pd.isna(value):
                continue

            metric_rows.append(
                {
                    "Target": config["label"],
                    "Algorithm": metadata.get(
                        "algorithm",
                        "—",
                    ),
                    "Metric": metric,
                    "Value": value,
                }
            )

    if metric_rows:

        st.dataframe(
            pd.DataFrame(
                metric_rows
            ),
            use_container_width=True,
            hide_index=True,
        )


with st.expander(
    "Configured model features",
    expanded=False,
):

    feature_rows = []

    for key, config in TARGETS.items():

        artifact = artifacts[key]

        if not artifact["available"]:
            continue

        metadata = artifact["metadata"]

        configured_features = metadata.get(
            "feature_columns",
            metadata.get(
                "features",
                [],
            ),
        )

        for position, feature in enumerate(
            configured_features,
            start=1,
        ):
            feature_rows.append(
                {
                    "Target": config["label"],
                    "Order": position,
                    "Feature": feature_label(
                        feature
                    ),
                    "Model column": feature,
                }
            )

    if feature_rows:

        st.dataframe(
            pd.DataFrame(
                feature_rows
            ),
            use_container_width=True,
            hide_index=True,
        )


with st.expander(
    "Methodology and limitations",
    expanded=False,
):

    insight_box(
        "Routine prediction architecture",
        (
            "The production prediction script loads the canonical "
            "fitness dataset, selects each participant's latest "
            "usable observation, loads the persisted model artifacts, "
            "generates one next-day record per participant, and writes "
            "the results to predictions.csv. The dashboard reads those "
            "stored routine forecasts."
        ),
        "PREDICTION STORE",
    )

    insight_box(
        "Historical validation",
        (
            "The training pipeline uses a chronological holdout and "
            "an expanding-window walk-forward backtest. The dashboard "
            "reads the resulting saved prediction evidence."
        ),
        "CHRONOLOGICAL HOLDOUT + WALK-FORWARD",
    )

    insight_box(
        "Interpretation",
        (
            "Regression predictions estimate calorie expenditure. "
            "Classification predictions represent model classes and "
            "positive probabilities. Prediction errors, probabilities, "
            "and feature importance describe model behavior and do not "
            "establish causal relationships."
        ),
        "ANALYTICAL DECISION SUPPORT",
    )

    insight_box(
        "Deployment limitation",
        (
            "The routine prediction layer is now separated from the "
            "dashboard, but the project still uses a historical "
            "dataset and shadow-status artifacts. A real production "
            "deployment would additionally require live data ingestion, "
            "data-quality gates, model promotion controls, scheduling, "
            "security, alerting, and operational infrastructure."
        ),
        "CURRENT STATE: SHADOW / ANALYTICAL",
        tone="watch",
    )


# ============================================================
# FOOTER
# ============================================================

forecast_footer_date = None

if not participant_prediction.empty:
    forecast_footer_date = pd.Timestamp(
        participant_prediction.iloc[0]["Target_Date"]
    )

render_html(
    f"""
    <div class="footer-note">

        Predictive analytics workflow:
        canonical dataset →
        model artifacts →
        prediction pipeline →
        prediction store →
        dashboard →
        monitoring.

        <br><br>

        Models available:
        <strong style="color:#d7dbe0;">
            {available_model_count}/3
        </strong>

        · Selected participant:
        <strong style="color:#d7dbe0;">
            {selected_participant}
        </strong>

        · Forecast date:
        <strong style="color:#d7dbe0;">
            {
                forecast_footer_date.strftime("%d %b %Y")
                if forecast_footer_date is not None
                else "—"
            }
        </strong>

        <br><br>

        Routine next-day forecasts are read from the persisted
        prediction store. Shadow mode means the artifacts remain
        in analytical evaluation rather than being represented as
        autonomous clinical or operational decision systems.

    </div>
    """
)
