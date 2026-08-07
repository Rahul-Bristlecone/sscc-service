FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required by ReportLab / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and install dependencies first (layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Copy application source
COPY src/ ./src/
COPY run.py ./

ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app/src

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
