import pandas as pd
import pytest

from src.quality import run_checks, validate_csv
from src.transform import build_dataframe

PAYLOAD = {
    "city": "Pune",
    "hourly": {
        "time": ["2026-10-30T00:00", "2026-10-30T01:00", "2026-10-30T01:00"],
        "temperature_2m": [24.1, 23.8, 23.8],
        "relative_humidity_2m": [70, 72, 72],
        "precipitation": [0.0, 0.2, 0.2],
        "wind_speed_10m": [5.1, 4.8, 4.8],
    },
}


def test_transform_drops_duplicates_and_shapes_columns():
    df = build_dataframe([PAYLOAD])
    assert len(df) == 2
    assert list(df.columns) == [
        "city", "ts", "temperature_c", "humidity_pct", "precipitation_mm", "wind_speed_kmh"
    ]


def test_transform_handles_empty_payloads():
    df = build_dataframe([])
    assert df.empty
    assert "city" in df.columns
    assert "ts" in df.columns


def test_quality_passes_on_clean_data():
    assert run_checks(build_dataframe([PAYLOAD])) == []


def test_quality_catches_bad_temperature():
    df = build_dataframe([PAYLOAD])
    df.loc[0, "temperature_c"] = 200
    assert any("temperature" in f for f in run_checks(df))


def test_quality_catches_bad_humidity():
    df = build_dataframe([PAYLOAD])
    df.loc[0, "humidity_pct"] = 105
    assert any("humidity" in f for f in run_checks(df))


def test_quality_catches_negative_precipitation():
    df = build_dataframe([PAYLOAD])
    df.loc[0, "precipitation_mm"] = -1.5
    assert any("negative precipitation" in f for f in run_checks(df))


def test_quality_catches_null_key_columns():
    df = build_dataframe([PAYLOAD])
    df.loc[0, "city"] = None
    assert any("key columns" in f for f in run_checks(df))


def test_quality_catches_missing_columns():
    df = build_dataframe([PAYLOAD]).drop(columns=["wind_speed_kmh"])
    failures = run_checks(df)
    assert any("missing required columns" in f for f in failures)


def test_quality_catches_excessive_nulls():
    df = build_dataframe([PAYLOAD])
    # 1 out of 2 rows null = 50% nulls (> 20% limit)
    df.loc[0, "temperature_c"] = None
    assert any("20% nulls" in f for f in run_checks(df))


def test_quality_catches_empty():
    assert run_checks(pd.DataFrame()) == ["dataframe is empty"]


def test_validate_csv_raises_on_invalid_data(tmp_path):
    bad_df = build_dataframe([PAYLOAD])
    bad_df.loc[0, "temperature_c"] = 999.0
    csv_file = tmp_path / "bad_weather.csv"
    bad_df.to_csv(csv_file, index=False)

    with pytest.raises(ValueError, match="Data quality checks failed"):
        validate_csv(str(csv_file))
