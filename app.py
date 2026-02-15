import streamlit as st
import sqlite3
import pandas as pd
import os
from data.seed_data import initialize_database

DB_PATH = "sdg.db"

# Auto-create database if missing
if not os.path.exists(DB_PATH):
    initialize_database()

@st.cache_data
def run_query(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

st.set_page_config(page_title="SDG Country Profiler", layout="wide")

st.title("🌍 SDG Country Profiler")

countries = run_query("SELECT country_name FROM dim_country")
goals = run_query("SELECT goal_id, title FROM sdg_goal")

selected_country = st.sidebar.selectbox(
    "Select Country", 
    countries["country_name"]
)

selected_goal = st.sidebar.selectbox(
    "Select SDG Goal",
    goals.apply(lambda row: f"{row.goal_id} - {row.title}", axis=1)
)

goal_id = int(selected_goal.split(" - ")[0])

goal_info = run_query(
    "SELECT description FROM sdg_goal WHERE goal_id = ?",
    (goal_id,)
)

st.subheader(f"SDG {goal_id}")
st.write(goal_info.iloc[0]["description"])

query = """
SELECT p.year, i.name, f.value, i.unit
FROM fact_sdg_value f
JOIN dim_country c ON c.country_id = f.country_id
JOIN sdg_indicator i ON i.indicator_id = f.indicator_id
JOIN dim_period p ON p.period_id = f.period_id
WHERE c.country_name = ?
AND i.goal_id = ?
ORDER BY p.year
"""

df = run_query(query, (selected_country, goal_id))

if df.empty:
    st.warning("No data available.")
else:
    st.dataframe(df)
    st.line_chart(df, x="year", y="value")
