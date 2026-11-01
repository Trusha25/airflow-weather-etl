"""TRANSFORM: raw JSON -> clean, tidy table (one row per city per hour)."""
import json
import logging
from pathlib import Path
import sys

import pandas as pd

from src.config import DATA_DIR, METRICS

log = logging.getLogger(__name__)


def build_dataframe(payloads: list[dict]) -> pd.DataFrame:
    if not payloads:
        return pd.DataFrame(columns=["city", "ts"] + METRICS)

    frames = []
    for p in payloads:
        h = p.get("hourly", {})
        if not h or "time" not in h:
            continue
        frames.append(
            pd.DataFrame(
                {
                    "city": p.get("city", ""),
                    "ts": pd.to_datetime(h["time"]),
                    "temperature_c": h.get("temperature_2m", []),
                    "humidity_pct": h.get("relative_humidity_2m", []),
                    "precipitation_mm": h.get("precipitation", []),
                    "wind_speed_kmh": h.get("wind_speed_10m", []),
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=["city", "ts"] + METRICS)

    df = pd.concat(frames, ignore_index=True)
    df[METRICS] = df[METRICS].apply(pd.to_numeric, errors="coerce")
    df = df.drop_duplicates(subset=["city", "ts"])
    df = df.dropna(subset=METRICS, how="all")
    return df.sort_values(["city", "ts"]).reset_index(drop=True)


def transform_day(raw_dir: str, day: str | None = None) -> str:
    raw_path = Path(raw_dir)
    day = day or raw_path.name
    payloads = [
        json.loads(f.read_text(encoding="utf-8"))
        for f in sorted(raw_path.glob("*.json"))
    ]
    df = build_dataframe(payloads)
    out_dir = DATA_DIR / "staging"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"weather_{day}.csv"
    df.to_csv(out, index=False)
    log.info("Transformed %d rows to %s", len(df), out)
    return str(out)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python -m src.transform <raw_dir> [day]")
        sys.exit(1)
    raw_directory = sys.argv[1]
    target_day = sys.argv[2] if len(sys.argv) > 2 else None
    csv_file = transform_day(raw_directory, target_day)
    print(f"Staged CSV created at: {csv_file}")
