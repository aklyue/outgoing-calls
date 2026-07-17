FROM python:3.10-alpine

WORKDIR /app

ENV PYTHONPATH=/app/

COPY third-party/api.txt /app

RUN pip install -r api.txt

COPY .env ./
COPY ./src/api/storage ./api/storage

CMD ["python", "api/storage/main.py"]