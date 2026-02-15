import sqlite3
import os

DB_PATH = "sdg.db"
SCHEMA_PATH = "database/schema.sql"


def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load schema
    with open(SCHEMA_PATH, "r") as f:
        cursor.executescript(f.read())

    # -------------------------
    # Insert Goals
    # -------------------------
    goals = [
        (1, "No Poverty", "End poverty in all its forms everywhere."),
        (2, "Zero Hunger", "End hunger and achieve food security."),
        (3, "Good Health and Well-being", "Ensure healthy lives and promote well-being."),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO sdg_goal VALUES (?, ?, ?)", goals
    )

    # -------------------------
    # Insert Indicators
    # -------------------------
    indicators = [
        (1, "1.1.1", "Population below poverty line", "%"),
        (2, "2.1.1", "Prevalence of undernourishment", "%"),
        (3, "3.2.1", "Under-5 mortality rate", "per 1000"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO sdg_indicator (goal_id, indicator_code, name, unit) VALUES (?, ?, ?, ?)",
        indicators
    )

    # -------------------------
    # Insert Countries
    # -------------------------
    countries = [
        ("United Kingdom", "GBR"),
        ("Kenya", "KEN"),
        ("Germany", "DEU"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO dim_country (country_name, iso3) VALUES (?, ?)",
        countries
    )

    # -------------------------
    # Insert Years
    # -------------------------
    for year in range(2015, 2025):
        cursor.execute(
            "INSERT OR IGNORE INTO dim_period (year) VALUES (?)",
            (year,),
        )

    # -------------------------
    # Insert Sample Fact Data
    # -------------------------
    cursor.execute("SELECT country_id, iso3 FROM dim_country")
    countries_data = cursor.fetchall()

    cursor.execute("SELECT indicator_id, indicator_code FROM sdg_indicator")
    indicators_data = cursor.fetchall()

    cursor.execute("SELECT period_id, year FROM dim_period")
    periods_data = cursor.fetchall()

    for country_id, iso3 in countries_data:
        for indicator_id, code in indicators_data:
            for period_id, year in periods_data:

                # Generate simple trend logic
                if code == "1.1.1":
                    base = {"GBR": 12, "KEN": 45, "DEU": 8}[iso3]
                    value = base - (year - 2015) * 0.3

                elif code == "2.1.1":
                    base = {"GBR": 3, "KEN": 20, "DEU": 2}[iso3]
                    value = base - (year - 2015) * 0.2

                elif code == "3.2.1":
                    base = {"GBR": 5, "KEN": 35, "DEU": 4}[iso3]
                    value = base - (year - 2015) * 0.5

                else:
                    value = None

                cursor.execute("""
                    INSERT OR IGNORE INTO fact_sdg_value
                    (country_id, indicator_id, period_id, value, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (country_id, indicator_id, period_id, value, "Sample Data"))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialised.")
