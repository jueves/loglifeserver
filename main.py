from fastapi import FastAPI, HTTPException
from datetime import datetime
import sqlite3
import os
import hashlib

app = FastAPI()
API_KEY = os.getenv("API_KEY", "my-secret-key")
DB_PATH = os.getenv("DB_PATH", "data/events.db")
CERT_PATH = os.getenv("CERT_PATH", "certs/cert.pem")
KEY_PATH = os.getenv("KEY_PATH", "certs/key.pem")

# Initialize database
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_key TEXT,
            value TEXT,
            timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

init_db()

def verify_key(key: str):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/log")
def log_event(event_key: str, value: str, key: str):
    verify_key(key)
    conn = sqlite3.connect(DB_PATH)
    timestamp = datetime.now().isoformat()
    conn.execute("INSERT INTO events (event_key, value, timestamp) VALUES (?, ?, ?)",
                 (event_key, value, timestamp))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/logs")
def get_logs(key: str):
    verify_key(key)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT id, event_key, value, timestamp FROM events ORDER BY timestamp DESC LIMIT 100"
    )
    logs = [{"id": row[0], "event_key": row[1], "value": row[2], "timestamp": row[3]}
            for row in cursor.fetchall()]
    conn.close()
    return logs

@app.get("/fingerprint")
def get_fingerprint():
    """
    Get the SHA-256 fingerprint of the server's TLS certificate.
    Clients should verify this fingerprint to ensure server identity.
    No authentication required - fingerprint is public information.
    """
    try:
        if not os.path.exists(CERT_PATH):
            raise HTTPException(
                status_code=503,
                detail="Certificate not found. Server may be running in HTTP mode."
            )

        # Read the certificate file
        with open(CERT_PATH, "rb") as f:
            cert_pem = f.read()

        # Parse PEM to get DER format for fingerprinting
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization

        cert = x509.load_pem_x509_certificate(cert_pem)
        cert_der = cert.public_bytes(serialization.Encoding.DER)

        # Calculate SHA-256 fingerprint
        fingerprint = hashlib.sha256(cert_der).hexdigest()

        return {
            "fingerprint": fingerprint,
            "algorithm": "sha256",
            "certificate_path": CERT_PATH
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading certificate: {str(e)}")
