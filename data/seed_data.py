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

    # Insert Goals (sample 1–3)
    goals = [
        (1, "No Poverty", "End poverty in all its forms everywhere."),
        (2, "Zero Hunger", "End hunger, achieve food security and improved nutrition."),
        (3, "Good Health and Well-being", "Ensure healthy lives and promote well-being.")
    ]
    cursor.executemany("INSERT OR IGNORE INTO sdg_goal VALUES (?, ?, ?)", goals)

    # Indicators
    indicators = [
        (1, "1.1.1", "Population below poverty line", "%"),
        (2, "2.1.1", "Prevalence of undernourishment", "%"),
        (3, "3.2.1", "Under-5 mortality rate", "per 1000")
    ]
    cursor.executemany(
        "INSERT INTO sdg_indicator (goal_id, indicator_code, name, unit) VALUES (?, ?, ?, ?)",
        indicators
    )

    # Countries
    countries = [
        ("United Kingdom", "GBR"),
        ("Kenya", "KEN"),
        ("Germany", "DEU")
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO dim_country (country_name, iso3) VALUES (?, ?)",
        countries
    )

    # Years
    for year in range(2015, 2025):
        cursor.execute("INSERT OR IGNORE INTO dim_period (year) VALUES (?)", (year,))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("Database initialised.")

