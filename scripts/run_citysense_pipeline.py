
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

STEPS = [
    {
        "name": "Step 1 - Collect current weather",
        "script": "01_weather_intelligence/collect_weather.py",
        "outputs": ["data/raw/weather_snapshot_*.csv"],
    },
    {
        "name": "Step 2 - Collect hourly weather forecasts",
        "script": "01_weather_intelligence/collect_hourly_forecasts.py",
        "outputs": ["data/raw/weather_hourly_forecast_*.csv"],
    },
    {
        "name": "Step 3 - Load current weather",
        "script": "01_weather_intelligence/load_weather_to_sqlite.py",
    },
    {
        "name": "Step 4 - Load hourly weather forecasts",
        "script": "01_weather_intelligence/load_hourly_forecasts.py",
    },
    {
        "name": "Step 5 - Create weather outlook",
        "script": "01_weather_intelligence/create_weather_outlook.py",
    },
    {
        "name": "Step 6 - Create weather risk assessments",
        "script": "03_weather_disruption_risk/create_weather_risk_assessments.py",
    },
    {
        "name": "Step 7 - Collect traffic incidents",
        "script": "02_traffic_intelligence/collect_traffic_incidents.py",
        "outputs": ["02_traffic_intelligence/data/raw/traffic_incidents_*.csv"],
    },
    {
        "name": "Step 8 - Load traffic incidents",
        "script": "02_traffic_intelligence/load_traffic_incidents_to_sqlite.py",
    },
    {
        "name": "Step 9 - Create traffic analytics",
        "script": "02_traffic_intelligence/create_traffic_analytics.py",
    },
    {
        "name": "Step 10 - Create traffic risk scores",
        "script": "02_traffic_intelligence/create_traffic_risk_scores.py",
    },
    {
        "name": "Step 11 - Collect air quality data",
        "script": "05_air_quality_intelligence/collect_air_quality.py",
        "outputs": [
            "05_air_quality_intelligence/data/raw/air_quality_snapshot_*.csv",
            "05_air_quality_intelligence/data/raw/air_quality_hourly_forecast_*.csv",
        ],
    },
    {
        "name": "Step 12 - Load air quality data",
        "script": "05_air_quality_intelligence/load_air_quality_to_sqlite.py",
    },
    {
        "name": "Step 13 - Create air quality outlook",
        "script": "05_air_quality_intelligence/create_air_quality_outlook.py",
    },
    {
        "name": "Step 14 - Create air quality risk assessments",
        "script": "05_air_quality_intelligence/create_air_quality_risk_assessments.py",
    },
    
    {
        "name": "Step 15 - Build incident intelligence",
        "script": "04_incident_intelligence/build_incident_intelligence.py",
    },
    {
        "name": "Step 16 - Build forecasting and early warnings",
        "script": "06_forecasting_early_warnings/build_early_warnings.py",
    },
]

def get_output_files(patterns):
    files = set()
    for pattern in patterns:
        files.update(PROJECT_DIR.glob(pattern))
    return files


def run_pipeline():
    started_at = datetime.now()

    print("=" * 65)
    print("CITYSENSE AI - CENTRAL DATA PIPELINE")
    print(f"Started: {started_at.isoformat(timespec='seconds')}")
    print("=" * 65)

    completed = 0

    for step in STEPS:
        step_name = step["name"]
        script_path = PROJECT_DIR / step["script"]
        output_patterns = step.get("outputs", [])

        print(f"\n{'-' * 65}")
        print(step_name)
        print(f"Script: {step['script']}")
        print("-" * 65)

        if not script_path.is_file():
            print(f"ERROR: Script not found: {script_path}")
            return 1

        # Remember existing files so old CSVs cannot satisfy validation.
        previous_files = get_output_files(output_patterns)

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_DIR,
            check=False,
        )

        if result.returncode != 0:
            print(f"\nERROR: {step_name} failed.")
            print(f"Exit code: {result.returncode}")
            print("Pipeline stopped.")
            return result.returncode or 1

        if output_patterns:
            current_files = get_output_files(output_patterns)
            new_files = current_files - previous_files

            if not new_files:
                print("ERROR: No new CSV output was detected.")
                print("The collector may have failed or produced no data.")
                print("Pipeline stopped to protect downstream steps.")
                return 1

            for file_path in sorted(new_files):
                print(f"Verified new output: {file_path.relative_to(PROJECT_DIR)}")

        completed += 1
        print(f"SUCCESS: {step_name}")

    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()

    print("\n" + "=" * 65)
    print("PIPELINE FINISHED")
    print(f"Steps completed: {completed}/{len(STEPS)}")
    print(f"Started: {started_at.isoformat(timespec='seconds')}")
    print(f"Finished: {finished_at.isoformat(timespec='seconds')}")
    print(f"Duration: {duration:.1f} seconds")
    print("=" * 65)

    return 0


if __name__ == "__main__":
    raise SystemExit(run_pipeline())