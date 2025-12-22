#!/usr/bin/env python3
"""
Server startup script with optional HTTPS support
"""
import os
import sys
import uvicorn

def main():
    # Basic configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3001"))

    # SSL configuration (optional)
    ssl_cert = os.getenv("SSL_CERT_PATH")
    ssl_key = os.getenv("SSL_KEY_PATH")

    config = {
        "app": "main:app",
        "host": host,
        "port": port,
        "reload": os.getenv("RELOAD", "false").lower() == "true"
    }

    # If SSL certificates are configured, enable HTTPS
    if ssl_cert and ssl_key:
        if not os.path.exists(ssl_cert):
            print(f"Error: Certificate not found at {ssl_cert}")
            sys.exit(1)
        if not os.path.exists(ssl_key):
            print(f"Error: Private key not found at {ssl_key}")
            sys.exit(1)

        config["ssl_certfile"] = ssl_cert
        config["ssl_keyfile"] = ssl_key
        print(f"🔒 Starting HTTPS server at https://{host}:{port}")
    else:
        print(f"🌐 Starting HTTP server at http://{host}:{port}")

    # Start server
    uvicorn.run(**config)

if __name__ == "__main__":
    main()
