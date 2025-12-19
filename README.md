# Simple Logging API

Minimalist REST API for logging events with key-value structure using FastAPI and SQLite.

## Features

- 🚀 Ultra-minimalist (~55 lines of code)
- 🔒 API key authentication
- 💾 Embedded SQLite database
- ⏱️ Automatic timestamps
- 📊 Query last 100 records
- 🐳 Docker support with persistent volumes

## Installation

### Option 1: Docker (Recommended)

```bash
# Using docker-compose
docker-compose up -d

# Or build and run with Docker
docker build -t logging-api .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data logging-api
```

### Option 2: Local Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`

## Usage

### Log an event

```bash
curl "http://localhost:8000/log?event_key=temperature&value=25.5&key=your-api-key"
```

**Response:**
```json
{"ok": true}
```

### Query logs

```bash
curl "http://localhost:8000/logs?key=your-api-key"
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

### Server Configuration (Safe for Git Pull)

Create a `.env` file in the project root (this file is git-ignored and won't be overwritten):

```bash
cp .env.example .env
```

Edit `.env` to set your API key:

```
API_KEY=your-secret-key-here
DB_PATH=data/events.db
```

**Security Note:** Always change the default API_KEY before deploying to production. Never commit your `.env` file to version control.

**Note:** The `.env` file is automatically loaded by docker-compose and is ignored by git, so your configuration persists across updates when you `git pull`.

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

## Docker Details

### Volume Persistence

The database is stored in `./data/events.db` and mounted as a volume in Docker, ensuring data persists across container restarts.

### Environment Variables

- `API_KEY`: Authentication key (required, set in `.env` file)
- `DB_PATH`: Database file path (default: `data/events.db`)

### Stop Container

```bash
docker-compose down
```

## Notes

- The database is created automatically in the `data/` directory when starting the application
- With Docker, data persists in the mounted volume
- Designed for low volume (~7-10 records/day)
- No complex dependencies, ideal for learning and iteration
- SQLite is sufficient for this data volume
