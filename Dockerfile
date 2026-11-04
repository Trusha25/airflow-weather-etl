FROM apache/airflow:2.9.3

USER airflow
COPY --chown=airflow:root requirements.txt /requirements.txt
RUN pip install --no-cache-dir --user -r /requirements.txt
