import sqlite3
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# CITYSENSE AI - TRAFFIC ANALYTICS
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
    """Read traffic incidents from SQLite."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        df = pd.read_sql_query(
            """
            SELECT *
            FROM traffic_incidents
            """,
            connection,
        )

    if df.empty:
        raise ValueError(
            "The traffic_incidents table contains no records."
        )

    return df


def create_city_summary(df):
    """Summarise incident counts and available delays by city."""

    summary = (
        df.groupby("city", dropna=False)
        .agg(
            total_incidents=("record_id", "count"),
            traffic_jams=(
                "category",
                lambda s: s.eq("jam").sum(),
            ),
            road_closures=(
                "category",
                lambda s: s.eq("roadClosed").sum(),
            ),
            roadworks=(
                "category",
                lambda s: s.eq("roadWorks").sum(),
            ),
            incidents_with_delay=(
                "delay_in_seconds",
                "count",
            ),
            average_delay_seconds=(
                "delay_in_seconds",
                "mean",
            ),
            maximum_delay_seconds=(
                "delay_in_seconds",
                "max",
            ),
        )
        .reset_index()
    )

    summary["average_delay_seconds"] = (
        summary["average_delay_seconds"].round(2)
    )

    return summary.sort_values(
        "total_incidents", ascending=False
    )


def create_category_summary(df):
    """Count incidents by city and category."""

    summary = (
        df.groupby(
            ["city", "category"],
            dropna=False,
        )
        .size()
        .reset_index(name="incident_count")
    )

    return summary.sort_values(
        ["city", "incident_count"],
        ascending=[True, False],
    )


def create_severity_summary(df):
    """Analyse TomTom's reported delay-severity levels."""

    severity = (
        df.groupby(
            ["city", "magnitude_of_delay"],
            dropna=False,
        )
        .size()
        .reset_index(name="incident_count")
    )

    severity["magnitude_of_delay"] = (
        severity["magnitude_of_delay"]
        .fillna("Not provided")
    )

    return severity.sort_values(
        ["city", "incident_count"],
        ascending=[True, False],
    )


def create_road_closure_summary(df):
    """Summarise road closure records."""

    closures = df[
        df["category"].eq("roadClosed")
    ].copy()

    if closures.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "from_road",
                "to_road",
                "closure_records",
            ]
        )

    summary = (
        closures.groupby(
            ["city", "from_road", "to_road"],
            dropna=False,
        )
        .size()
        .reset_index(name="closure_records")
    )

    return summary.sort_values(
        "closure_records",
        ascending=False,
    )


def create_data_quality_report(df):
    """Report missing values and duplicate IDs."""

    fields = [
        "incident_id",
        "category",
        "magnitude_of_delay",
        "delay_in_seconds",
        "from_road",
        "to_road",
        "geometry_type",
        "coordinates",
    ]

    rows = []

    for field in fields:
        missing = int(df[field].isna().sum())

        rows.append(
            {
                "field": field,
                "total_records": len(df),
                "missing_records": missing,
                "missing_percentage": round(
                    missing / len(df) * 100, 2
                ),
            }
        )

    quality = pd.DataFrame(rows)

    # IDs can legitimately appear again in later snapshots.
    # This report identifies duplicate IDs within this
    # loaded dataset; it does not automatically delete them.
   
    duplicate_ids = int(
    df.duplicated(
        subset=["city", "fetched_at", "incident_id"],
        keep="first",
    )
    .where(df["incident_id"].notna(), False)
    .sum()
)

    return quality, duplicate_ids


def save_report(df, filename):
    """Save a DataFrame as a Power BI-ready CSV."""

    output_path = OUTPUT_DIR / filename

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Created: {output_path.name} ({len(df)} rows)")


def main():
    print("=" * 60)
    print("CITYSENSE AI - TRAFFIC ANALYTICS")
    print("=" * 60)

    df = load_traffic_data()

    print(f"\nDatabase records analysed: {len(df)}")
    print(f"Cities: {df['city'].nunique()}")

    # Report 1: city performance
    city_summary = create_city_summary(df)
    save_report(
        city_summary,
        "traffic_city_summary.csv",
    )

    # Report 2: incident category counts
    category_summary = create_category_summary(df)
    save_report(
        category_summary,
        "traffic_category_summary.csv",
    )

    # Report 3: reported delay severity
    severity_summary = create_severity_summary(df)
    save_report(
        severity_summary,
        "traffic_severity_summary.csv",
    )

    # Report 4: road closures and affected roads
    closure_summary = create_road_closure_summary(df)
    save_report(
        closure_summary,
        "traffic_road_closure_summary.csv",
    )

    # Report 5: data quality
    quality, duplicate_ids = create_data_quality_report(df)
    save_report(
        quality,
        "traffic_data_quality_report.csv",
    )

    # Report 6: detailed incident data
    detail_columns = [
        "city",
        "fetched_at",
        "incident_id",
        "category",
        "magnitude_of_delay",
        "delay_in_seconds",
        "from_road",
        "to_road",
        "length_in_meters",
        "start_time",
        "end_time",
        "number_of_reports",
        "geometry_type",
    ]

    save_report(
        df[detail_columns],
        "traffic_incident_details.csv",
    )

    print("\n" + "=" * 60)
    print("CITY TRAFFIC SUMMARY")
    print("=" * 60)
    print(city_summary.to_string(index=False))

    print("\n" + "=" * 60)
    print("DATA QUALITY SUMMARY")
    print("=" * 60)
    print(quality.to_string(index=False))
    print(f"\nDuplicate IDs within identical snapshots: {duplicate_ids}")

    print("\nTraffic categories:")
    print(
        df["category"]
        .fillna("Unknown")
        .value_counts()
        .to_string()
    )

    print("\nAll traffic analytics reports created successfully.")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
