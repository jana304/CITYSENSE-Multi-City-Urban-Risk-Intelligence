
from pathlib import Path
import pandas as pd

# CITYSENSE AI - Scope 06: Forecasting and Early Warnings

ROOT = Path(__file__).resolve().parents[1]

WEATHER_RISK = ROOT / "data" / "processed" / "weather_risk_assessments.csv"
AQ_RISK = (
    ROOT / "05_air_quality_intelligence" / "data" / "processed"
    / "air_quality_risk_assessments.csv"
)
INCIDENTS = (
    ROOT / "04_incident_intelligence" / "data" / "processed"
    / "incident_city_summary.csv"
)

OUTPUT_DIR = ROOT / "06_forecasting_early_warnings" / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "city_early_warnings.csv"


def load_csv(path, label):
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"{label} file contains no records: {path}")

    return df


def risk_points(value):
    """Convert an existing risk category into transparent score points."""
    value = str(value).strip().upper()

    mapping = {
        "LOW": 0,
        "MODERATE": 25,
        "MEDIUM": 25,
        "HIGH": 60,
        "UNHEALTHY FOR SENSITIVE GROUPS": 40,
        "UNHEALTHY": 60,
        "VERY UNHEALTHY": 80,
        "HAZARDOUS": 100,
        "CRITICAL": 100,
    }

    return mapping.get(value, 0)


def incident_pressure(row):
    """Estimate current incident pressure using the city summary."""
    total = max(float(row.get("incidents", 0) or 0), 0)
    serious = max(float(row.get("high_or_critical", 0) or 0), 0)
    critical = max(float(row.get("critical_incidents", 0) or 0), 0)

    if total <= 0:
        return 0

    serious_rate = serious / total
    critical_rate = critical / total

    # Project-defined score; this is not an official traffic risk score.
    score = (serious_rate * 70) + (critical_rate * 30)
    return round(min(score, 100), 2)


def combined_level(score):
    if score >= 70:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def main():
    weather = load_csv(WEATHER_RISK, "Weather risk")
    air = load_csv(AQ_RISK, "Air-quality risk")
    incidents = load_csv(INCIDENTS, "Incident city summary")

    required_weather = {
        "city", "horizon_hours", "weather_risk_score",
        "weather_risk_level", "risk_reasons", "recommended_actions"
    }
    required_air = {
        "city", "horizon_hours", "air_quality_risk_level",
        "risk_explanation", "recommended_action"
    }
    required_incidents = {
        "city", "incidents", "high_or_critical", "critical_incidents"
    }

    for label, df, required in [
        ("Weather risk", weather, required_weather),
        ("Air-quality risk", air, required_air),
        ("Incident summary", incidents, required_incidents),
    ]:
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"{label} file is missing columns: {sorted(missing)}"
            )

    # Use the newest available incident summary per city.
    incident_map = {}
    for _, row in incidents.iterrows():
        incident_map[str(row["city"]).strip().lower()] = row

    # Match weather and air-quality forecasts by city and forecast horizon.
    merged = pd.merge(
        weather,
        air,
        on=["city", "horizon_hours"],
        how="inner",
        suffixes=("_weather", "_air"),
    )

    if merged.empty:
        raise ValueError(
            "No matching city and forecast-horizon records found "
            "between weather and air-quality data."
        )

    results = []

    for _, row in merged.iterrows():
        city = str(row["city"]).strip()
        city_key = city.lower()
        horizon = int(row["horizon_hours"])

        weather_score = max(
            0, min(float(row["weather_risk_score"]), 100)
        )
        weather_level = str(row["weather_risk_level"]).strip().upper()

        air_level = str(row["air_quality_risk_level"]).strip().upper()
        air_score = risk_points(air_level)

        incident_row = incident_map.get(city_key)

        if incident_row is None:
            traffic_score = 0
            incident_count = 0
            serious_count = 0
            critical_count = 0
            traffic_note = "No matching city incident summary available"
        else:
            traffic_score = incident_pressure(incident_row)
            incident_count = int(incident_row["incidents"])
            serious_count = int(incident_row["high_or_critical"])
            critical_count = int(incident_row["critical_incidents"])
            traffic_note = (
                f"{serious_count} high/critical incidents among "
                f"{incident_count} incidents in the incident summary"
            )

        # Combined score: weather 35%, air quality 40%, incidents 25%.
        combined_score = round(
            (weather_score * 0.35)
            + (air_score * 0.40)
            + (traffic_score * 0.25),
            2,
        )

        reasons = []

        if weather_score >= 35:
            reasons.append(
                f"Weather risk is {weather_level} "
                f"(score {weather_score:.1f})"
            )

        if air_score >= 25:
            reasons.append(f"Air quality is {air_level}")

        if traffic_score >= 35:
            reasons.append(
                f"Elevated incident pressure (score {traffic_score:.1f})"
            )

        if not reasons:
            reasons.append(
                "No high combined-risk signal under configured project rules"
            )

        actions = []

        if weather_score >= 35:
            actions.append(str(row["recommended_actions"]))

        if air_score >= 25:
            actions.append(str(row["recommended_action"]))

        if traffic_score >= 35:
            actions.append(
                "Check current traffic and incident information before travel"
            )

        if not actions:
            actions.append("Continue monitoring updated city conditions")

        results.append({
            "city": city,
            "horizon_hours": horizon,
            "target_time": row.get("target_time_weather", row.get("target_time", "")),
            "weather_risk_score": round(weather_score, 2),
            "weather_risk_level": weather_level,
            "air_quality_risk_level": air_level,
            "air_quality_score_points": air_score,
            "incident_count_in_summary": incident_count,
            "high_or_critical_incidents": serious_count,
            "critical_incidents": critical_count,
            "incident_pressure_score": traffic_score,
            "combined_risk_score": combined_score,
            "combined_risk_level": combined_level(combined_score),
            "warning_reasons": " | ".join(reasons),
            "recommended_actions": " | ".join(dict.fromkeys(actions)),
            "traffic_context": traffic_note,
            "reference_time_weather": row.get("reference_time_weather", ""),
            "reference_time_air": row.get("reference_time_air", ""),
            "data_note": (
                "Weather and air-quality outlooks are forecast-based; "
                "incident pressure is based on the available incident summary."
            ),
        })

    output = pd.DataFrame(results)
    output = output.sort_values(
        ["horizon_hours", "combined_risk_score"],
        ascending=[True, False],
    )

    output.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("=" * 60)
    print("CITYSENSE AI - EARLY WARNING REPORT")
    print("=" * 60)
    print(f"Warnings generated: {len(output)}")
    print(f"Cities covered: {output['city'].nunique()}")
    print("\nRisk levels:")
    print(output["combined_risk_level"].value_counts().to_string())
    print("\nPreview:")
    print(
        output[
            [
                "city",
                "horizon_hours",
                "combined_risk_score",
                "combined_risk_level",
                "warning_reasons",
            ]
        ].to_string(index=False)
    )
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()