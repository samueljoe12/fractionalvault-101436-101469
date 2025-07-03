#!/bin/bash
# Script to generate self-signed SSL cert/key for local/dev HTTPS FastAPI server

CERT_FILE="ssl.crt"
KEY_FILE="ssl.key"

if [[ -f "${CERT_FILE}" && -f "${KEY_FILE}" ]]; then
  echo "SSL certificate and key already exist."
else
  echo "Generating self-signed certificate and key..."
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "${KEY_FILE}" -out "${CERT_FILE}" \
    -subj "/CN=localhost"
  echo "Self-signed certificate and key generated: ${CERT_FILE}, ${KEY_FILE}"
fi
