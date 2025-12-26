# LogLife - Personal Data Recording API

Minimalist REST API for recording life data with flexible JSON structure using FastAPI and SQLite.

## Features

- 🔒 API key authentication
- 💾 Embedded SQLite database with JSON support
- 📊 Flexible schema - record any data structure
- ⏱️ Support for historical timestamps
- ✏️ Easy corrections via delete + recreate
- 🐳 Docker support with persistent volumes

## Installation

### Option 1: Docker (Recommended)

```bash
# Using docker-compose
docker-compose up -d

# Or build and run with Docker
docker build -t loglife-api .
docker run -d -p 3001:3001 -v $(pwd)/data:/app/data loglife-api
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

# 5. Verify HTTPS is enabled
docker-compose logs api
# You should see: "🔒 Starting HTTPS server at https://0.0.0.0:3001"
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

# Record current data
./loglife record '{"temperature":25.5,"humidity":60}'

# Record past event
./loglife record --timestamp '2025-12-20T14:30:00' '{"workout":"running","duration":30,"distance":5.2}'

# Query all records
./loglife query

# Query specific date
./loglife query --date 2025-12-20

# Query date range
./loglife query --from 2025-12-01 --to 2025-12-31

# Delete a record (for corrections)
./loglife delete 123
```

**Alternative**: Use environment variables directly
```bash
export LOGLIFE_SERVER=http://localhost:3001
export LOGLIFE_API_KEY=your-secret-key
./loglife record '{"temperature":25.5}'
```

**Optional**: Copy to PATH for system-wide use
```bash
sudo cp loglife /usr/local/bin/
```

## Data Model

The system uses a flexible JSON-based schema that allows you to record any data structure:

### Database Schema

```sql
CREATE TABLE records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,        -- When the event happened
    data JSON NOT NULL,                 -- Your flexible data structure
    created_at DATETIME NOT NULL        -- When you recorded it
)
```

### Example Records

```json
{
  "id": 1,
  "timestamp": "2025-12-20T14:30:00",
  "data": {
    "workout": "running",
    "duration": 30,
    "distance": 5.2,
    "heart_rate": 145
  },
  "created_at": "2025-12-20T14:35:00"
}
```

```json
{
  "id": 2,
  "timestamp": "2025-12-20T08:00:00",
  "data": {
    "meal": "breakfast",
    "calories": 450,
    "protein": 25,
    "carbs": 55
  },
  "created_at": "2025-12-20T08:15:00"
}
```

## API Endpoints

### POST /record

Create a new record with optional custom timestamp.

**Headers:**
- `X-API-Key`: Your API key (required)

**Request Body:**
```json
{
  "timestamp": "2025-12-20T14:30:00",  // Optional, defaults to now
  "data": {
    "temperature": 25.5,
    "humidity": 60
  }
}
```

**Response:**
```json
{
  "ok": true,
  "id": 123
}
```

**Example:**
```bash
curl -X POST http://localhost:3001/record \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"data": {"temperature": 25.5, "humidity": 60}}'
```

### GET /records

Query records with optional filters.

**Headers:**
- `X-API-Key`: Your API key (required)

**Query Parameters:**
- `limit`: Maximum number of records (default: 100)
- `date`: Filter by specific date (YYYY-MM-DD)
- `from_date`: Start date for range filter (YYYY-MM-DD)
- `to_date`: End date for range filter (YYYY-MM-DD)

**Response:**
```json
{
  "data": [
    {
      "id": 123,
      "timestamp": "2025-12-20T14:30:00",
      "data": {
        "temperature": 25.5,
        "humidity": 60
      },
      "created_at": "2025-12-20T14:35:00"
    }
  ]
}
```

**Examples:**
```bash
# Get all records (up to 100)
curl -H "X-API-Key: your-api-key" \
  http://localhost:3001/records

# Get records for specific date
curl -H "X-API-Key: your-api-key" \
  "http://localhost:3001/records?date=2025-12-20"

# Get records for date range
curl -H "X-API-Key: your-api-key" \
  "http://localhost:3001/records?from_date=2025-12-01&to_date=2025-12-31"

# Limit results
curl -H "X-API-Key: your-api-key" \
  "http://localhost:3001/records?limit=10"
```

### DELETE /record/{id}

Delete a record by ID.

**Headers:**
- `X-API-Key`: Your API key (required)

**Response:**
```json
{
  "ok": true
}
```

**Example:**
```bash
curl -X DELETE -H "X-API-Key: your-api-key" \
  http://localhost:3001/record/123
```

## Making Corrections

To correct a record, delete the incorrect one and create a new one with the correct data and original timestamp:

```bash
# Delete incorrect record
./loglife delete 123

# Create corrected record with original timestamp
./loglife record --timestamp '2025-12-20T14:30:00' '{"workout":"running","duration":35}'
```

This approach keeps the data simple and maintains a clean audit trail via the `created_at` field.

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

## Migration from Old Format

If you have an existing database with the old `events` table (event_key, value, timestamp), the system will automatically migrate it to the new format on startup:

- Old format: `event_key="temperature", value="25.5"`
- New format: `data={"temperature": "25.5"}`

The migration happens automatically and the old table is removed after successful migration.

## Docker Details

### Volume Persistence

The database is stored in `./data/events.db` and mounted as a volume in Docker, ensuring data persists across container restarts.

### Environment Variables

- `LOGLIFE_API_KEY`: Authentication key (required, set in `.env` file)
- `DB_PATH`: Database file path (default: `data/events.db`)
- `PORT`: Server port (default: `3001`)
- `SSL_CERT_PATH`: Path to SSL certificate (optional, for HTTPS)
- `SSL_KEY_PATH`: Path to SSL private key (optional, for HTTPS)

### Stop Container

```bash
docker-compose down
```

## Examples

### Track Daily Variables

```bash
# Morning routine
./loglife record '{"weight":75.2,"sleep_hours":7.5,"mood":"good"}'

# Workout
./loglife record '{"workout":"running","duration":30,"distance":5.2}'

# Meal
./loglife record '{"meal":"lunch","calories":650,"protein":35}'

# Evening metrics
./loglife record '{"productivity":8,"stress":3,"energy":7}'
```

### Record Past Events

```bash
# Forgot to log yesterday's workout
./loglife record --timestamp '2025-12-19T18:00:00' \
  '{"workout":"cycling","duration":45,"distance":15}'
```

### Query and Analyze

```bash
# See all records from last week
./loglife query --from 2025-12-13 --to 2025-12-20

# See records from specific day
./loglife query --date 2025-12-20

# Get latest 10 records
./loglife query --limit 10
```

## Notes

- The database is created automatically in the `data/` directory when starting the application
- With Docker, data persists in the mounted volume
- Designed for personal use with flexible data recording
- All timestamps use ISO 8601 format
- Records are returned in descending order by timestamp (most recent first)
