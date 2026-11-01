#!/usr/bin/env bash
set -e

airflow db migrate

airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com || true

airflow scheduler &
SCHEDULER_PID=$!

cleanup() {
  echo "Shutting down Airflow scheduler and webserver..."
  kill -TERM "$SCHEDULER_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGTERM SIGINT

exec airflow webserver
