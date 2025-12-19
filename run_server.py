#!/usr/bin/env python3
"""
Start the LogLife server with optional HTTPS support.

Usage:
    python run_server.py              # Start with HTTPS (generates cert if needed)
    python run_server.py --http       # Start with HTTP only (insecure)
    python run_server.py --host 0.0.0.0 --port 8443
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Start LogLife server")
    parser.add_argument("--http", action="store_true", help="Run in HTTP mode (insecure)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, help="Port to bind to (default: 8443 for HTTPS, 8000 for HTTP)")
    args = parser.parse_args()

    # Determine default port based on mode
    if args.port is None:
        args.port = 8000 if args.http else 8443

    cert_path = os.getenv("CERT_PATH", "certs/cert.pem")
    key_path = os.getenv("KEY_PATH", "certs/key.pem")

    if args.http:
        # Run in HTTP mode
        print("⚠️  WARNING: Running in HTTP mode - NO ENCRYPTION, NO SERVER VERIFICATION")
        print(f"Starting server at http://{args.host}:{args.port}")
        cmd = ["uvicorn", "main:app", "--host", args.host, "--port", str(args.port)]
    else:
        # Check if certificate exists, generate if not
        if not Path(cert_path).exists() or not Path(key_path).exists():
            print(f"Certificate not found at {cert_path}")
            print("Generating self-signed certificate...")
            subprocess.run([sys.executable, "generate_cert.py"], check=True)
            print()

        # Run in HTTPS mode
        print(f"✓ Starting server with HTTPS at https://{args.host}:{args.port}")
        print(f"  Certificate: {cert_path}")
        print(f"  Private Key: {key_path}")

        # Display fingerprint if available
        fingerprint_path = Path(cert_path).parent / "fingerprint.txt"
        if fingerprint_path.exists():
            fingerprint = fingerprint_path.read_text().strip()
            print(f"\n{'='*70}")
            print(f"CERTIFICATE FINGERPRINT (SHA-256):")
            print(f"{fingerprint}")
            print(f"{'='*70}")
            print(f"Clients should verify this fingerprint before sending data.")
            print()

        cmd = [
            "uvicorn", "main:app",
            "--host", args.host,
            "--port", str(args.port),
            "--ssl-keyfile", key_path,
            "--ssl-certfile", cert_path
        ]

    # Start the server
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")

if __name__ == "__main__":
    main()
