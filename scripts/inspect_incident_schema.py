import sqlite3

connection = sqlite3.connect("database/citysense.db")

for table_name in ["traffic_incidents", "cities"]:
    print("\nTABLE:", table_name)
    print("-" * 50)

    columns = connection.execute(
        "PRAGMA table_info(" + table_name + ")"
    ).fetchall()

    for column in columns:
        print(column[1], "-", column[2])

    count = connection.execute(
        "SELECT COUNT(*) FROM " + table_name
    ).fetchone()[0]

    print("Total records:", count)

connection.close()
