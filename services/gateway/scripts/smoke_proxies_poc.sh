#!/usr/bin/env bash
# Smoke manuel : gateway (127.0.0.1:8000) → auth/streaming du stack poc-gateway (Docker).
# Prérequis : conteneurs poc-gateway-auth-1, poc-gateway-streaming-1, catalog lab sur 8002.
set -euo pipefail

auth_ip="$(docker inspect poc-gateway-auth-1 -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')"
stream_ip="$(docker inspect poc-gateway-streaming-1 -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')"
poc_cat_ip="$(docker inspect poc-gateway-catalog-1 -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')"

if [[ -z "$auth_ip" || -z "$stream_ip" ]]; then
  echo "POC auth/streaming introuvables (docker ps | grep poc-gateway)" >&2
  exit 1
fi

video_id="$(curl -sf "http://${poc_cat_ip}:8002/api/catalog/videos" | python3 -c "import json,sys; print(json.load(sys.stdin)['items'][0]['id'])")"

export GATEWAY_CATALOG_URL="${GATEWAY_CATALOG_URL:-http://127.0.0.1:8002}"
export GATEWAY_AUTH_URL="http://${auth_ip}:8001"
export GATEWAY_STREAMING_URL="http://${stream_ip}:8003"

echo "GATEWAY_AUTH_URL=$GATEWAY_AUTH_URL"
echo "GATEWAY_STREAMING_URL=$GATEWAY_STREAMING_URL"
echo "video_id (POC catalog)=$video_id"

if ! curl -sf http://127.0.0.1:8000/health >/dev/null; then
  echo "Gateway absent sur :8000. Lancer :" >&2
  echo "  cd services/gateway && source .venv/bin/activate" >&2
  echo "  export GATEWAY_CATALOG_URL GATEWAY_AUTH_URL GATEWAY_STREAMING_URL" >&2
  echo "  uvicorn app.main:app --reload --port 8000" >&2
  exit 1
fi

echo -n "GET /api/auth/me via gateway → "
auth_code="$(curl -s -o /tmp/smoke-auth.json -w '%{http_code}' http://127.0.0.1:8000/api/auth/me)"
echo "$auth_code"
if [[ "$auth_code" != "401" ]]; then
  echo "Attendu 401 sans JWT (proxy vers auth POC)" >&2
  exit 1
fi
grep -q Authentification /tmp/smoke-auth.json && echo "  (corps auth POC = proxy OK)"

echo -n "GET /api/stream/${video_id} via gateway → "
code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8000/api/stream/${video_id}?quality=720p")"
echo "$code"
if [[ "$code" != "200" ]]; then
  echo "Échec streaming smoke" >&2
  exit 1
fi

echo "Smoke auth + streaming OK."
