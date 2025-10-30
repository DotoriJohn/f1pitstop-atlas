import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title="Pit stop leaderboard (FastF1)", layout="wide")

TEAM = Path("data/clean/pit_metrics_team.csv")
DRIVER = Path("data/clean/pit_metrics_driver.csv")

if not TEAM.exists() or not DRIVER.exists():
    st.error("Metrics not found. Run the pitstop_leaderboard_fastf1.py script first")
    st.stop()


team = pd.read_csv(TEAM)
driver = pd.read_csv(DRIVER)

st.title("Pit stop leaderboard 2024-2025")

seasons = sorted(team["season"].unique())
sel_season = st.sidebar.selectbox("Season", seasons, index = len(seasons)-1)

st.subheader(f"Team Leaderboard - {sel_season}")
t = team[team["season"] == sel_season]
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Fastest Average(lower is better)**")
    st.dataframe(t.sort_values("avg_s").reset_index(drop=True), use_container_width=True)
with col2:
    st.markdown("**Most Consistent(lowest p95 - median)**")
    st.dataframe(t.sort_values("consistency_score").reset_index(drop=True), use_container_width=True)

st.divider()
st.subheader("Average Pit Time by Team (selected season)")
fig = px.bar(t.sort_values("avg_s"), x="Team", y="avg_s", title="Average Pit-Stop Time (s)")
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Driver View")
drivers = sorted(driver[driver["season"] == sel_season]["Driver"].unique())
sel_driver = st.selectbox("Driver", drivers)
d = driver[(driver["season"] == sel_season) & (driver["Driver"] == sel_driver)]
st.dataframe(d.sort_values("avg_s").reset_index(drop=True), use_container_width=True)