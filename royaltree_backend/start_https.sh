#!/bin/bash
# Launch the Royaltree Backend with HTTPS (uvicorn/FastAPI) on the expected port 3001 with self-signed SSL cert
# Usage: bash start_https.sh

set -e
cd "$(dirname "$0")"

CERT="ssl.crt"
KEY="ssl.key"

if [[ ! -f "$CERT" || ! -f "$KEY" ]]; then
  echo "Generating self-signed SSL certificate/key..."
  bash generate_selfsigned_cert.sh
else
  echo "SSL certificate and key found: $CERT, $KEY"
fi

echo "Starting FastAPI backend with HTTPS on port 3001 ..."
# The --reload flag enables auto-reload on code changes (good for dev)
uvicorn src.api.main:app \
  --host 0.0.0.0 \
  --port 3001 \
  --reload \
  --ssl-keyfile "$KEY" \
  --ssl-certfile "$CERT" \
  --log-level debug
