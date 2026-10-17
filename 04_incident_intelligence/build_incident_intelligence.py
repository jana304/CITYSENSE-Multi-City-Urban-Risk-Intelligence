
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "citysense.db"
OUTPUT_DIR = PROJECT_DIR / "04_incident_intelligence" / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "incident_intelligence.csv"
CITY_SUMMARY_FILE = OUTPUT_DIR / "incident_city_summary.csv"
CATEGORY_SUMMARY_FILE = OUTPUT_DIR / "incident_category_summary.csv"


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        df = pd.read_sql_query(
            """
            SELECT
                city,
                fetched_at,
                incident_id,
                category,
                magnitude_of_delay,
                start_time,
                end_time,
                from_road,
                to_road,
                length_in_meters,
                delay_in_seconds,
                time_validity,
                probability_of_occurrence,
                number_of_reports,
                last_report_time,
                geometry_type,
                coordinates
            FROM traffic_incidents
            """,
            connection,
        )

    if df.empty:
        raise ValueError("No traffic incidents found in the database.")

    original_count = len(df)

    # Standardize text fields.
    text_columns = [
        "city", "incident_id", "category", "magnitude_of_delay",
        "from_road", "to_road", "time_validity", "geometry_type"
    ]

    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()

    # Parse timestamps. Missing timestamps remain missing.
    df["fetched_at"] = pd.to_datetime(
        df["fetched_at"], errors="coerce", utc=True
    )
    df["start_time"] = pd.to_datetime(
        df["start_time"], errors="coerce", utc=True
    )
    df["end_time"] = pd.to_datetime(
        df["end_time"], errors="coerce", utc=True
    )
    df["last_report_time"] = pd.to_datetime(
        df["last_report_time"], errors="coerce", utc=True
    )

    # Convert numeric columns safely.
    numeric_columns = [
        "length_in_meters",
        "delay_in_seconds",
        "probability_of_occurrence",
        "number_of_reports",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # One row per incident in each captured snapshot.
    df = df.drop_duplicates(
        subset=["city", "fetched_at", "incident_id"],
        keep="last",
    )

    # Determine whether an incident appeared in one or multiple snapshots.
    snapshot_counts = (
        df.groupby(["city", "incident_id"])["fetched_at"]
        .nunique()
        .rename("observed_snapshot_count")
        .reset_index()
    )

    df = df.merge(
        snapshot_counts,
        on=["city", "incident_id"],
        how="left",
        validate="many_to_one",
    )

    df["repeat_observation_flag"] = (
        df["observed_snapshot_count"] > 1
    ).astype(int)

    # These labels describe evidence in the captured data, not guaranteed
    # real-world status between API snapshots.
    df["observed_status"] = "OBSERVED"
    df.loc[df["end_time"].notna(), "observed_status"] = "END_TIME_RECORDED"
    df.loc[
        df["time_validity"].str.lower().eq("present").fillna(False),
        "observed_status",
    ] = "REPORTED_PRESENT_IN_SNAPSHOT"

    # Map raw categories to readable business categories.
    category_map = {
        "jam": "Traffic Congestion",
        "roadclosed": "Road Closure",
        "roadworks": "Roadworks",
    }

    df["incident_type"] = (
        df["category"].str.lower().map(category_map).fillna("Other")
    )

    # Transparent priority score based on available signals.
    # This is a rule-based score, not a trained ML prediction.
    score = pd.Series(0, index=df.index, dtype="int64")

    category_points = {
        "jam": 25,
        "roadclosed": 40,
        "roadworks": 15,
    }
    score += df["category"].str.lower().map(category_points).fillna(10).astype(int)

    severity_points = {
        "minor": 10,
        "moderate": 20,
        "major": 30,
        "critical": 40,
    }
    score += (
        df["magnitude_of_delay"]
        .str.lower()
        .map(severity_points)
        .fillna(5)
        .astype(int)
    )

    delay = df["delay_in_seconds"].fillna(0)
    score += (delay >= 60).astype(int) * 5
    score += (delay >= 300).astype(int) * 5
    score += (delay >= 900).astype(int) * 5

    length_km = df["length_in_meters"].fillna(0) / 1000
    score += (length_km >= 1).astype(int) * 5
    score += (length_km >= 5).astype(int) * 5

    df["priority_score"] = score.clip(upper=100)

    df["priority_level"] = "LOW"
    df.loc[df["priority_score"] >= 35, "priority_level"] = "MEDIUM"
    df.loc[df["priority_score"] >= 55, "priority_level"] = "HIGH"
    df.loc[df["priority_score"] >= 75, "priority_level"] = "CRITICAL"

    # Keep the latest snapshot separately for current-view summaries.
    latest_snapshot = df["fetched_at"].max()
    latest = df[df["fetched_at"] == latest_snapshot].copy()

    # Convert timestamps to readable UTC strings for CSV export.
    for column in ["fetched_at", "start_time", "end_time", "last_report_time"]:
        df[column] = df[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        latest[column] = latest[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    df.to_csv(OUTPUT_FILE, index=False)

    city_summary = (
        latest.groupby("city", dropna=False)
        .agg(
            incidents=("incident_id", "nunique"),
            high_or_critical=("priority_level", lambda s: s.isin(["HIGH", "CRITICAL"]).sum()),
            critical_incidents=("priority_level", lambda s: (s == "CRITICAL").sum()),
            average_priority_score=("priority_score", "mean"),
            road_closures=("incident_type", lambda s: (s == "Road Closure").sum()),
        )
        .reset_index()
    )
    city_summary["average_priority_score"] = (
        city_summary["average_priority_score"].round(2)
    )
    city_summary.to_csv(CITY_SUMMARY_FILE, index=False)

    category_summary = (
        latest.groupby(["city", "incident_type"], dropna=False)
        .size()
        .reset_index(name="incident_count")
    )
    category_summary.to_csv(CATEGORY_SUMMARY_FILE, index=False)

    print("CITYSENSE AI - INCIDENT INTELLIGENCE")
    print("=" * 45)
    print(f"Source rows: {original_count}")
    print(f"Rows after snapshot deduplication: {len(df)}")
    print(f"Latest snapshot time (UTC): {latest_snapshot}")
    print(f"Latest snapshot records: {len(latest)}")
    print(f"Repeat-observed incident records: {int(df['repeat_observation_flag'].sum())}")
    print("\nPriority distribution in latest snapshot:")
    print(latest["priority_level"].value_counts().to_string())
    print("\nCity summary:")
    print(city_summary.to_string(index=False))
    print("\nCreated files:")
    print(OUTPUT_FILE)
    print(CITY_SUMMARY_FILE)
    print(CATEGORY_SUMMARY_FILE)


if __name__ == "__main__":
    main()