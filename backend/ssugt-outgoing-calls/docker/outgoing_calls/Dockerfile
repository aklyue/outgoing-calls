FROM python:3.10-slim

WORKDIR /app

ENV PYTHONPATH=/app/

COPY third-party/api.txt /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    ffmpeg \
    supervisor \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxinerama1 \
    fonts-dejavu \
    mesa-utils \
    libreoffice \
    libreoffice-java-common \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r api.txt

COPY .env ./
COPY alembic.ini ./
COPY ./src/api/outgoing_calls ./api/outgoing_calls

CMD alembic upgrade head && python -u api/outgoing_calls/main.py
