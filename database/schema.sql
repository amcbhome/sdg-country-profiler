PRAGMA foreign_keys = ON;

-- Goals (1..17)
CREATE TABLE IF NOT EXISTS sdg_goal (
    goal_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL
);

-- Indicators (starter set; extend later)
CREATE TABLE IF NOT EXISTS sdg_indicator (
    indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    indicator_code TEXT NOT NULL UNIQUE, -- e.g. "3.2.1"
    name TEXT NOT NULL,
    unit TEXT,
    FOREIGN KEY (goal_id) REFERENCES sdg_goal(goal_id)
);

-- Countries
CREATE TABLE IF NOT EXISTS dim_country (
    country_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_name TEXT NOT NULL,
    iso3 TEXT UNIQUE
);

-- Period (year)
CREATE TABLE IF NOT EXISTS dim_period (
    period_id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL UNIQUE
);

-- Fact table: one value per country x indicator x year
CREATE TABLE IF NOT EXISTS fact_sdg_value (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    indicator_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    value REAL,
    source TEXT,
    FOREIGN KEY (country_id) REFERENCES dim_country(country_id),
    FOREIGN KEY (indicator_id) REFERENCES sdg_indicator(indicator_id),
    FOREIGN KEY (period_id) REFERENCES dim_period(period_id),
    UNIQUE(country_id, indicator_id, period_id)
);

-- Helpful view for Superset / quick summaries
CREATE VIEW IF NOT EXISTS vw_country_goal_summary AS
SELECT
    c.country_name,
    g.goal_id,
    g.title,
    p.year,
    AVG(f.value) AS avg_value,
    COUNT(f.value) AS indicator_count
FROM fact_sdg_value f
JOIN dim_country c   ON c.country_id = f.country_id
JOIN sdg_indicator i ON i.indicator_id = f.indicator_id
JOIN sdg_goal g      ON g.goal_id = i.goal_id
JOIN dim_period p    ON p.period_id = f.period_id
GROUP BY c.country_name, g.goal_id, g.title, p.year;

-- Country value + Global average (per indicator per year)
CREATE VIEW IF NOT EXISTS vw_indicator_with_avg AS
SELECT
    c.country_name,
    g.goal_id,
    i.indicator_code,
    i.name AS indicator_name,
    i.unit,
    p.year,
    f.value,
    AVG(f.value) OVER (
        PARTITION BY i.indicator_code, p.year
    ) AS global_avg
FROM fact_sdg_value f
JOIN dim_country c   ON c.country_id = f.country_id
JOIN sdg_indicator i ON i.indicator_id = f.indicator_id
JOIN sdg_goal g      ON g.goal_id = i.goal_id
JOIN dim_period p    ON p.period_id = f.period_id;
