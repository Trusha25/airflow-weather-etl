from datetime import datetime, timedelta

from airflow.decorators import dag, task


@dag(
    dag_id="weather_etl",
    description="Daily weather ETL: Open-Meteo API -> clean -> validate -> Postgres star schema",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["etl", "portfolio"],
)
def weather_etl():
    @task
    def extract(ds=None) -> str:
        from src.extract import extract_all
        return extract_all(day=ds)

    @task
    def transform(raw_dir: str, ds=None) -> str:
        from src.transform import transform_day
        return transform_day(raw_dir=raw_dir, day=ds)

    @task
    def quality_check(csv_path: str) -> str:
        from src.quality import validate_csv
        return validate_csv(csv_path)

    @task
    def load(csv_path: str) -> int:
        from src.load import load_csv
        return load_csv(csv_path)

    raw_dir = extract()
    staged_csv = transform(raw_dir)
    validated_csv = quality_check(staged_csv)
    load(validated_csv)


weather_etl()
