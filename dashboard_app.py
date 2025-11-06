import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Selenium Test Dashboard", layout="wide")

st.title("🧪 Selenium Automation Dashboard")

conn = sqlite3.connect("results.db")
df = pd.read_sql_query("SELECT * FROM results ORDER BY date DESC", conn)

if not df.empty:
    suites = df["suite_name"].unique()
    suite = st.selectbox("Select Test Suite", suites)

    filtered = df[df["suite_name"] == suite]
    latest = filtered.iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", int(latest["total"]))
        st.metric("Passed", int(latest["passed"]))
        st.metric("Failed", int(latest["failed"]))
        st.metric("Pass %", f"{latest['pass_percent']}%")
    with col2:
        pie = px.pie(values=[latest["passed"], latest["failed"], latest["skipped"]],
                     names=["Passed", "Failed", "Skipped"],
                     title=f"{suite} - Latest Execution")
        st.plotly_chart(pie, use_container_width=True)

    trend = px.line(filtered, x="date", y="pass_percent",
                    title=f"{suite} - Pass Percentage Trend")
    st.plotly_chart(trend, use_container_width=True)

    st.subheader("📅 Execution History")
    st.dataframe(filtered)
else:
    st.info("No results found. Run outlook_reader.py to load test reports.")
