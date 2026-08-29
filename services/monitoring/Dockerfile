FROM python:3.11-slim
WORKDIR /app
COPY services/monitoring/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services /app/services
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "services.monitoring.app:app", "--host", "0.0.0.0", "--port", "8000"]
