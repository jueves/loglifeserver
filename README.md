# Simple Logging API

Minimalist REST API for logging events with key-value structure using FastAPI and SQLite.

## Features

- 🚀 Ultra-minimalist (~55 lines of code)
- 🔒 API key authentication
- 🔐 **HTTPS with certificate pinning for server identity verification**
- 💾 Embedded SQLite database
- ⏱️ Automatic timestamps
- 📊 Query last 100 records
- 🐳 Docker support with persistent volumes

## Installation

### Option 1: Docker (Recommended)

```bash
# Using docker-compose (HTTPS enabled by default on port 8443)
docker-compose up -d

# Or build and run with Docker
docker build -t logging-api .
docker run -d -p 8443:8443 -v $(pwd)/data:/app/data -v $(pwd)/certs:/app/certs logging-api
```

### Option 2: Local Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run server with HTTPS (recommended)
python run_server.py

# Or run with HTTP only (insecure, not recommended)
python run_server.py --http
```

The server will be available at:
- **HTTPS (recommended):** `https://localhost:8443`
- **HTTP (insecure):** `http://localhost:8000` (if using `--http` flag)

## Security - Server Identity Verification

### Why Server Identity Verification?

If you access your server over a VPN, **losing the VPN connection could route your requests to the wrong server**, potentially exposing your API key and data to an attacker. This implementation provides **certificate pinning** to verify you're always communicating with YOUR server.

### How It Works

1. **Server generates a self-signed TLS certificate** (happens automatically on first run)
2. **Certificate has a unique fingerprint** (like a cryptographic fingerprint)
3. **Clients verify the fingerprint** before sending data
4. **If fingerprint doesn't match → connection refused**

This prevents man-in-the-middle attacks even if your VPN drops.

### Setup Server Identity Verification

#### Step 1: Generate Certificate (First Time)

When you first start the server, it will automatically generate a certificate:

```bash
# Start server (generates certificate if not present)
python run_server.py

# Or manually generate
python generate_cert.py
```

You'll see output like:
```
✓ Certificate generated successfully!
======================================================================
CERTIFICATE FINGERPRINT (SHA-256):
a1b2c3d4e5f6...your_fingerprint_here...
======================================================================
Save this fingerprint for client verification!
```

**IMPORTANT:** Save this fingerprint! Clients will need it to verify server identity.

#### Step 2: Get Fingerprint from Running Server

You can retrieve the fingerprint anytime via the API:

```bash
curl -k https://localhost:8443/fingerprint
```

Response:
```json
{
  "fingerprint": "a1b2c3d4e5f6...",
  "algorithm": "sha256",
  "certificate_path": "certs/cert.pem"
}
```

Or read from file:
```bash
cat certs/fingerprint.txt
```

#### Step 3: Configure Client to Verify Server

Use the example client with certificate pinning:

```bash
# First time: save the server fingerprint
python example_client.py --server https://your-server:8443 --save-fingerprint

# Regular use: client automatically verifies fingerprint
python example_client.py --server https://your-server:8443 --api-key YOUR_KEY --get-logs
```

The client will:
1. ✅ Connect to server
2. ✅ Retrieve certificate
3. ✅ Calculate fingerprint
4. ✅ Compare with saved fingerprint
5. ✅ **ONLY proceed if match** ⚠️ Refuse if mismatch

### Example Client Usage

```bash
# Save fingerprint (first time setup)
python example_client.py --server https://192.168.1.100:8443 --save-fingerprint

# Log an event (with verification)
python example_client.py \
  --server https://192.168.1.100:8443 \
  --api-key my-secret-key \
  --log --event temperature --value 25.5

# Get logs (with verification)
python example_client.py \
  --server https://192.168.1.100:8443 \
  --api-key my-secret-key \
  --get-logs
```

### What Happens If VPN Drops?

**Without verification (old way):**
```
VPN drops → Request goes to wrong server → Data leaked ❌
```

**With verification (new way):**
```
VPN drops → Request goes to wrong server → Fingerprint mismatch →
Connection refused → Data protected ✅
```

You'll see an error:
```
🚨 SECURITY ERROR 🚨
Server identity verification FAILED!
Expected: a1b2c3d4e5f6...
Actual:   9z8y7x6w5v4u...
⚠️  DO NOT SEND DATA - You may be connected to the wrong server!
```

## Usage

### Log an event

```bash
# Using HTTPS (recommended, requires -k flag for self-signed cert)
curl -k "https://localhost:8443/log?event_key=temperature&value=25.5&key=my-secret-key"

# Or using HTTP (not recommended)
curl "http://localhost:8000/log?event_key=temperature&value=25.5&key=my-secret-key"
```

**Response:**
```json
{"ok": true}
```

### Query logs

```bash
# Using HTTPS (recommended)
curl -k "https://localhost:8443/logs?key=my-secret-key"

# Or using HTTP (not recommended)
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

**Note:** The `-k` flag tells curl to accept self-signed certificates. For production use, consider using a proper CA-signed certificate or implement certificate pinning in your client (see example_client.py).

## Configuration

### Server Configuration (Safe for Git Pull)

Create a `.env` file in the project root (this file is git-ignored and won't be overwritten):

```bash
cp .env.example .env
```

Edit `.env` to configure your server:

```bash
# API authentication key
API_KEY=your-secret-key-here

# Database path
DB_PATH=data/events.db

# TLS certificate paths (for HTTPS)
CERT_PATH=certs/cert.pem
KEY_PATH=certs/key.pem
```

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

### GET /fingerprint

Retrieves the server's TLS certificate fingerprint for identity verification.

**Parameters:** None (no authentication required - fingerprint is public information)

**Response:**
```json
{
  "fingerprint": "a1b2c3d4e5f6789...",
  "algorithm": "sha256",
  "certificate_path": "certs/cert.pem"
}
```

**Use case:** Clients can verify they're communicating with the correct server by comparing this fingerprint with a previously saved value. See the Security section for details.

## Docker Details

### Volume Persistence

Two volumes are mounted for persistence:
- `./data/` - SQLite database storage
- `./certs/` - TLS certificates (persists fingerprint across container restarts)

### Environment Variables

- `API_KEY`: Authentication key (default: `my-secret-key`)
- `DB_PATH`: Database file path (default: `data/events.db`)
- `CERT_PATH`: TLS certificate path (default: `certs/cert.pem`)
- `KEY_PATH`: TLS private key path (default: `certs/key.pem`)

### Ports

- `8443`: HTTPS port (default, recommended)
- `8000`: HTTP port (optional, for backward compatibility)

### Stop Container

```bash
docker-compose down
```

## Notes

- The database is created automatically in the `data/` directory when starting the application
- With Docker, data persists in the mounted volume
- **TLS certificates are auto-generated** on first run if not present
- Certificates are stored in `./certs/` and persist across restarts
- Designed for low volume (~7-10 records/day)
- No complex dependencies, ideal for learning and iteration
- SQLite is sufficient for this data volume

## Security Best Practices

1. **Always use HTTPS** in production to encrypt data in transit
2. **Implement certificate pinning** in your clients to verify server identity
3. **Change the default API key** in your `.env` file
4. **Keep your API key secret** - never commit it to git
5. **Save the certificate fingerprint** when first setting up clients
6. **Monitor for fingerprint mismatches** - they indicate potential attacks

## Files

- `main.py` - FastAPI server with API endpoints
- `generate_cert.py` - Certificate generation utility
- `run_server.py` - Server startup script with HTTPS support
- `example_client.py` - Example client with certificate pinning
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Docker orchestration
- `.env.example` - Configuration template
- `certs/` - TLS certificates (auto-generated, git-ignored)
- `data/` - SQLite database (git-ignored)
