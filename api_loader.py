import requests
import pandas as pd

BASE_URL = "https://api.worldbank.org/v2/country"

def fetch_world_bank_data(country_code, indicator_code):
    """
    Fetch data from the World Bank API.
    Returns a clean pandas DataFrame with:
    - date (datetime)
    - value (float)
    """

    url = f"{BASE_URL}/{country_code}/indicator/{indicator_code}?format=json&per_page=1000"

    try:
        response = requests.get(url)
    except Exception:
        return pd.DataFrame()

    if response.status_code != 200:
        return pd.DataFrame()

    data = response.json()

    if not data or len(data) < 2:
        return pd.DataFrame()

    records = data[1]
    df = pd.DataFrame(records)

    if df.empty:
        return df

    df = df[["date", "value"]]
    df = df.dropna()

    # Convert year to datetime (fixes comma issue)
    df["date"] = pd.to_datetime(df["date"], format="%Y")

    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna()
    df = df.sort_values("date")

    return df

