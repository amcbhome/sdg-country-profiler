import os
import sqlite3
import pandas as pd
import streamlit as st
from data.seed_data import initialize_database

DB_PATH = "sdg.db"

# Ensure DB exists (first run on a fresh clone)
if not os.path.exists(DB_PATH):
    initialize_database(rebuild=True)

@st.cache_data
def run_query(query: str, params=()):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

st.set_page_config(page_title="SDG Country Profiler", layout="wide")
st.title("🌍 SDG Country Profiler")

# Sidebar
countries = run_query("SELECT country_name FROM dim_country ORDER BY country_name")
goals = run_query("SELECT goal_id, title FROM sdg_goal ORDER BY goal_id")

country = st.sidebar.selectbox("Select Country", countries["country_name"])
goal_label = st.sidebar.selectbox(
    "Select SDG Goal",
    goals.apply(lambda r: f"{r.goal_id} - {r.title}", axis=1)
)
goal_id = int(goal_label.split(" - ")[0])

goal_info = run_query("SELECT title, description FROM sdg_goal WHERE goal_id = ?", (goal_id,))
st.subheader(f"SDG {goal_id} — {goal_info.iloc[0]['title']}")
st.write(goal_info.iloc[0]["description"])

# Indicator selector within the goal
indicators = run_query(
    """
    SELECT indicator_code, name, unit
    FROM sdg_indicator
    WHERE goal_id = ?
    ORDER BY indicator_code
    """,
    (goal_id,),
)

indicator_label = st.sidebar.selectbox(
    "Select Indicator",
    indicators.apply(lambda r: f"{r.indicator_code} — {r.name}", axis=1)
)
indicator_code = indicator_label.split(" — ")[0]

# Pull time series for that country + indicator
df = run_query(
    """
    SELECT p.year, i.indicator_code, i.name AS indicator_name, i.unit, f.value
    FROM fact_sdg_value f
    JOIN dim_country c   ON c.country_id = f.country_id
    JOIN sdg_indicator i ON i.indicator_id = f.indicator_id
    JOIN dim_period p    ON p.period_id = f.period_id
    WHERE c.country_name = ?
      AND i.indicator_code = ?
    ORDER BY p.year
    """,
    (country, indicator_code),
)

if df.empty:
    st.warning("No data available for this selection.")
else:
    latest = df.iloc[-1]
    st.metric(
        label=f"Latest value ({latest['year']})",
        value=f"{latest['value']:.2f} {latest['unit']}"
    )

    st.dataframe(
        df[["year", "indicator_code", "indicator_name", "value", "unit"]],
        use_container_width=True
    )
    st.line_chart(df, x="year", y="value")
