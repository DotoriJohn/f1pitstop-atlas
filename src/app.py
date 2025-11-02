import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title="Pit stop leaderboard", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
TEAM = Path("data/clean/pit_metrics_team.csv")

if not TEAM.exists():
    st.error("Metrics not found. Run the pitstop_leaderboard.py script first")
    st.stop()


team = pd.read_csv(TEAM)

st.title("F1 Team Pit-stop leaderboard 2024-2025")

seasons = sorted(team["Season"].unique())
sel_season = st.sidebar.selectbox("Season", seasons, index = len(seasons)-1)

st.subheader(f"Team Leaderboard - {sel_season}")

# filter selected season
t = team[team["Season"] == sel_season].copy()

t = t.rename(columns={
    "Consistency (p95-Median)": "Consistency (P95-Median)",
    "P95(s)": "P95 (s)",
    "Std Dev(s)": "Std Dev (s)"
})

# If consistency column doesn’t exist yet but ingredients do, create it
if "Consistency (P95-Median)" not in t.columns and {"P95 (s)", "Median (s)"} <= set(t.columns):
    t["Consistency (P95-Median)"] = t["P95 (s)"] - t["Median (s)"]

required_cols = {"Team", "Average (s)", "Median (s)", "P95 (s)", "Stops"}
if not required_cols.issubset(set(t.columns)):
    st.error(f"Missing columns in metrics: {required_cols - set(t.columns)}. "
             "Re-run the data build script.")
    st.stop()

# rankings
t_avg = t.sort_values("Average (s)").reset_index(drop=True)
t_avg.insert(0, "Rank (Avg)", t_avg.index+1)

t_cons = t.sort_values("Consistency (P95-Median)").reset_index(drop=True)
t_cons.insert(0, "Rank (Consistency)", t_cons.index+1)

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Fastest Average — {sel_season} (lower is better)")
    st.dataframe(t_avg[["Rank (Avg)", "Team", "Average (s)", "Median (s)", "P95 (s)", "Stops"]],
        use_container_width=True)
with col2:
    st.subheader(f"Most Consistent — {sel_season} (lower is better)")
    st.caption("Consistency = P95 - Median (smaller gap → fewer slow outliers)")
    st.dataframe(t_cons[["Rank (Consistency)", "Team", "Consistency (P95-Median)", "Median (s)", "P95 (s)", "Stops"]],
        use_container_width=True)

st.divider()
st.subheader("Average Pit Time by Team (selected season)")

# Bar chart
fig = px.bar(t.sort_values("Average (s)"), x="Team", y="Average (s)", title="Average Pit-Stop Time (s) - Tyre changes only")
st.plotly_chart(fig, use_container_width=True)

