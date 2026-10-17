
from pathlib import Path
import csv
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = ROOT / "data" / "processed" / "powerbi_pipeline_status.txt"
OUTPUT_FILE = ROOT / "data" / "processed" / "powerbi_refresh_status.csv"

status_text = STATUS_FILE.read_text(encoding="utf-8").strip()
parts = status_text.split(maxsplit=1)

status = parts[0] if parts else "UNKNOWN"
refresh_time = parts[1] if len(parts) > 1 else ""

with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["pipeline_status", "last_successful_refresh"])
    writer.writerow([status, refresh_time if status == "SUCCESS" else ""])
