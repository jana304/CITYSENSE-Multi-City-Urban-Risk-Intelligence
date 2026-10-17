import sqlite3
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# CITYSENSE AI - TRAFFIC RISK SCORING
# Transparent, rule-based incident prioritisation
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_DIR / "database" / "citysense.db"

OUTPUT_DIR = (
    PROJECT_DIR
    / "02_traffic_intelligence"
    / "data"
    / "processed"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_traffic_data():
    """Load traffic incidents from SQLite."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        df = pd.read_sql_query(
            """
            SELECT *
            FROM traffic_incidents
            """,
            connection,
        )

    if df.empty:
        raise ValueError("No traffic incidents found in SQLite.")

    return df


def calculate_risk_score(df):
    """Calculate an explainable rule-based risk score."""

    df = df.copy()

    # Initialise scores.
    df["risk_score"] = 0
    df["risk_reasons"] = ""

    # Rule 1: Incident category.
    category_points = {
        "jam": 25,
        "roadClosed": 40,
        "roadWorks": 15,
    }

    df["category_points"] = (
        df["category"]
        .map(category_points)
        .fillna(10)
        .astype(int)
    )

    df["risk_score"] += df["category_points"]

    # Rule 2: Reported severity.
    severity_points = {
        "minor": 10,
        "moderate": 20,
        "major": 30,
        "critical": 40,
        "undefined": 5,
    }

    severity = (
        df["magnitude_of_delay"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    df["severity_points"] = (
        severity.map(severity_points)
        .fillna(5)
        .astype(int)
    )

    df["risk_score"] += df["severity_points"]

    # Rule 3: Reported delay.
    delay = pd.to_numeric(
        df["delay_in_seconds"],
        errors="coerce",
    )

    df["delay_points"] = 0

    df.loc[
        delay.ge(60) & delay.lt(300),
        "delay_points",
    ] = 5

    df.loc[
        delay.ge(300) & delay.lt(900),
        "delay_points",
    ] = 10

    df.loc[
        delay.ge(900),
        "delay_points",
    ] = 15

    df["risk_score"] += df["delay_points"]

    # Rule 4: Road length, if supplied.
    road_length = pd.to_numeric(
        df["length_in_meters"],
        errors="coerce",
    )

    df["length_points"] = 0

    df.loc[
        road_length.ge(1000) & road_length.lt(5000),
        "length_points",
    ] = 5

    df.loc[
        road_length.ge(5000),
        "length_points",
    ] = 10

    df["risk_score"] += df["length_points"]

    # Cap scores at 100.
    df["risk_score"] = df["risk_score"].clip(0, 100)

    # Assign operational priority bands.
    df["risk_level"] = "LOW"

    df.loc[
        df["risk_score"].ge(35),
        "risk_level",
    ] = "MEDIUM"

    df.loc[
        df["risk_score"].ge(55),
        "risk_level",
    ] = "HIGH"

    df.loc[
        df["risk_score"].ge(75),
        "risk_level",
    ] = "CRITICAL"

    # Explain why each record received its score.
    for index, row in df.iterrows():
        reasons = []

        if row["category_points"] >= 40:
            reasons.append("Road closure")
        elif row["category"] == "jam":
            reasons.append("Traffic jam")
        elif row["category"] == "roadWorks":
            reasons.append("Roadworks")

        if row["severity_points"] >= 30:
            reasons.append("High reported severity")

        if row["delay_points"] > 0:
            reasons.append("Reported delay")

        if row["length_points"] > 0:
            reasons.append("Long affected road segment")

        if not reasons:
            reasons.append("Limited reported risk indicators")

        df.at[index, "risk_reasons"] = "; ".join(reasons)

    # Suggested action based on incident category and risk.
    def recommend_action(row):
        if row["category"] == "roadClosed":
            return "Verify closure and identify an alternative route"

        if row["risk_level"] == "CRITICAL":
            return "Urgently verify incident and assess traffic impact"

        if row["risk_level"] == "HIGH":
            return "Prioritise review and monitor traffic conditions"

        if row["category"] == "jam":
            return "Monitor congestion and consider route alternatives"

        if row["category"] == "roadWorks":
            return "Check work-zone traffic management"

        return "Continue monitoring and validate incident details"

    df["recommended_action"] = df.apply(
        recommend_action,
        axis=1,
    )

    return df


def create_city_risk_summary(df):
    """Summarise scores and priority counts by city."""

    summary = (
        df.groupby("city")
        .agg(
            total_incidents=("record_id", "count"),
            average_risk_score=("risk_score", "mean"),
            maximum_risk_score=("risk_score", "max"),
            high_risk_incidents=(
                "risk_level",
                lambda s: s.isin(["HIGH", "CRITICAL"]).sum(),
            ),
            critical_incidents=(
                "risk_level",
                lambda s: s.eq("CRITICAL").sum(),
            ),
            road_closures=(
                "category",
                lambda s: s.eq("roadClosed").sum(),
            ),
        )
        .reset_index()
    )

    summary["average_risk_score"] = (
        summary["average_risk_score"].round(2)
    )

    return summary.sort_values(
        "average_risk_score",
        ascending=False,
    )


def create_priority_summary(df):
    """Count incidents in each priority band."""

    summary = (
        df.groupby(["city", "risk_level"])
        .size()
        .reset_index(name="incident_count")
    )

    return summary.sort_values(
        ["city", "incident_count"],
        ascending=[True, False],
    )


def main():
    print("=" * 60)
    print("CITYSENSE AI - TRAFFIC RISK SCORING")
    print("=" * 60)

    df = load_traffic_data()
    scored_df = calculate_risk_score(df)

    # Detailed scored incidents.
    detail_columns = [
        "city",
        "fetched_at",
        "incident_id",
        "category",
        "magnitude_of_delay",
        "delay_in_seconds",
        "from_road",
        "to_road",
        "risk_score",
        "risk_level",
        "risk_reasons",
        "recommended_action",
    ]

    details = scored_df[detail_columns].sort_values(
        ["risk_score", "city"],
        ascending=[False, True],
    )

    details.to_csv(
        OUTPUT_DIR / "traffic_risk_scores.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # City-level risk summary.
    city_summary = create_city_risk_summary(scored_df)

    city_summary.to_csv(
        OUTPUT_DIR / "traffic_city_risk_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Priority distribution.
    priority_summary = create_priority_summary(scored_df)

    priority_summary.to_csv(
        OUTPUT_DIR / "traffic_priority_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(f"\nIncidents scored: {len(scored_df)}")

    print("\nRisk-level distribution:")
    print(
        scored_df["risk_level"]
        .value_counts()
        .to_string()
    )

    print("\nCity risk summary:")
    print(city_summary.to_string(index=False))

    print("\nHighest-priority incidents:")
    print(
        details[
            [
                "city",
                "category",
                "risk_score",
                "risk_level",
                "risk_reasons",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nCreated reports:")
    print("- traffic_risk_scores.csv")
    print("- traffic_city_risk_summary.csv")
    print("- traffic_priority_summary.csv")

    print(f"\nOutput folder: {OUTPUT_DIR}")
    print("\nTraffic risk scoring completed.")


if __name__ == "__main__":
    main()
