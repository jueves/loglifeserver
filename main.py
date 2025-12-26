import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

app = FastAPI()
API_KEY = os.getenv("LOGLIFE_API_KEY", "my-secret-key")
DB_PATH = os.getenv("DB_PATH", "data/events.db")


class RecordCreate(BaseModel):
    timestamp: Optional[str] = None
    data: Dict[str, Any]


class RecordResponse(BaseModel):
    id: int
    timestamp: str
    data: Dict[str, Any]
    created_at: str


def verify_key(key: Optional[str]):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def init_db():
    """Initialize database and migrate old data if needed"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Check if old events table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
        )
        old_table_exists = cursor.fetchone() is not None

        # Create new records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                data JSON NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)

        # Migrate data from old table if it exists
        if old_table_exists:
            cursor.execute("SELECT COUNT(*) FROM records")
            records_count = cursor.fetchone()[0]

            # Only migrate if records table is empty
            if records_count == 0:
                cursor.execute("SELECT id, event_key, value, timestamp FROM events")
                old_events = cursor.fetchall()

                if old_events:
                    print(f"Migrating {len(old_events)} events to new format...")
                    for old_id, event_key, value, timestamp in old_events:
                        # Convert to new format: {event_key: value}
                        data = json.dumps({event_key: value})
                        cursor.execute(
                            "INSERT INTO records (timestamp, data, created_at) VALUES (?, ?, ?)",
                            (timestamp, data, timestamp)
                        )
                    print(f"Migration complete!")

            # Drop old table after successful migration
            cursor.execute("DROP TABLE IF EXISTS events")

        conn.commit()


@app.post("/record")
def create_record(
    record: RecordCreate,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Create a new record with optional custom timestamp"""
    verify_key(x_api_key)

    # Use provided timestamp or default to now
    timestamp = record.timestamp if record.timestamp else datetime.now().isoformat()
    created_at = datetime.now().isoformat()

    # Validate timestamp format
    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format (e.g., 2025-12-20T14:30:00)")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO records (timestamp, data, created_at) VALUES (?, ?, ?)",
            (timestamp, json.dumps(record.data), created_at)
        )
        record_id = cursor.lastrowid
        conn.commit()

    return {"ok": True, "id": record_id}


@app.delete("/record/{record_id}")
def delete_record(
    record_id: int,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Delete a record by ID"""
    verify_key(x_api_key)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")

    return {"ok": True}


@app.get("/records")
def get_records(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    limit: int = 100,
    date: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """
    Query records with optional filters

    - limit: Maximum number of records to return (default: 100)
    - date: Filter by specific date (YYYY-MM-DD)
    - from_date: Filter by start date (YYYY-MM-DD)
    - to_date: Filter by end date (YYYY-MM-DD)
    """
    verify_key(x_api_key)

    query = "SELECT id, timestamp, data, created_at FROM records WHERE 1=1"
    params = []

    # Filter by specific date
    if date:
        query += " AND DATE(timestamp) = ?"
        params.append(date)

    # Filter by date range
    if from_date:
        query += " AND DATE(timestamp) >= ?"
        params.append(from_date)

    if to_date:
        query += " AND DATE(timestamp) <= ?"
        params.append(to_date)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(query, params)
        records = [
            {
                "id": row[0],
                "timestamp": row[1],
                "data": json.loads(row[2]),
                "created_at": row[3]
            }
            for row in cursor.fetchall()
        ]

    return {"data": records}


# Initialize database on startup
init_db()
