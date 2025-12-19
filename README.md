# Simple Logging API

Minimalist REST API for logging events with key-value structure using FastAPI and SQLite.

## Features

- 🚀 Ultra-minimalist (~48 lines of code)
- 🔒 API key authentication
- 💾 Embedded SQLite database
- ⏱️ Automatic timestamps
- 📊 Query last 100 records

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run server

```bash
uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`

### Log an event

```bash
curl "http://localhost:8000/log?event_key=temperature&value=25.5&key=my-secret-key"
```

**Response:**
```json
{"ok": true}
```

### Query logs

```bash
curl "http://localhost:8000/logs?key=my-secret-key"
```

**Response:**
```json
[
  {
    "id": 1,
    "event_key": "temperature",
    "value": "25.5",
    "timestamp": "2025-12-19T10:35:00.123456"
  }
]
```

## Configuration

### Change API Key

Edit the `main.py` file and modify the constant:

```python
API_KEY = "your-secret-key-here"
```

## Database Structure

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key TEXT,
    value TEXT,
    timestamp DATETIME
)
```

## Endpoints

### GET /log

Saves an event to the database.

**Parameters:**
- `event_key` (string): Event name
- `value` (string): Event value
- `key` (string): API key for authentication

**Response:** `{"ok": true}`

### GET /logs

Retrieves the last 100 events ordered by timestamp in descending order.

**Parameters:**
- `key` (string): API key for authentication

**Response:** Array of events with `id`, `event_key`, `value`, `timestamp`

## Notes

- The `events.db` database is created automatically when starting the application
- Designed for low volume (~7-10 records/day)
- No complex dependencies, ideal for learning and iteration
- SQLite is sufficient for this data volume
