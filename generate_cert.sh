#!/bin/bash
# Script para generar certificados SSL autofirmados para servidor privado

CERT_DIR="./certs"
mkdir -p "$CERT_DIR"

echo "Generando certificados SSL autofirmados..."

openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days 365 \
  -subj "/C=ES/ST=State/L=City/O=Organization/CN=localhost"

chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo "✓ Certificados generados en $CERT_DIR/"
echo "  - cert.pem: Certificado público"
echo "  - key.pem: Clave privada"
echo ""
echo "Nota: Estos son certificados autofirmados para uso privado."
echo "Tu navegador mostrará una advertencia de seguridad - esto es normal."
