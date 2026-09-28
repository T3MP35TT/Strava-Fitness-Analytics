
import streamlit as st
import numpy as np
import plotly.express as px
from utils.data import load_data, activity_groups

st.title("Business Insights & Action Center")
st.caption("Translate analytical signals into product, engagement, and monitoring opportunities.")

df = load_data()
filtered = st.session_state.get("global_filtered", df)
if filtered.empty:
    st.warning("No records match the current filters.")
    st.stop()

activity = activity_groups(filtered)

c1,c2,c3,c4 = st.columns(4)
c1.metric("10K Goal Rate", f"{filtered['Meets_10k_Steps'].mean()*100:.1f}%")
c2.metric("Avg Sedentary Time", f"{filtered['SedentaryMinutes'].mean():,.0f} min")
c3.metric("Avg Active Time", f"{filtered['Total_Active_Minutes'].mean():,.0f} min")
c4.metric("Avg Sleep", f"{filtered['Sleep_Minutes'].mean()/60:.1f} hrs")

st.subheader("Opportunity Areas")

opportunities = []

goal_rate = filtered["Meets_10k_Steps"].mean()
if goal_rate < 0.50:
    opportunities.append(
        ("Goal engagement", "A substantial share of participant-days are below the 10K step benchmark. "
         "Consider progress nudges, streaks, adaptive goals, and weekly progress summaries.")
    )
else:
    opportunities.append(
        ("Goal engagement", "10K-step attainment is relatively common in the selected population. "
         "Consider progressive goals and personalized challenges rather than a single fixed benchmark.")
    )

sedentary = filtered["SedentaryMinutes"].mean()
opportunities.append(
    ("Sedentary behavior", f"Average sedentary time is {sedentary:,.0f} minutes/day. "
     "Product teams could test inactivity reminders or movement-break programs.")
)

if not activity.empty:
    high = activity.loc[activity["Activity_Level"]=="High Activity","Calories"].mean()
    low = activity.loc[activity["Activity_Level"]=="Low Activity","Calories"].mean()
    opportunities.append(
        ("Behavioral segmentation",
         f"Activity groups show different calorie profiles in this dataset "
         f"(Low Activity ≈ {low:,.0f}; High Activity ≈ {high:,.0f} calories/day). "
         "This supports differentiated engagement strategies.")
    )

for title, body in opportunities:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.write(body)

st.subheader("Monitoring View")

daily = filtered.groupby("Date", as_index=False).agg(
    Avg_Steps=("TotalSteps","mean"),
    Avg_Calories=("Calories","mean"),
    Avg_Sedentary=("SedentaryMinutes","mean"),
    Goal_Rate=("Meets_10k_Steps","mean"),
)
daily["Goal_Rate"] *= 100

metric = st.selectbox(
    "Operational metric",
    ["Avg_Steps","Avg_Calories","Avg_Sedentary","Goal_Rate"],
    format_func=lambda x: {
        "Avg_Steps":"Average Steps",
        "Avg_Calories":"Average Calories",
        "Avg_Sedentary":"Average Sedentary Minutes",
        "Goal_Rate":"10K Goal Rate (%)",
    }[x],
)
st.plotly_chart(px.line(daily, x="Date", y=metric, markers=True, title="Metric Monitoring Trend"),
                use_container_width=True)

st.info(
    "These are analytical opportunities, not clinical recommendations. "
    "Use additional product, user, and outcome data before making operational decisions."
)
