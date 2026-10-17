import sqlite3
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# CITYSENSE AI - TRAFFIC INCIDENT DATABASE LOADER
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_DIR / "database" / "citysense.db"

RAW_DATA_DIR = (
    PROJECT_DIR
    / "02_traffic_intelligence"
    / "data"
    / "raw"
)

TABLE_NAME = "traffic_incidents"


def main():
    # Find the most recent traffic collection file.
    csv_files = sorted(
        RAW_DATA_DIR.glob("traffic_incidents_*.csv"),
        key=lambda path: path.stat().st_mtime,
    )

    if not csv_files:
        print("ERROR: No traffic incident CSV files found.")
        return

    csv_path = csv_files[-1]

    print(f"Reading CSV: {csv_path.name}")

    df = pd.read_csv(csv_path)

    if df.empty:
        print("No traffic records to load.")
        return

    required_columns = [
        "city",
        "fetched_at",
        "incident_id",
        "category",
        "magnitude_of_delay",
        "start_time",
        "end_time",
        "from_road",
        "to_road",
        "length_in_meters",
        "delay_in_seconds",
        "road_numbers",
        "time_validity",
        "probability_of_occurrence",
        "number_of_reports",
        "last_report_time",
        "geometry_type",
        "coordinates",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print("ERROR: CSV is missing required columns:")
        print(missing_columns)
        return

    # Keep only the expected database columns.
    df = df[required_columns].copy()

    # Convert blank strings into proper missing values.
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    # Open the existing database.
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        # Create only the new traffic table.
        # Existing tables remain untouched.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_incidents (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                incident_id TEXT,
                category TEXT,
                magnitude_of_delay TEXT,
                start_time TEXT,
                end_time TEXT,
                from_road TEXT,
                to_road TEXT,
                length_in_meters REAL,
                delay_in_seconds REAL,
                road_numbers TEXT,
                time_validity TEXT,
                probability_of_occurrence REAL,
                number_of_reports INTEGER,
                last_report_time TEXT,
                geometry_type TEXT,
                coordinates TEXT,
                UNIQUE(city, fetched_at, incident_id)
            )
        """)

        # Insert new records without duplicating the same
        # incident within the same city and collection time.
        insert_sql = """
            INSERT INTO traffic_incidents (
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
                road_numbers,
                time_validity,
                probability_of_occurrence,
                number_of_reports,
                last_report_time,
                geometry_type,
                coordinates
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(city, fetched_at, incident_id) DO NOTHING
        """

        # Replace pandas missing values with SQLite-compatible NULL.
        records = [
            tuple(
                None if pd.isna(value) else value
                for value in row
            )
            for row in df.itertuples(index=False, name=None)
        ]

        cursor.executemany(insert_sql, records)
        inserted_rows = cursor.rowcount

        connection.commit()

        total_rows = cursor.execute(
            "SELECT COUNT(*) FROM traffic_incidents"
        ).fetchone()[0]

        print("\nDATABASE LOAD SUMMARY")
        print("=" * 40)
        print(f"Source CSV records: {len(df)}")
        print(f"New records inserted: {inserted_rows}")
        print(f"Total database records: {total_rows}")

        print("\nRecords by city:")
        for city, count in cursor.execute("""
            SELECT city, COUNT(*)
            FROM traffic_incidents
            GROUP BY city
            ORDER BY city
        """).fetchall():
            print(f"{city}: {count}")

        print("\nTraffic categories:")
        for category, count in cursor.execute("""
            SELECT category, COUNT(*)
            FROM traffic_incidents
            GROUP BY category
            ORDER BY COUNT(*) DESC
        """).fetchall():
            print(f"{category}: {count}")

    print("\nTraffic data loaded successfully.")


if __name__ == "__main__":
    main()
