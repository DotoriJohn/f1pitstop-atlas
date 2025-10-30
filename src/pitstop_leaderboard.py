# src/pitstop_leaderboard.py
import argparse
from pathlib import Path
import pandas as pd
import fastf1

def enable_cache(cache_dir: Path):
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))

def list_event_names(year: int) -> list[str]:
    sched = fastf1.get_event_schedule(year, include_testing=False).reset_index(drop=False)
    return sched["EventName"].dropna().unique().tolist()

def pit_events_for_race(year: int, gp_name: str) -> pd.DataFrame:
    s = fastf1.get_session(year, gp_name, "R")
    s.load()
    laps = s.laps.copy()

    # Per driver, align PitIn (this lap) with PitOut (next Lap)
    laps = laps.sort_values(["DriverNumber", "LapNumber"]).copy()
    laps["NextPitOutTime"] = laps.groupby("DriverNumber")["PitOutTime"].shift(-1)
    
    pit_laps = laps[laps["PitInTime"].notna()].copy()
    pit_laps["duration_s"] = (pit_laps["NextPitOutTime"] - pit_laps["PitInTime"]).dt.total_seconds()

    pit_laps["season"] = year
    pit_laps["race_name"] = gp_name
    pit_laps = pit_laps.rename(columns={"LapNumber": "LapIn"})

    return pit_laps[[
        "season", "race_name",
        "Driver", "DriverNumber", "Team",
        "LapIn", "duration_s"
    ]]

    # pit_in = laps[laps["PitInTime"].notna()][["Driver","DriverNumber","Team","LapNumber","PitInTime"]]
    # pit_in = pit_in.rename(columns={"LapNumber":"LapIn"})

    # pit_out = laps[laps["PitOutTime"].notna()][["Driver","DriverNumber","Team","LapNumber","PitOutTime"]]
    # pit_out = pit_out.rename(columns={"LapNumber":"LapOut"})

    # pit = pd.merge(pit_in, pit_out, on=["Driver","DriverNumber","Team"], how="inner")
    # pit = pit[pit["LapOut"] == pit["LapIn"] + 1].copy()

    # pit["duration_s"] = (pit["PitOutTime"] - pit["PitInTime"]).dt.total_seconds()
    # pit = pit[(pit["duration_s"] > 1.5) & (pit["duration_s"] < 25.0)]
    # pit["season"] = year
    # pit["race_name"] = gp_name

    # return pit[["season","race_name","Driver","DriverNumber","Team","LapIn","LapOut","duration_s"]]

def build_team_metrics(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["season","Team"])["duration_s"]
    out = pd.DataFrame({
        "n_stops": g.size(),
        "avg_s": g.mean(),
        "median_s": g.median(),
        "p90_s": g.quantile(0.90),
        "p95_s": g.quantile(0.95),
        "std_s": g.std(ddof=0),
    }).reset_index()
    out["consistency_score"] = out["p95_s"] - out["median_s"]
    out = out.sort_values(["season","avg_s"]).reset_index(drop=True)
    return out

def build_driver_metrics(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["season","Driver","Team"])["duration_s"]
    out = pd.DataFrame({
        "n_stops": g.size(),
        "avg_s": g.mean(),
        "median_s": g.median(),
        "p90_s": g.quantile(0.90),
        "p95_s": g.quantile(0.95),
        "std_s": g.std(ddof=0),
    }).reset_index()
    out["consistency_score"] = out["p95_s"] - out["median_s"]
    out = out.sort_values(["season","avg_s"]).reset_index(drop=True)
    return out

def run(start: int, end: int, raw_dir: Path, clean_dir: Path, cache_dir: Path):
    enable_cache(cache_dir)
    all_pits = []

    for year in range(start, end + 1):
        events = list_event_names(year)
        print(f"[INFO] {year}: {len(events)} scheduled events")
        for name in events:
            try:
                pits = pit_events_for_race(year, name)
            except Exception as e:
                print(f"[WARN] {year} {name}: {e}")
                continue
            if pits.empty:
                print(f"[WARN] {year} {name}: no pit events derived")
                continue
            raw_dir.mkdir(parents=True, exist_ok=True)
            out_csv = raw_dir / f"pitstops_{year}_{name.replace(' ', '_')}.csv"
            pits.to_csv(out_csv, index=False)
            print(f"[OK] {year} {name}: {len(pits)} pit events → {out_csv}")
            all_pits.append(pits)

    if not all_pits:
        print("[WARN] Nothing to aggregate.")
        return

    full = pd.concat(all_pits, ignore_index=True)
    (raw_dir / "pitstops_all.csv").write_text(full.to_csv(index=False))

    clean_dir.mkdir(parents=True, exist_ok=True)
    team = build_team_metrics(full)
    driver = build_driver_metrics(full)
    team.to_csv(clean_dir / "pit_metrics_team.csv", index=False)
    driver.to_csv(clean_dir / "pit_metrics_driver.csv", index=False)
    print(f"[OK] Wrote team/driver metrics → {clean_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pit-stop leaderboard (FastF1) for 2024–2025.")
    ap.add_argument("--start", type=int, default=2024)
    ap.add_argument("--end", type=int, default=2025)
    args = ap.parse_args()

    ROOT = Path(__file__).resolve().parents[1]
    RAW = ROOT / "data" / "raw"
    CLEAN = ROOT / "data" / "clean"
    CACHE = ROOT / ".cache_fastf1"

    run(args.start, args.end, RAW, CLEAN, CACHE)
