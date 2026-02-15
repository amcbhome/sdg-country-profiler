import os
import sqlite3
import pandas as pd
import streamlit as st
import numpy as np

from data.seed_data import initialize_database
from data.api_loader import load_indicator_data

DB_PATH = "sdg.db"

# -----------------------------
# Ensure Database Exists
# -----------------------------
if not os.path.exists(DB_PATH):
    initialize_database(rebuild=True)


# -----------------------------
# Database Query Helper
# -----------------------------
@st.cache_data
def run_query(query: str, params=()):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="SDG Country Profiler", layout="wide")
st.title("🌍 SDG Country Profiler")

# -----------------------------
# Sidebar Controls
# -----------------------------
countries = run_query(
    "SELECT country_name FROM dim_country ORDER BY country_name"
)

goals = run_query(
    "SELECT goal_id, title FROM sdg_goal ORDER BY goal_id"
)

country = st.sidebar.selectbox(
    "Select Country",
    countries["country_name"]
)

goal_label = st.sidebar.selectbox(
    "Select SDG Goal",
    goals.apply(lambda r: f"{r.goal_id} - {r.title}", axis=1)
)

goal_id = int(goal_label.split(" - ")[0])

# -----------------------------
# Goal Description
# -----------------------------
goal_info = run_query(
    "SELECT title, description FROM sdg_goal WHERE goal_id = ?",
    (goal_id,)
)

st.subheader(f"SDG {goal_id} — {goal_info.iloc[0]['title']}")
st.write(goal_info.iloc[0]["description"])

# -----------------------------
# Indicator Selection
# -----------------------------
indicators = run_query(
    """
    SELECT indicator_code, name, unit
    FROM sdg_indicator
    WHERE goal_id = ?
    ORDER BY indicator_code
    """,
    (goal_id,)
)

indicator_label = st.sidebar.selectbox(
    "Select Indicator",
    indicators.apply(lambda r: f"{r.indicator_code} — {r.name}", axis=1)
)

indicator_code = indicator_label.split(" — ")[0]

# -----------------------------
# Fetch Data
# -----------------------------
def fetch_indicator_dataframe(country_name, indicator_code):
    df = run_query(
        """
        SELECT p.year, i.indicator_code, i.name AS indicator_name,
               i.unit, f.value
        FROM fact_sdg_value f
        JOIN dim_country c   ON c.country_id = f.country_id
        JOIN sdg_indicator i ON i.indicator_id = f.indicator_id
        JOIN dim_period p    ON p.period_id = f.period_id
        WHERE c.country_name = ?
          AND i.indicator_code = ?
        ORDER BY p.year
        """,
        (country_name, indicator_code),
    )
    return df


df = fetch_indicator_dataframe(country, indicator_code)

# -----------------------------
# If No Data → Call API
# -----------------------------
if df.empty:
    iso3 = run_query(
        "SELECT iso3 FROM dim_country WHERE country_name = ?",
        (country,)
    ).iloc[0]["iso3"]

    with st.spinner("Fetching data from UN SDG API..."):
        load_indicator_data(indicator_code, iso3)

    df = fetch_indicator_dataframe(country, indicator_code)

# -----------------------------
# Display Section
# -----------------------------
if df.empty:
    st.error("No data available for this selection.")
else:

    # Latest KPI
    latest = df.iloc[-1]
    st.metric(
        label=f"Latest Value ({latest['year']})",
        value=f"{latest['value']:.2f} {latest['unit']}"
    )

    # Trend Calculation (Linear Regression)
    if len(df) > 1:
        years = df["year"].values
        values = df["value"].values
        slope = np.polyfit(years, values, 1)[0]

        if slope > 0:
            trend = "Increasing"
        elif slope < 0:
            trend = "Decreasing"
        else:
            trend = "Stable"

        st.write(f"Trend Direction: **{trend}**")

    # Data Table
    st.dataframe(
        df[["year", "indicator_code", "indicator_name", "value", "unit"]],
        use_container_width=True
    )

    # Line Chart
    st.line_chart(df, x="year", y="value")
