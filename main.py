from fastapi import FastAPI, HTTPException
from datetime import datetime
import sqlite3
import os

app = FastAPI()
API_KEY = os.getenv("API_KEY", "my-secret-key")
DB_PATH = os.getenv("DB_PATH", "data/events.db")

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
