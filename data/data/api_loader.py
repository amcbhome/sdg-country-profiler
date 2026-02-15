import requests
import sqlite3

DB_PATH = "sdg.db"
BASE_URL = "https://unstats.un.org/SDGAPI/v1/sdg/Data"


def fetch_indicator_data(indicator_code: str, iso3: str):
    params = {
        "Indicator": indicator_code,
        "Country": iso3
    }

    response = requests.get(BASE_URL, params=params, timeout=30)

    if response.status_code != 200:
        print(f"API error {response.status_code}")
        return []

    data = response.json()
    return data.get("data", [])


def load_indicator_data(indicator_code: str, iso3: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch IDs
    cursor.execute("SELECT country_id FROM dim_country WHERE iso3 = ?", (iso3,))
    country_row = cursor.fetchone()
    if not country_row:
        conn.close()
        return

    country_id = country_row[0]

    cursor.execute("SELECT indicator_id FROM sdg_indicator WHERE indicator_code = ?", (indicator_code,))
    indicator_row = cursor.fetchone()
    if not indicator_row:
        conn.close()
        return

    indicator_id = indicator_row[0]

    api_data = fetch_indicator_data(indicator_code, iso3)

    for row in api_data:
        year = row.get("TimePeriod")
        value = row.get("Value")

        if not year or value is None:
            continue

        year = int(year)

        # Ensure year exists
        cursor.execute("INSERT OR IGNORE INTO dim_period (year) VALUES (?)", (year,))
        cursor.execute("SELECT period_id FROM dim_period WHERE year = ?", (year,))
        period_id = cursor.fetchone()[0]

        # Insert only if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO fact_sdg_value
            (country_id, indicator_id, period_id, value, source)
            VALUES (?, ?, ?, ?, ?)
        """, (country_id, indicator_id, period_id, float(value), "UN SDG API"))

    conn.commit()
    conn.close()
