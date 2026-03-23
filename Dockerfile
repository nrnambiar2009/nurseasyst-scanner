FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libzbar0 \
    libdmtx0b \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .

CMD gunicorn app:app --bind 0.0.0.0:$PORT