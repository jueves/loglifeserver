#!/bin/bash
# Script to generate self-signed SSL certificates for private server

set -e  # Exit on error

CERT_DIR="./certs"

# Check if openssl is installed
if ! command -v openssl &> /dev/null; then
    echo "❌ Error: openssl is not installed"
    echo "   Install with: apt-get install openssl (Debian/Ubuntu)"
    echo "             or: yum install openssl (CentOS/RHEL)"
    exit 1
fi

# Create certificates directory
if ! mkdir -p "$CERT_DIR" 2>/dev/null; then
    echo "❌ Error: Cannot create directory $CERT_DIR"
    echo "   Check permissions of current directory"
    echo "   Try running: sudo mkdir -p $CERT_DIR && sudo chown \$USER $CERT_DIR"
    exit 1
fi

# Check write permissions
if [ ! -w "$CERT_DIR" ]; then
    echo "❌ Error: You don't have write permissions in $CERT_DIR"
    echo "   Try running: sudo chown \$USER $CERT_DIR"
    exit 1
fi

echo "Generating self-signed SSL certificates..."

# Generate certificates
if openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" 2>&1; then

    # Set correct permissions
    chmod 600 "$CERT_DIR/key.pem"
    chmod 644 "$CERT_DIR/cert.pem"

    echo ""
    echo "✓ Certificates generated successfully in $CERT_DIR/"
    echo "  - cert.pem: Public certificate"
    echo "  - key.pem: Private key"
    echo ""
    echo "Note: These are self-signed certificates for private use."
    echo "Your browser will show a security warning - this is normal."
    echo ""
    echo "Next steps:"
    echo "1. Edit your .env file and uncomment the SSL lines:"
    echo "   SSL_CERT_PATH=certs/cert.pem"
    echo "   SSL_KEY_PATH=certs/key.pem"
    echo "2. Run: python start_server.py"
else
    echo ""
    echo "❌ Error: Certificate generation failed"
    echo "   Check the error messages above"
    exit 1
fi
