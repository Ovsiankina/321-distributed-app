FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY fixtures /app/fixtures

ENV PYTHONPATH=/app
ENV CATALOG_FIXTURES_DIR=/app/fixtures
ENV CATALOG_DATABASE_URL=mariadb+pymysql://catalog@catalog-db:3306/catalog
ENV CATALOG_DB_PASSWORD=catalog
EXPOSE 8002

HEALTHCHECK --interval=10s --timeout=5s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
