FROM python:3.11-slim
WORKDIR /app
COPY services/pipeline/requirements.txt /tmp/pipeline-requirements.txt
COPY services/orchestration/requirements.txt /tmp/orchestration-requirements.txt
RUN pip install --no-cache-dir -r /tmp/pipeline-requirements.txt -r /tmp/orchestration-requirements.txt
COPY config /app/config
COPY warehouse /app/warehouse
COPY services /app/services
COPY data /app/data
ENV PYTHONPATH=/app
ENV DAGSTER_HOME=/app/runtime/dagster
RUN mkdir -p /app/runtime/dagster /app/runtime/models /app/runtime/reports /app/runtime/artifacts
EXPOSE 3000
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000", "-m", "services.orchestration.repository"]
