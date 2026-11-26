FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

ENV PYTHONPATH=/app
ENV UPLOAD_DATA_DIR=/data/videos
EXPOSE 8003

HEALTHCHECK --interval=10s --timeout=5s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8003/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
