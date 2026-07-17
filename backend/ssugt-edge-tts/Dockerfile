FROM python:3.11-slim

# Добавляем ffmpeg в список устанавливаемых пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
ENV PYTHONPATH=/app

COPY src/edge_tts_service ./edge_tts_service

CMD ["python3", "edge_tts_service/main.py"]