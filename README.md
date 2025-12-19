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
curl "http://localhost:8000/log?clave=temperatura&valor=25.5&key=mi-clave-secreta"
```

**Response:**
```json
{"ok": true}
```

### Query logs

```bash
curl "http://localhost:8000/logs?key=mi-clave-secreta"
```

**Response:**
```json
[
  {
    "id": 1,
    "clave": "temperatura",
    "valor": "25.5",
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
CREATE TABLE eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT,
    valor TEXT,
    timestamp DATETIME
)
```

## Endpoints

### GET /log

Saves an event to the database.

**Parameters:**
- `clave` (string): Event name
- `valor` (string): Event value
- `key` (string): API key for authentication

**Response:** `{"ok": true}`

### GET /logs

Retrieves the last 100 events ordered by timestamp in descending order.

**Parameters:**
- `key` (string): API key for authentication

**Response:** Array of events with `id`, `clave`, `valor`, `timestamp`

## Notes

- The `eventos.db` database is created automatically when starting the application
- Designed for low volume (~7-10 records/day)
- No complex dependencies, ideal for learning and iteration
- SQLite is sufficient for this data volume
