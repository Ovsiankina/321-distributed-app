FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY fixtures /app/fixtures

ENV PYTHONPATH=/app
ENV CATALOG_DATA_DIR=/data/catalog
ENV CATALOG_FIXTURES_DIR=/app/fixtures
ENV CATALOG_VIDEOS_DIR=/data/videos
ENV CATALOG_SUBTITLES_DIR=/data/subtitles
ENV CATALOG_DATABASE_URL=mariadb+pymysql://catalog:catalog@catalog-db:3306/catalog
EXPOSE 8002

HEALTHCHECK --interval=10s --timeout=5s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
