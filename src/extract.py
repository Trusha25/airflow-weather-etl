"""EXTRACT: pull hourly weather for each city from the Open-Meteo API."""
from datetime import date
import json
import logging
import sys

import requests

from src.config import API_URL, CITIES, DATA_DIR, HOURLY_FIELDS

log = logging.getLogger(__name__)


def fetch_city(city: str, lat: float, lon: float, day: str) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": HOURLY_FIELDS,
        "start_date": day,
        "end_date": day,
        "timezone": "Asia/Kolkata",
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    payload["city"] = city
    return payload


def extract_all(day: str | None = None) -> str:
    """Save one raw JSON file per city. Returns the folder path."""
    if not day:
        day = date.today().isoformat()
    out_dir = DATA_DIR / "raw" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    for city, (lat, lon) in CITIES.items():
        payload = fetch_city(city, lat, lon, day)
        (out_dir / f"{city}.json").write_text(json.dumps(payload), encoding="utf-8")
        log.info("Extracted %s for %s", city, day)
    return str(out_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    target_day = sys.argv[1] if len(sys.argv) > 1 else None
    folder = extract_all(target_day)
    print(f"Extracted files to: {folder}")
