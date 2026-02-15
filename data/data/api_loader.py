import requests
import sqlite3
from typing import Optional

DB_PATH = "sdg.db"
BASE_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Data"


def fetch_indicator_data(indicator_code: str, iso3: str):
    """
    Fetch data from UN SDG API for a given indicator and country.
    """
    params = {
        "Indicator": indicator_code,
        "Country": iso3
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        print(f"Error fetching {indicator_code} for {iso3}")
        return []

    data = response.json()

    if "data" not in data:
        return []

    return data["data"]


def insert_data(indicator_code: str, iso3: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get IDs
    cursor.execute("SELECT country_id FROM dim_country WHERE iso3 = ?", (iso3,))
    country = cursor.fetchone()
    if not country:
        print(f"Country {iso3} not found")
        return
    country_id = country[0]

    cursor.execute("SELECT indicator_id FROM sdg_indicator WHERE indicator_code = ?", (indicator_code,))
    indicator = cursor.fetchone()
    if not indicator:
        print(f"Indicator {indicator_code} not found")
        return
    indicator_id = indicator[0]

    api_data = fetch_indicator_data(indicator_code, iso3)

    for row in api_data:
        year = row.get("TimePeriod")
        value = row.get("Value")

        if year is None or value is None:
            continue

        # Ensure year exists in dim_period
        cursor.execute("INSERT OR IGNORE INTO dim_period (year) VALUES (?)", (int(year),))
        cursor.execute("SELECT period_id FROM dim_period WHERE year = ?", (int(year),))
        period_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT OR IGNORE INTO fact_sdg_value
            (country_id, indicator_id, period_id, value, source)
            VALUES (?, ?, ?, ?, ?)
        """, (country_id, indicator_id, period_id, float(value), "UN SDG API"))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Example load
    insert_data("3.2.1", "GBR")
    print("Data loaded from API.")
