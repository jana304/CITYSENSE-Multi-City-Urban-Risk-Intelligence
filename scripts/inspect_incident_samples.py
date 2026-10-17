import sqlite3

connection = sqlite3.connect("database/citysense.db")

query = """
SELECT city, incident_id, category, start_time, end_time,
       from_road, to_road, number_of_reports,
       geometry_type, coordinates, fetched_at
FROM traffic_incidents
ORDER BY fetched_at DESC
LIMIT 8
"""

for row in connection.execute(query):
    print("-" * 60)
    for column, value in zip(
        ["city", "incident_id", "category", "start_time",
         "end_time", "from_road", "to_road", "reports",
         "geometry_type", "coordinates", "fetched_at"],
        row
    ):
        print(f"{column}: {value}")

connection.close()
