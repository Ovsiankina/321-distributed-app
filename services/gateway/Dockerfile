FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

ENV PYTHONPATH=/app
ENV GATEWAY_PORT=8000
ENV GATEWAY_SUBTITLES_URL=http://host.docker.internal:8004
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${GATEWAY_PORT}"]
