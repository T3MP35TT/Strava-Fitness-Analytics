# Strava Fitness Analytics App

An end-to-end **Data Analytics and Business Analytics portfolio project** that transforms multi-granular fitness activity data into an interactive decision-support application.

The project combines **data preparation, exploratory analysis, KPI reporting, statistical analysis, predictive modeling, SQL analytics, data quality controls, and business insight generation** in a single Streamlit application.

> **Purpose:** demonstrate how a Data Analyst / Business Analyst can move from raw operational data to trusted metrics, predictive signals, and business-oriented recommendations.

---

## Executive Summary

Fitness activity data is often fragmented across daily, hourly, and minute-level records. A business-facing analytics solution needs more than charts: it needs a consistent data model, defined KPIs, quality checks, analytical workflows, and a clear path from findings to decisions.

This project addresses that problem through a structured analytics pipeline:

**Raw Data → Data Preparation → Analytical Dataset → KPI Reporting → Statistical Analysis → Predictive Insights → SQL Analysis → Business Insights**

The resulting Streamlit application provides an interactive environment for exploring participant behavior, activity patterns, calorie expenditure, sleep and wellness indicators, predictive outputs, and business questions.

---

## Business Problem

A fitness analytics business may want to understand:

- How active are participants over time?
- What drives differences in daily activity and calorie expenditure?
- Which participants or behavioral patterns require attention?
- How are sleep and wellness related to activity behavior?
- Can historical activity patterns support next-day predictions?
- Which findings are useful for product, engagement, wellness, or customer-success decisions?

The challenge is to answer these questions using data that is:

- consistent across multiple source tables,
- sufficiently validated before analysis,
- easy for non-technical stakeholders to explore,
- reproducible through code,
- and connected to measurable business questions.

---

## Business Objectives

The project is designed around five practical objectives:

### 1. Measure Performance
Track activity, steps, distance, intensity, calories, sleep, and other fitness KPIs.

### 2. Understand Behavior
Identify participant-level and time-based patterns in activity and wellness behavior.

### 3. Detect Relationships
Use statistical analysis to investigate relationships between operational and behavioral variables.

### 4. Predict Outcomes
Use historical activity information to generate predictive signals for calories, activity-target attainment, and sleep-target attainment.

### 5. Support Decisions
Translate analytical findings into business-oriented insights rather than stopping at visualization.

---

# Application Pages

The Streamlit application is organized as a stakeholder-oriented analytics workspace.

| Page | Business Purpose |
|---|---|
| **Executive Overview** | High-level KPI summary and overall fitness performance |
| **Activity and Calories** | Analyze steps, distance, intensity, activity patterns, and calories |
| **Sleep and Wellness** | Explore sleep behavior and wellness indicators |
| **Participant Analysis** | Compare participant-level performance and behavior |
| **Statistical Analysis** | Examine distributions, relationships, and statistical patterns |
| **Predictive Insights** | View model outputs, performance, and prediction monitoring |
| **SQL Playground** | Answer business questions using controlled SQL analysis |
| **Business Insights** | Translate analytical results into stakeholder-ready findings |

---

# Key Analytical Questions

The application is built around questions a business stakeholder could realistically ask.

### Engagement & Activity

- How active are participants across the observed period?
- What does daily activity look like over time?
- Which activity levels are most common?
- How do steps, distance, and intensity vary between participants?

### Calories

- How does calorie expenditure vary by activity behavior?
- Which variables are associated with higher or lower calorie expenditure?
- Are there meaningful differences between participant groups?

### Sleep & Wellness

- How frequently do participants achieve the defined sleep target?
- How does sleep behavior vary across participants?
- Are there observable relationships between sleep and activity?

### Participant Performance

- Which participants show consistently high activity?
- Which participants show lower or inconsistent engagement?
- How stable are individual activity patterns?

### Predictive Analytics

- Can historical activity signals help estimate next-day calories?
- Can previous behavior help classify whether a participant will meet an activity target?
- Can historical sleep information help classify sleep-target attainment?

### Business Analysis

- What findings are most relevant to engagement and wellness use cases?
- Where could monitoring or targeted interventions be considered?
- Which metrics should stakeholders continue tracking?

---

# Analytics Workflow

## 1. Data Preparation

The project begins with multiple raw fitness datasets covering different levels of granularity, including:

- daily activity
- daily calories
- daily intensities
- daily steps
- heart-rate observations
- hourly calories
- hourly intensities
- hourly steps
- minute-level calories
- minute-level intensities
- minute-level METs
- minute-level sleep
- minute-level steps
- sleep-day records
- weight-log records

The cleaning notebook consolidates the source data into a canonical analytical dataset.

### Canonical Dataset

```text
data/processed/fitness_daily_master.csv
```

Additional metadata is maintained in:

```text
data/processed/fitness_data_dictionary.csv
```

---

# Data Quality

A production-style analytics workflow should validate data before downstream modeling and reporting.

The project includes a reusable data-quality gate that checks the analytical dataset before model training and prediction generation.

```text
scripts/run_data_quality_gate.py
```

The quality framework distinguishes between:

- **PASS** — validation completed successfully
- **WARN** — a known limitation or missingness pattern exists but is handled by the pipeline
- **FAIL** — a condition prevents reliable downstream processing

### Current Data Quality Consideration

Sleep-related fields contain substantial missingness in the historical data. Rather than treating missing sleep observations as a positive or negative sleep outcome, the target logic was repaired so unavailable observations remain missing and are handled explicitly by the predictive workflow.

This is an important analytical principle:

> Missing data should not automatically be interpreted as negative behavior.

Quality and pipeline outputs are written to:

```text
data/quality/
```

These files are generated artifacts rather than core dashboard inputs.

---

# Predictive Analytics

The project includes a reproducible predictive analytics pipeline for three business-relevant targets.

## Prediction Targets

| Target | Problem Type | Business Meaning |
|---|---|---|
| **Calories** | Regression | Estimate next-day calorie expenditure |
| **Activity Target** | Classification | Predict whether the participant will meet the defined activity target |
| **Sleep Target** | Classification | Predict whether the participant will meet the defined sleep target |

The model feature set uses historical activity information through lag-based features together with calendar variables.

This is deliberately structured around **historical information available before the prediction date**, reducing the risk of target leakage.

---

## Model Development

The predictive workflow includes:

1. feature preparation
2. chronological train / holdout / backtest splitting
3. model training
4. model comparison
5. evaluation
6. prediction generation
7. monitoring
8. model artifact storage

The main training script is:

```text
scripts/train_predictive_model.py
```

### Model Results

The latest validated training run produced the following holdout metrics:

| Model | Metric | Result |
|---|---|---:|
| Calories Regression | MAE | 469.21 |
| Calories Regression | RMSE | 725.36 |
| Calories Regression | R² | 0.296 |
| Activity Target | Accuracy | 0.799 |
| Activity Target | Precision | 0.590 |
| Activity Target | Recall | 0.857 |
| Activity Target | F1 | 0.699 |
| Activity Target | ROC-AUC | 0.908 |
| Sleep Target | Accuracy | 0.667 |
| Sleep Target | Precision | 0.717 |
| Sleep Target | Recall | 0.767 |
| Sleep Target | F1 | 0.742 |
| Sleep Target | ROC-AUC | 0.688 |

For the calories target, a linear-regression comparison was also performed. The comparison helps demonstrate that model selection is based on measured performance rather than assuming a more complex model is automatically better.

> These metrics are descriptive results from the historical dataset used in this project. They should not be interpreted as evidence of production performance on a new population.

---

# Prediction Generation

After training, the pipeline generates participant-level prediction records.

```text
scripts/run_predictive_predictions.py
```

Output:

```text
data/processed/predictions.csv
```

The generated prediction dataset is used by the Streamlit predictive-insights page.

---

# Prediction Monitoring

The project also includes post-prediction monitoring.

```text
scripts/run_predictive_monitoring.py
```

Monitoring compares predictions with available actual outcomes and records model-review signals.

The monitoring workflow evaluates:

- prediction vs. actual outcome
- prediction status
- historical-range checks
- feature-drift indicators
- review-required conditions

This creates a simple but realistic **model monitoring loop** instead of treating model training as a one-time activity.

---

# Production-Style Pipeline

The complete workflow can be executed through a single orchestrator:

```text
scripts/run_production_pipeline.py
```

Pipeline sequence:

```text
Data Quality Gate
        ↓
Model Training
        ↓
Prediction Generation
        ↓
Prediction Monitoring
        ↓
Run Report
```

Example:

```bash
python scripts/run_production_pipeline.py
```

The pipeline produces run-level status and audit information under:

```text
data/quality/
```

This design makes the project closer to a real analytics workflow where data validation, model generation, and monitoring are connected rather than executed manually as unrelated notebook steps.

---

# SQL Analytics Playground

The application includes a controlled SQL Playground for business analysis.

```text
pages/7_SQL_Playground.py
```

The SQL layer is designed for read-only analytical use.

The SQL execution framework includes controls such as:

- `SELECT` / `WITH` query enforcement
- single-statement execution
- result-size limits
- query-length limits
- execution timeout
- SQLite read-only access
- write/schema operation blocking
- query auditing

The SQL functionality is intended to demonstrate how an analyst can translate business questions into reproducible SQL queries while maintaining basic execution safeguards.

---

# Business Questions

The SQL Playground includes predefined business-oriented questions covering areas such as:

- participant activity
- performance comparison
- productive activity behavior
- rankings
- trends
- target attainment
- participant segmentation
- other stakeholder-oriented analytical questions

Users can also inspect the underlying SQL before execution.

This supports an important Business Analyst workflow:

**Business Question → Metric Definition → SQL Logic → Result → Interpretation**

---

# Business Insights

The final analytics layer translates findings into business-oriented observations.

Rather than presenting only charts, the Business Insights page focuses on:

### Performance
What the available data indicates about overall participant activity and behavior.

### Engagement
Where differences in participation or consistency may exist.

### Wellness
How sleep and activity measures behave within the available historical records.

### Predictive Signals
Where model outputs may help prioritize attention or monitoring.

### Decision Support
What stakeholders could reasonably monitor, investigate, or use as an input to future analysis.

The objective is not to prescribe actions automatically, but to demonstrate how analytical evidence can support business decisions.

---

# Project Architecture

```text
Strava Fitness App Project/
│
├── Home.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── processed/
│   │   ├── fitness_daily_master.csv
│   │   ├── fitness_data_dictionary.csv
│   │   └── predictions.csv
│   │
│   ├── quality/
│   │   ├── data_quality_report.json
│   │   ├── production_pipeline_latest.json
│   │   ├── production_pipeline_history.jsonl
│   │   └── sql_query_audit_log.csv
│   │
│   └── raw / merged source datasets
│
├── images/
│   └── strava_logo.png
│
├── models/
│   └── predictive_models/
│       ├── activity_target/
│       ├── calories/
│       ├── sleep_target/
│       └── monitoring_log.csv
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
│   └── 8_Business_Insights.py
│
├── scripts/
│   ├── run_data_quality_gate.py
│   ├── run_predictive_monitoring.py
│   ├── run_predictive_predictions.py
│   ├── run_production_pipeline.py
│   └── train_predictive_model.py
│
└── utils/
    ├── __init__.py
    ├── data.py
    ├── data_quality.py
    ├── predictive_model.py
    ├── predictive_registry.py
    ├── sql.py
    └── theme.py
```

---

# Technology Stack

| Area | Technologies |
|---|---|
| Application | Python, Streamlit |
| Data Analysis | Pandas, NumPy |
| Visualization | Plotly, Matplotlib |
| Statistical Analysis | Python statistical tooling |
| Machine Learning | Scikit-learn |
| SQL | SQL, SQLite |
| Data Processing | Python / Pandas |
| Model Persistence | Joblib |
| Development | VS Code, Git, GitHub |
| Documentation | Markdown |

---

# Getting Started

## 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd <repository-folder>
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Run the Streamlit application

```bash
streamlit run Home.py
```

The application will open in the browser.

---

# Reproducing the Analytics Pipeline

The application can be used directly from the prepared analytical data.

For a complete model refresh, run:

```bash
python scripts/run_production_pipeline.py
```

Or execute the individual stages:

```bash
python scripts/run_data_quality_gate.py
```

```bash
python scripts/train_predictive_model.py
```

```bash
python scripts/run_predictive_predictions.py
```

```bash
python scripts/run_predictive_monitoring.py --model all
```

This structure supports reproducibility and makes each stage independently auditable.

---

# Data Design

The analytical workflow separates source data from the canonical dataset.

### Source Layer

Multiple merged datasets preserve the original granularity of the collected fitness observations.

### Analytical Layer

```text
fitness_daily_master.csv
```

acts as the central daily analytical dataset used by downstream reporting and predictive workflows.

### Prediction Layer

```text
predictions.csv
```

stores generated prediction outputs for application consumption.

### Model Layer

```text
models/predictive_models/
```

stores trained model artifacts and associated metadata.

### Monitoring Layer

```text
data/quality/
```

stores data-quality, pipeline, and SQL audit outputs.

This separation supports a simple analytics architecture:

```text
Source Data
    ↓
Data Preparation
    ↓
Canonical Analytical Dataset
    ↓
 ┌───────────────┬──────────────────┬─────────────────┐
 ↓               ↓                  ↓
Dashboards     SQL Analysis      Predictive Models
 ↓               ↓                  ↓
Business Insights ←────── Decision Support ──────→ Monitoring
```

---

# Analytical Governance

Several practices were intentionally included to make the project closer to real-world analytics work.

### Reproducibility

Core transformations and model workflows are implemented in Python scripts rather than relying entirely on manual notebook execution.

### Metric Consistency

The application is built around a canonical analytical dataset so that dashboard metrics, SQL analysis, and predictive features are aligned.

### Data Validation

A dedicated quality gate runs before the predictive pipeline.

### Leakage Prevention

Predictive features are based on historical information relative to the prediction date.

### Monitoring

Predictions are evaluated after generation instead of assuming that a trained model remains reliable indefinitely.

### Controlled SQL

The SQL Playground is intentionally restricted to read-only analytical access.

---

# Important Limitations

This project uses a **historical fixed dataset**, so several real-world capabilities are outside the current scope.

### Historical Data Only

The application does not represent a continuously updating production data stream.

### No Live User Authentication

There is no implemented user-account or authentication system.

### No External Production Ingestion

The project does not claim to provide a live production ingestion pipeline from a fitness platform API.

### Limited Population

Model performance is dependent on the population and historical period represented in the dataset.

### Predictive Results Are Decision Support

Predictions should be treated as analytical signals rather than guaranteed outcomes.

### Missing Data

Some wellness fields, particularly sleep-related fields, contain missing observations. The modeling workflow explicitly handles missingness rather than assuming missing values represent a behavioral outcome.

---

# What This Project Demonstrates

From a **Data Analyst** perspective:

- data cleaning and preparation
- exploratory data analysis
- KPI design
- dashboard development
- statistical analysis
- SQL analytics
- analytical storytelling
- predictive modeling
- model evaluation
- data-quality validation
- reproducible analytical workflows

From a **Business Analyst** perspective:

- converting business questions into measurable metrics
- stakeholder-oriented dashboard design
- structured problem solving
- performance analysis
- segmentation and comparison
- identifying meaningful trends
- translating quantitative findings into business insights
- supporting evidence-based decisions
- communicating limitations and uncertainty

---

# Portfolio Highlights

### End-to-End Analytics

The project covers the full analytical journey from raw datasets to business-facing outputs.

### Stakeholder-Oriented Reporting

The application is structured around business questions and decision-support use cases rather than only technical demonstrations.

### Predictive Analytics

Three predictive targets demonstrate regression and classification workflows using historical behavioral data.

### SQL Business Analysis

The SQL Playground demonstrates practical SQL querying tied to business questions.

### Data Quality & Monitoring

The project includes validation, pipeline status reporting, prediction monitoring, and SQL query auditing.

### Reproducibility

The main data and model workflows can be executed through scripts instead of depending solely on manual notebook steps.

---

# Suggested Portfolio Talking Points

A concise way to present the project in an interview:

> **Built an end-to-end fitness analytics application in Python and Streamlit that transformed multi-granular activity data into KPI dashboards, statistical analysis, business-oriented SQL insights, and predictive models for calorie expenditure, activity-target attainment, and sleep-target attainment. Implemented a data-quality gate, reproducible model pipeline, prediction monitoring, and controlled SQL execution to make the workflow closer to a real-world analytics solution.**

---

# Project Outcome

The final application demonstrates how analytical teams can combine:

**Data → Metrics → Insights → Predictions → Monitoring**

into a single decision-support workflow.

The project is intentionally scoped around the capabilities supported by the historical dataset, while still applying real-world analytics practices such as data validation, reproducibility, model evaluation, monitoring, and stakeholder-oriented storytelling.

---

## License

This project is intended as a portfolio and learning project.

Add the appropriate license here if the repository will be distributed publicly under a specific license.
