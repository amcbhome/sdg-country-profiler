import sqlite3
import os
from typing import Dict, Tuple, List

DB_PATH = "sdg.db"
SCHEMA_PATH = "database/schema.sql"


GOALS: List[Tuple[int, str, str]] = [
    (1,  "No Poverty", "End poverty in all its forms everywhere."),
    (2,  "Zero Hunger", "End hunger, achieve food security and improved nutrition, and promote sustainable agriculture."),
    (3,  "Good Health and Well-being", "Ensure healthy lives and promote well-being for all at all ages."),
    (4,  "Quality Education", "Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all."),
    (5,  "Gender Equality", "Achieve gender equality and empower all women and girls."),
    (6,  "Clean Water and Sanitation", "Ensure availability and sustainable management of water and sanitation for all."),
    (7,  "Affordable and Clean Energy", "Ensure access to affordable, reliable, sustainable and modern energy for all."),
    (8,  "Decent Work and Economic Growth", "Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all."),
    (9,  "Industry, Innovation and Infrastructure", "Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation."),
    (10, "Reduced Inequalities", "Reduce inequality within and among countries."),
    (11, "Sustainable Cities and Communities", "Make cities and human settlements inclusive, safe, resilient and sustainable."),
    (12, "Responsible Consumption and Production", "Ensure sustainable consumption and production patterns."),
    (13, "Climate Action", "Take urgent action to combat climate change and its impacts."),
    (14, "Life Below Water", "Conserve and sustainably use the oceans, seas and marine resources for sustainable development."),
    (15, "Life on Land", "Protect, restore and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification, and halt biodiversity loss."),
    (16, "Peace, Justice and Strong Institutions", "Promote peaceful and inclusive societies, provide access to justice for all, and build effective, accountable and inclusive institutions."),
    (17, "Partnerships for the Goals", "Strengthen the means of implementation and revitalize the global partnership for sustainable development."),
]

# Starter: 1 indicator per goal (extend later by adding more rows)
INDICATORS: List[Tuple[int, str, str, str]] = [
    (1,  "1.1.1",  "Population below international poverty line", "%"),
    (2,  "2.1.1",  "Prevalence of undernourishment", "%"),
    (3,  "3.2.1",  "Under-5 mortality rate", "per 1000"),
    (4,  "4.1.1",  "Minimum proficiency in reading/maths (proxy)", "%"),
    (5,  "5.5.1",  "Women in parliament (proxy)", "%"),
    (6,  "6.1.1",  "Safely managed drinking water services", "%"),
    (7,  "7.1.1",  "Access to electricity", "%"),
    (8,  "8.5.2",  "Unemployment rate", "%"),
    (9,  "9.5.1",  "R&D expenditure", "% of GDP"),
    (10, "10.1.1", "Income growth of bottom 40% (proxy)", "%"),
    (11, "11.6.2", "PM2.5 annual mean concentration", "µg/m³"),
    (12, "12.5.1", "National recycling rate (proxy)", "%"),
    (13, "13.2.1", "Climate policy coverage index (proxy)", "index"),
    (14, "14.5.1", "Marine protected area coverage", "%"),
    (15, "15.1.1", "Forest area as proportion of land area", "%"),
    (16, "16.1.1", "Intentional homicide rate", "per 100,000"),
    (17, "17.1.1", "Total government revenue", "% of GDP"),
]

COUNTRIES: List[Tuple[str, str]] = [
    ("United Kingdom", "GBR"),
    ("Germany", "DEU"),
    ("Kenya", "KEN"),
]

YEARS = list(range(2015, 2025))


def _load_schema(cur: sqlite3.Cursor) -> None:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cur.executescript(f.read())


def _insert_reference_data(cur: sqlite3.Cursor) -> None:
    cur.executemany("INSERT OR IGNORE INTO sdg_goal(goal_id, title, description) VALUES (?, ?, ?)", GOALS)

    cur.executemany(
        "INSERT OR IGNORE INTO sdg_indicator(goal_id, indicator_code, name, unit) VALUES (?, ?, ?, ?)",
        INDICATORS
    )

    cur.executemany(
        "INSERT OR IGNORE INTO dim_country(country_name, iso3) VALUES (?, ?)",
        COUNTRIES
    )

    for y in YEARS:
        cur.execute("INSERT OR IGNORE INTO dim_period(year) VALUES (?)", (y,))


def _country_modifier(iso3: str) -> float:
    # Creates a stable difference between countries for synthetic values
    return {"GBR": 0.9, "DEU": 0.85, "KEN": 1.25}.get(iso3, 1.0)


def _direction(indicator_code: str) -> int:
    """
    +1 means "higher is better" (e.g., access %),
    -1 means "lower is better" (e.g., poverty %, PM2.5, homicide rate, under-5 mortality, unemployment).
    """
    lower_is_better = {
        "1.1.1", "2.1.1", "3.2.1", "8.5.2", "11.6.2", "16.1.1"
    }
    return -1 if indicator_code in lower_is_better else +1


def _base_value(indicator_code: str, iso3: str) -> float:
    # Rough starting points by indicator (synthetic, not real)
    bases = {
        "1.1.1":  {"GBR": 10.0, "DEU": 8.0,  "KEN": 45.0},
        "2.1.1":  {"GBR": 3.0,  "DEU": 2.0,  "KEN": 20.0},
        "3.2.1":  {"GBR": 5.0,  "DEU": 4.0,  "KEN": 35.0},
        "4.1.1":  {"GBR": 72.0, "DEU": 75.0, "KEN": 55.0},
        "5.5.1":  {"GBR": 32.0, "DEU": 35.0, "KEN": 22.0},
        "6.1.1":  {"GBR": 99.0, "DEU": 99.0, "KEN": 70.0},
        "7.1.1":  {"GBR": 100.0,"DEU": 100.0,"KEN": 75.0},
        "8.5.2":  {"GBR": 6.5,  "DEU": 5.0,  "KEN": 10.0},
        "9.5.1":  {"GBR": 1.7,  "DEU": 2.9,  "KEN": 0.4},
        "10.1.1": {"GBR": 1.8,  "DEU": 1.5,  "KEN": 2.5},
        "11.6.2": {"GBR": 12.0, "DEU": 11.0, "KEN": 25.0},
        "12.5.1": {"GBR": 45.0, "DEU": 55.0, "KEN": 12.0},
        "13.2.1": {"GBR": 60.0, "DEU": 65.0, "KEN": 45.0},
        "14.5.1": {"GBR": 25.0, "DEU": 20.0, "KEN": 10.0},
        "15.1.1": {"GBR": 13.0, "DEU": 33.0, "KEN": 7.0},
        "16.1.1": {"GBR": 1.2,  "DEU": 0.9,  "KEN": 4.5},
        "17.1.1": {"GBR": 35.0, "DEU": 37.0, "KEN": 18.0},
    }
    return bases[indicator_code][iso3]


def _annual_delta(indicator_code: str) -> float:
    # Synthetic year-on-year change magnitude
    deltas = {
        "1.1.1":  0.30,
        "2.1.1":  0.20,
        "3.2.1":  0.50,
        "4.1.1":  0.40,
        "5.5.1":  0.35,
        "6.1.1":  0.25,
        "7.1.1":  0.10,
        "8.5.2":  0.10,
        "9.5.1":  0.05,
        "10.1.1": 0.03,
        "11.6.2": 0.15,
        "12.5.1": 0.40,
        "13.2.1": 0.80,
        "14.5.1": 0.25,
        "15.1.1": 0.10,
        "16.1.1": 0.05,
        "17.1.1": 0.15,
    }
    return deltas[indicator_code]


def _clamp(value: float, unit: str) -> float:
    # Keep values in sensible ranges for dashboard demo
    if unit == "%":
        return max(0.0, min(100.0, value))
    if unit in {"% of GDP"}:
        return max(0.0, min(10.0, value))
    if unit == "index":
        return max(0.0, min(100.0, value))
    return max(0.0, value)


def _insert_fact_data(cur: sqlite3.Cursor) -> None:
    # Pre-fetch ids
    country_rows = cur.execute("SELECT country_id, iso3 FROM dim_country").fetchall()
    indicator_rows = cur.execute("SELECT indicator_id, indicator_code, unit FROM sdg_indicator").fetchall()
    period_rows = cur.execute("SELECT period_id, year FROM dim_period").fetchall()
    period_id_by_year = {y: pid for pid, y in period_rows}

    for country_id, iso3 in country_rows:
        mod = _country_modifier(iso3)

        for indicator_id, ind_code, unit in indicator_rows:
            base = _base_value(ind_code, iso3)
            delta = _annual_delta(ind_code)
            sign = _direction(ind_code)  # +1 means higher is better; -1 means lower is better

            for year in YEARS:
                t = year - YEARS[0]

                # If lower is better -> trend downward; if higher is better -> upward
                # Add a tiny country modifier effect in the trend slope as well
                value = base + (sign * delta * t) * (1.0 / mod)

                # Clamp to sensible bounds for unit type
                value = _clamp(value, unit)

                cur.execute(
                    """
                    INSERT OR IGNORE INTO fact_sdg_value
                    (country_id, indicator_id, period_id, value, source)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (country_id, indicator_id, period_id_by_year[year], float(value), "Synthetic demo data"),
                )


def initialize_database(rebuild: bool = False) -> None:
    """
    If rebuild=True, delete and recreate sdg.db.
    Otherwise idempotently ensures schema + reference data exist, and fills missing facts.
    """
    if rebuild and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    _load_schema(cur)
    _insert_reference_data(cur)
    _insert_fact_data(cur)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database(rebuild=True)
    print("Database initialised (rebuild=True).")
