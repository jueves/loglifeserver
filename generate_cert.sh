#!/bin/bash
# Script para generar certificados SSL autofirmados para servidor privado

set -e  # Exit on error

CERT_DIR="./certs"

# Verificar que openssl está instalado
if ! command -v openssl &> /dev/null; then
    echo "❌ Error: openssl no está instalado"
    echo "   Instálalo con: apt-get install openssl (Debian/Ubuntu)"
    echo "              o: yum install openssl (CentOS/RHEL)"
    exit 1
fi

# Crear directorio de certificados
if ! mkdir -p "$CERT_DIR" 2>/dev/null; then
    echo "❌ Error: No se puede crear el directorio $CERT_DIR"
    echo "   Verifica los permisos del directorio actual"
    echo "   Prueba ejecutar: sudo mkdir -p $CERT_DIR && sudo chown \$USER $CERT_DIR"
    exit 1
fi

# Verificar permisos de escritura
if [ ! -w "$CERT_DIR" ]; then
    echo "❌ Error: No tienes permisos de escritura en $CERT_DIR"
    echo "   Prueba ejecutar: sudo chown \$USER $CERT_DIR"
    exit 1
fi

echo "Generando certificados SSL autofirmados..."

# Generar certificados
if openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days 365 \
  -subj "/C=ES/ST=State/L=City/O=Organization/CN=localhost" 2>&1; then

    # Establecer permisos correctos
    chmod 600 "$CERT_DIR/key.pem"
    chmod 644 "$CERT_DIR/cert.pem"

    echo ""
    echo "✓ Certificados generados exitosamente en $CERT_DIR/"
    echo "  - cert.pem: Certificado público"
    echo "  - key.pem: Clave privada"
    echo ""
    echo "Nota: Estos son certificados autofirmados para uso privado."
    echo "Tu navegador mostrará una advertencia de seguridad - esto es normal."
    echo ""
    echo "Próximos pasos:"
    echo "1. Edita tu archivo .env y descomenta las líneas SSL:"
    echo "   SSL_CERT_PATH=certs/cert.pem"
    echo "   SSL_KEY_PATH=certs/key.pem"
    echo "2. Ejecuta: python start_server.py"
else
    echo ""
    echo "❌ Error: Falló la generación de certificados"
    echo "   Revisa los mensajes de error anteriores"
    exit 1
fi
