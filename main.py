import os
import sqlite3
from datetime import datetime

from fastapi import FastAPI, HTTPException

app = FastAPI()
API_KEY = os.getenv("LOGLIFE_API_KEY", "my-secret-key")
DB_PATH = os.getenv("DB_PATH", "data/events.db")

# Initialize database
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT,
                value TEXT,
                timestamp DATETIME
            )
        """)
        conn.commit()

def verify_key(key: str):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/log")
def log_event(event_key: str, value: str, key: str):
    verify_key(key)
    timestamp = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO events (event_key, value, timestamp) VALUES (?, ?, ?)",
            (event_key, value, timestamp)
        )
        conn.commit()
    return {"ok": True}

@app.get("/logs")
def get_logs(key: str):
    verify_key(key)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT id, event_key, value, timestamp FROM events "
            "ORDER BY timestamp DESC LIMIT 100"
        )
        logs = [
            {"id": row[0], "event_key": row[1], "value": row[2], "timestamp": row[3]}
            for row in cursor.fetchall()
        ]
    return {"data": logs}

# Initialize database on startup
init_db()

