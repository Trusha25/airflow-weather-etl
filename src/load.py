"""LOAD: idempotent upsert into a star schema in Postgres."""
import logging
import sys

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from src.config import CITIES, SQL_DIR, WAREHOUSE_DSN

log = logging.getLogger(__name__)


def _val(x):
    return None if pd.isna(x) else float(x)


def load_csv(path: str) -> int:
    df = pd.read_csv(path, parse_dates=["ts"])
    conn = psycopg2.connect(WAREHOUSE_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))

            # dim_city (upsert coordinates if updated)
            city_tuples = [(c, lat, lon) for c, (lat, lon) in CITIES.items()]
            if city_tuples:
                execute_values(
                    cur,
                    "INSERT INTO dim_city (city_name, latitude, longitude) VALUES %s "
                    "ON CONFLICT (city_name) DO UPDATE SET "
                    "latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude",
                    city_tuples,
                )
            cur.execute("SELECT city_name, city_id FROM dim_city")
            city_ids = dict(cur.fetchall())

            # dim_date
            date_records = []
            if not df.empty and "ts" in df.columns:
                dates = pd.Series(df["ts"].dropna().dt.normalize().unique())
                date_records = [
                    (
                        int(d.strftime("%Y%m%d")),
                        d.date(),
                        int(d.day),
                        int(d.month),
                        int(d.year),
                        d.day_name(),
                        bool(d.dayofweek >= 5),
                    )
                    for d in dates
                ]

            if date_records:
                execute_values(
                    cur,
                    "INSERT INTO dim_date (date_key, full_date, day, month, year, "
                    "day_name, is_weekend) VALUES %s ON CONFLICT (date_key) DO NOTHING",
                    date_records,
                )

            # fact_weather (upsert -> safe to re-run the same day)
            rows = []
            if not df.empty:
                rows = [
                    (
                        city_ids[r.city],
                        int(r.ts.strftime("%Y%m%d")),
                        int(r.ts.hour),
                        r.ts.to_pydatetime(),
                        _val(r.temperature_c),
                        _val(r.humidity_pct),
                        _val(r.precipitation_mm),
                        _val(r.wind_speed_kmh),
                    )
                    for r in df.itertuples()
                    if r.city in city_ids
                ]

            if rows:
                execute_values(
                    cur,
                    "INSERT INTO fact_weather (city_id, date_key, hour, ts, temperature_c, "
                    "humidity_pct, precipitation_mm, wind_speed_kmh) VALUES %s "
                    "ON CONFLICT (city_id, ts) DO UPDATE SET "
                    "temperature_c = EXCLUDED.temperature_c, "
                    "humidity_pct = EXCLUDED.humidity_pct, "
                    "precipitation_mm = EXCLUDED.precipitation_mm, "
                    "wind_speed_kmh = EXCLUDED.wind_speed_kmh, loaded_at = now()",
                    rows,
                )

        conn.commit()
        log.info("Loaded %d rows from %s into fact_weather", len(rows), path)
        return len(rows)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python -m src.load <csv_path>")
        sys.exit(1)
    target_csv = sys.argv[1]
    loaded_count = load_csv(target_csv)
    print(f"Successfully loaded {loaded_count} rows into the warehouse.")
