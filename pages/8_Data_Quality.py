
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data import load_data

st.title("Data Quality")
st.caption("Monitor whether the analytical dataset is complete and structurally healthy.")

df = load_data()

duplicates = df.duplicated(subset=["Id","Date"]).sum()
missing_total = int(df.isna().sum().sum())
rows, cols = df.shape

c1,c2,c3,c4 = st.columns(4)
c1.metric("Rows", f"{rows:,}")
c2.metric("Columns", f"{cols:,}")
c3.metric("Missing Cells", f"{missing_total:,}")
c4.metric("Duplicate Participant-Date", f"{duplicates:,}")

quality = pd.DataFrame({
    "Column": df.columns,
    "Missing": df.isna().sum().values,
    "Missing %": (df.isna().mean().values*100),
    "Unique": df.nunique(dropna=True).values,
    "Data Type": df.dtypes.astype(str).values,
}).sort_values("Missing %", ascending=False)

st.subheader("Column Completeness")
st.dataframe(quality.style.format({"Missing %":"{:.2f}"}), use_container_width=True, hide_index=True)

missing = quality[quality["Missing"]>0].head(20)
if not missing.empty:
    st.plotly_chart(px.bar(missing.sort_values("Missing"), x="Missing", y="Column", orientation="h",
                           title="Columns with Missing Values"), use_container_width=True)

st.subheader("Date Coverage")
st.write(f"**{df['Date'].min().date()} → {df['Date'].max().date()}**")
st.write(f"**{df['Id'].nunique():,} unique participants** across **{df['Date'].nunique():,} dates**.")
