# Dockerfile for QRManaShinYi webserver
FROM python:3.11-slim

# Create app user
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Install system deps required by Pillow and others
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir httpx==0.25.2 \
    && pip install --no-cache-dir python-multipart==0.0.6


# Copy application
COPY . /app
RUN chown -R app:app /app
USER app

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "webserver.main:app", "--host", "0.0.0.0", "--port", "8000"]
