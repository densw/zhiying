FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY services/pipeline/requirements.txt /tmp/pipeline-requirements.txt
RUN pip install --no-cache-dir -r /tmp/pipeline-requirements.txt

COPY config /app/config
COPY warehouse /app/warehouse
COPY services /app/services
COPY data /app/data
RUN mkdir -p /app/runtime/artifacts /app/runtime/models /app/runtime/reports

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.pipeline.cli", "run-all"]
