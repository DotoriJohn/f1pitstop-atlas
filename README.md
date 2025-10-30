# f1 pit stop leaderboard (fastf1) - 2024-2025

Python + fastf1 api pipeline that derives pit-lane time (PitOutTime - PitInTime) per stops, aggregates to team/driver metrics, and shows a streamlit dashboard

## run
python .\src\pitstop_leaderboard_fastf1.py --start 2024 --end 2025
streamlit run .\src\app.py
