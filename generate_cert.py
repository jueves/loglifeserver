#!/usr/bin/env python3
"""
Generate self-signed TLS certificate for server identity verification.
This script creates a certificate and private key for HTTPS support.
"""

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta
import os
import hashlib

def generate_certificate(cert_path="certs/cert.pem", key_path="certs/key.pem"):
    """Generate a self-signed certificate for HTTPS."""

    # Create certs directory if it doesn't exist
    os.makedirs(os.path.dirname(cert_path), exist_ok=True)

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Private"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Private"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"LogLife Server"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=3650)  # Valid for 10 years
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"localhost"),
            x509.DNSName(u"*.localhost"),
            x509.IPAddress(u"127.0.0.1"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Write private key to file
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Write certificate to file
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Calculate and display certificate fingerprint
    cert_bytes = cert.public_bytes(serialization.Encoding.DER)
    fingerprint = hashlib.sha256(cert_bytes).hexdigest()

    print(f"✓ Certificate generated successfully!")
    print(f"  Certificate: {cert_path}")
    print(f"  Private Key: {key_path}")
    print(f"\n" + "="*70)
    print(f"CERTIFICATE FINGERPRINT (SHA-256):")
    print(f"{fingerprint}")
    print(f"="*70)
    print(f"\nSave this fingerprint for client verification!")
    print(f"Clients should verify this fingerprint before sending data.")

    # Save fingerprint to file for easy reference
    fingerprint_path = os.path.join(os.path.dirname(cert_path), "fingerprint.txt")
    with open(fingerprint_path, "w") as f:
        f.write(fingerprint)
    print(f"\nFingerprint also saved to: {fingerprint_path}")

    return fingerprint

if __name__ == "__main__":
    generate_certificate()
