CREATE TABLE IF NOT EXISTS dim_city (
    city_id    SERIAL PRIMARY KEY,
    city_name  TEXT UNIQUE NOT NULL,
    latitude   NUMERIC(8,4),
    longitude  NUMERIC(8,4)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key    INT PRIMARY KEY,           -- e.g. 20261031
    full_date   DATE NOT NULL,
    day         SMALLINT,
    month       SMALLINT,
    year        SMALLINT,
    day_name    TEXT,
    is_weekend  BOOLEAN
);

CREATE TABLE IF NOT EXISTS fact_weather (
    city_id           INT NOT NULL REFERENCES dim_city(city_id),
    date_key          INT NOT NULL REFERENCES dim_date(date_key),
    hour              SMALLINT,
    ts                TIMESTAMP NOT NULL,
    temperature_c     NUMERIC(5,2),
    humidity_pct      NUMERIC(5,2),
    precipitation_mm  NUMERIC(6,2),
    wind_speed_kmh    NUMERIC(6,2),
    loaded_at         TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (city_id, ts)
);

CREATE INDEX IF NOT EXISTS idx_fact_weather_date ON fact_weather(date_key);
