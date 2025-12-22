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
docker run -d -p 3001:3001 -v $(pwd)/data:/app/data logging-api
```

### Option 2: Local Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run server (HTTP)
python start_server.py

# Or with reload for development
RELOAD=true python start_server.py
```

The server will be available at `http://localhost:3001`

## HTTPS Configuration (Private Server)

To use HTTPS on your private server:

### 1. Generate self-signed certificates

```bash
./generate_cert.sh
```

This will create certificates in the `certs/` directory:
- `cert.pem`: Public certificate
- `key.pem`: Private key

### 2. Configure environment variables

Edit your `.env` file and uncomment the SSL lines:

```bash
SSL_CERT_PATH=certs/cert.pem
SSL_KEY_PATH=certs/key.pem
```

### 3. Update client URL

Change the URL in your `.env` to use HTTPS:

```bash
LOGLIFE_SERVER=https://localhost:3001
```

### 4. Start the server

```bash
python start_server.py
```

The server will now be available at `https://localhost:3001`

**Note about self-signed certificates:**
- Browsers will show a security warning - this is normal
- For script usage, you may need to disable SSL verification:
  - curl: use `-k` or `--insecure`
  - The `./loglife` client handles this automatically

### Docker with HTTPS

To use HTTPS with Docker:

```bash
# 1. Generate certificates first
./generate_cert.sh

# 2. Edit .env and uncomment the SSL lines:
# SSL_CERT_PATH=certs/cert.pem
# SSL_KEY_PATH=certs/key.pem

# 3. Edit docker-compose.yml and uncomment the SSL variables

# 4. Start container
docker-compose up -d

# 4. Verificar que está usando HTTPS
docker-compose logs api
# Deberías ver: "🔒 Iniciando servidor HTTPS en https://0.0.0.0:3001"
```

The `certs/` directory is automatically mounted in the container.

## Usage

### Bash Client (Recommended)

The client script automatically reads configuration from a `.env` file if present:

```bash
# Create .env file (already git-ignored)
cp .env.example .env

# Edit .env with your settings
# LOGLIFE_SERVER=http://localhost:3001
# LOGLIFE_API_KEY=your-secret-key

# Log an event
./loglife log temperature 25.5

# Log with spaces in value (use quotes)
./loglife log message "this is the variable value"

# Query logs
./loglife query
```

**Alternative**: Use environment variables directly
```bash
export LOGLIFE_SERVER=http://localhost:3001
export LOGLIFE_API_KEY=your-secret-key
./loglife log temperature 25.5
```

**Optional**: Copy to PATH for system-wide use
```bash
sudo cp loglife /usr/local/bin/
```

### Manual API Usage (curl)

#### Log an event

```bash
curl "http://localhost:3001/log?event_key=temperature&value=25.5&key=your-api-key"
```

**Response:**
```json
{"ok": true}
```

#### Query logs

```bash
curl "http://localhost:3001/logs?key=your-api-key"
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "event_key": "temperature",
      "value": "25.5",
      "timestamp": "2025-12-19T10:35:00.123456"
    }
  ]
}
```

## Configuration

### Server Configuration (Safe for Git Pull)

Create a `.env` file in the project root (this file is git-ignored and won't be overwritten):

```bash
cp .env.example .env
```

Edit `.env` to set your API key:

```
LOGLIFE_API_KEY=your-secret-key-here
DB_PATH=data/events.db
```

**Security Note:** Always change the default LOGLIFE_API_KEY before deploying to production. Never commit your `.env` file to version control.

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

- `LOGLIFE_API_KEY`: Authentication key (required, set in `.env` file)
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
