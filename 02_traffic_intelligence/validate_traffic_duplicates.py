
import sqlite3
from pathlib import Path

database_path = (
    Path(__file__).resolve().parent.parent
    / "database"
    / "citysense.db"
)

connection = sqlite3.connect(database_path)
cursor = connection.cursor()

query = """
SELECT
    city,
    fetched_at,
    incident_id,
    COUNT(*) AS records
FROM traffic_incidents
WHERE incident_id IS NOT NULL
GROUP BY city, fetched_at, incident_id
HAVING COUNT(*) > 1
ORDER BY records DESC
LIMIT 10
"""

duplicates = cursor.execute(query).fetchall()

total_query = """
SELECT COUNT(*)
FROM (
    SELECT city, fetched_at, incident_id
    FROM traffic_incidents
    WHERE incident_id IS NOT NULL
    GROUP BY city, fetched_at, incident_id
    HAVING COUNT(*) > 1
)
"""

total_groups = cursor.execute(total_query).fetchone()[0]

print("=" * 50)
print("TRAFFIC DUPLICATE VALIDATION")
print("=" * 50)
print("Duplicate examples:")

if duplicates:
    for row in duplicates:
        print(row)
else:
    print("No duplicate incident IDs found.")

print(f"\nTotal duplicate groups: {total_groups}")

connection.close()