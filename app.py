import streamlit as st
import pandas as pd
import altair as alt
from api_loader import fetch_world_bank_data

st.set_page_config(layout="wide")

st.title("🌍 SDG Country Profiler (World Bank Edition)")

# -----------------------------
# SDG → World Bank Mapping
# -----------------------------
SDG_INDICATORS = {
    "1 - Poverty (Extreme Poverty %)": "SI.POV.DDAY",
    "3 - Maternal Mortality": "SH.STA.MMRT",
    "5 - Female Population (%)": "SP.POP.TOTL.FE.ZS",
    "7 - Renewable Energy (%)": "EG.FEC.RNEW.ZS",
    "8 - GDP Growth (%)": "NY.GDP.MKTP.KD.ZG",
    "13 - CO₂ Emissions per capita": "EN.ATM.CO2E.PC"
}

COUNTRIES = {
    "United Kingdom": "GB",
    "United States": "US",
    "Hungary": "HU",
    "Germany": "DE",
    "France": "FR",
    "India": "IN",
    "Brazil": "BR"
}

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("Selection")

country_name = st.sidebar.selectbox(
    "Select Country",
    list(COUNTRIES.keys())
)

sdg_choice = st.sidebar.selectbox(
    "Select SDG Indicator",
    list(SDG_INDICATORS.keys())
)

country_code = COUNTRIES[country_name]
indicator_code = SDG_INDICATORS[sdg_choice]

# -----------------------------
# Data Fetch
# -----------------------------
@st.cache_data
def load_data(country_code, indicator_code):
    return fetch_world_bank_data(country_code, indicator_code)

with st.spinner("Fetching data from World Bank..."):
    df = load_data(country_code, indicator_code)

# -----------------------------
# Display
# -----------------------------
if df.empty:
    st.warning("No data available for this country/indicator.")
else:

    st.subheader(f"{sdg_choice} — {country_name}")

    # Latest value
    latest_value = df.iloc[-1]["value"]
    latest_year = df.iloc[-1]["date"].year

    st.metric(
        label=f"Latest Value ({latest_year})",
        value=round(latest_value, 2)
    )

    # Altair Chart (Professional)
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("date:T", title="Year"),
        y=alt.Y("value:Q", title="Value"),
        tooltip=[
            alt.Tooltip("date:T", title="Year"),
            alt.Tooltip("value:Q", title="Value", format=".2f")
        ]
    ).properties(
        height=450
    )

    st.altair_chart(chart, use_container_width=True)

