#!/usr/bin/env bash
# S-03 — Genera certificado auto-firmado para desarrollo local.
# Para producción, usar Let's Encrypt (Certbot) o certificado CA real.
#
# Uso:
#   chmod +x generate-dev-certs.sh
#   ./generate-dev-certs.sh
#
# Resultado: certs/server.key y certs/server.crt (2 años de validez)

set -euo pipefail

CERTS_DIR="$(dirname "$0")/certs"
mkdir -p "$CERTS_DIR"

openssl req -x509 -nodes \
  -newkey rsa:4096 \
  -keyout "$CERTS_DIR/server.key" \
  -out    "$CERTS_DIR/server.crt" \
  -days   730 \
  -subj   "/C=DO/ST=DN/L=Santo Domingo/O=SIRCCD/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$CERTS_DIR/server.key"
echo "Certificado generado en $CERTS_DIR/"
echo "  server.key — clave privada (NO COMMITEAR)"
echo "  server.crt — certificado público"
