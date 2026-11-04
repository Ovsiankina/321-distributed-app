FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

ENV PYTHONPATH=/app
ENV UPLOAD_DATA_DIR=/data/upload/incoming
ENV UPLOAD_JWT_SECRET=dev-upload-jwt-secret
EXPOSE 8003

HEALTHCHECK --interval=10s --timeout=5s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8003/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
