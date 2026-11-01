"""DATA QUALITY: fail the pipeline loudly instead of loading bad data."""
import logging
import sys

import pandas as pd

from src.config import METRICS

log = logging.getLogger(__name__)


def run_checks(df: pd.DataFrame) -> list[str]:
    failures = []
    if df.empty:
        return ["dataframe is empty"]

    expected_cols = {"city", "ts"} | set(METRICS)
    missing = expected_cols - set(df.columns)
    if missing:
        failures.append(f"missing required columns: {sorted(missing)}")
        return failures

    if df[["city", "ts"]].isnull().any().any():
        failures.append("null values in key columns (city, ts)")
    if df.duplicated(subset=["city", "ts"]).any():
        failures.append("duplicate (city, ts) rows")
    if not df["temperature_c"].dropna().between(-50, 60).all():
        failures.append("temperature_c outside -50..60")
    if not df["humidity_pct"].dropna().between(0, 100).all():
        failures.append("humidity_pct outside 0..100")
    if (df["precipitation_mm"].dropna() < 0).any():
        failures.append("negative precipitation_mm")
    if df[METRICS].isnull().mean().max() > 0.2:
        failures.append("more than 20% nulls in a metric column")
    return failures


def validate_csv(path: str) -> str:
    df = pd.read_csv(path, parse_dates=["ts"])
    failures = run_checks(df)
    if failures:
        raise ValueError(f"Data quality checks failed: {failures}")
    log.info("Quality checks passed for %s (%d rows)", path, len(df))
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python -m src.quality <csv_path>")
        sys.exit(1)
    target_csv = sys.argv[1]
    validate_csv(target_csv)
    print(f"Data quality checks passed successfully for: {target_csv}")
