import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
SQL_DIR = BASE_DIR / "sql"

# Local default points at the docker-compose Postgres exposed on port 5433
WAREHOUSE_DSN = os.getenv(
    "WAREHOUSE_DSN", "postgresql://airflow:airflow@localhost:5433/warehouse"
)

API_URL = "https://api.open-meteo.com/v1/forecast"  # free, no API key needed
HOURLY_FIELDS = "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"

# city -> (latitude, longitude)
CITIES = {
    "Pune": (18.5204, 73.8567),
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
}

METRICS = ["temperature_c", "humidity_pct", "precipitation_mm", "wind_speed_kmh"]
