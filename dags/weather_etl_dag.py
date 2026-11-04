import logging
from datetime import timedelta

import pendulum
from airflow.decorators import dag, task

log = logging.getLogger(__name__)

local_tz = pendulum.timezone("Asia/Kolkata")

DOC_MD = """
# 🌦️ Weather ETL Pipeline
Daily orchestrated pipeline collecting hourly weather metrics for six Indian cities
from the Open-Meteo API, transforming data with pandas, running fail-fast quality checks,
and loading into a PostgreSQL star schema.

### Key Details:
- **Timezone**: `Asia/Kolkata` (IST)
- **Schedule**: `@daily`
- **Concurrency**: `max_active_runs=1`
- **Task Timeout**: 5 minutes per task
- **Error Handling**: 2 retries (2m delay) with structured failure alerts
"""


def task_failure_alert(context):
    """Callback function executed whenever any task in the DAG fails."""
    ti = context.get("task_instance")
    task_id = ti.task_id if ti else "unknown_task"
    dag_id = context.get("dag").dag_id if context.get("dag") else "weather_etl"
    execution_date = context.get("logical_date") or context.get("execution_date")
    exception = context.get("exception")
    log.error(
        "[TASK FAILURE ALERT] DAG: %s | Task: %s | Execution Date: %s | Exception: %s",
        dag_id,
        task_id,
        execution_date,
        exception,
    )


@dag(
    dag_id="weather_etl",
    description="Daily weather ETL: Open-Meteo API -> clean -> validate -> Postgres star schema",
    doc_md=DOC_MD,
    start_date=pendulum.datetime(2024, 1, 1, tzinfo=local_tz),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "execution_timeout": timedelta(minutes=5),
        "on_failure_callback": task_failure_alert,
    },
    tags=["etl", "portfolio"],
)
def weather_etl():
    @task(execution_timeout=timedelta(minutes=5))
    def extract(data_interval_start=None, ds=None) -> str:
        from src.extract import extract_all

        # Align with Indian Standard Time calendar date
        target_day = (
            data_interval_start.in_timezone(local_tz).to_date_string()
            if data_interval_start
            else ds
        )
        return extract_all(day=target_day)

    @task(execution_timeout=timedelta(minutes=5))
    def transform(raw_dir: str, data_interval_start=None, ds=None) -> str:
        from src.transform import transform_day

        target_day = (
            data_interval_start.in_timezone(local_tz).to_date_string()
            if data_interval_start
            else ds
        )
        return transform_day(raw_dir=raw_dir, day=target_day)

    @task(execution_timeout=timedelta(minutes=5))
    def quality_check(csv_path: str) -> str:
        from src.quality import validate_csv

        return validate_csv(csv_path)

    @task(execution_timeout=timedelta(minutes=5))
    def load(csv_path: str) -> int:
        from src.load import load_csv

        return load_csv(csv_path)

    raw_dir = extract()
    staged_csv = transform(raw_dir)
    validated_csv = quality_check(staged_csv)
    load(validated_csv)


weather_etl()
