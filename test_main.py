import pytest
import os
import sqlite3
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def temp_db():
    """Create a temporary database file"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db_path = temp_db.name
    temp_db.close()

    # Initialize database
    os.makedirs(os.path.dirname(temp_db_path), exist_ok=True)
    conn = sqlite3.connect(temp_db_path)
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

    yield temp_db_path

    # Cleanup
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.fixture
def client(temp_db):
    """Create a test client with a temporary database"""
    # Patch DB_PATH in the main module to use temp database
    with patch('main.DB_PATH', temp_db):
        # Import app after patching
        from main import app
        client = TestClient(app)
        yield client


@pytest.fixture
def api_key():
    """Return the API key for testing"""
    return os.getenv("LOGLIFE_API_KEY", "my-secret-key")


class TestAuthentication:
    """Test authentication functionality"""

    def test_log_with_valid_key(self, client, api_key):
        """Test logging with valid API key"""
        response = client.get(
            "/log",
            params={"event_key": "test_event", "value": "test_value", "key": api_key}
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_log_with_invalid_key(self, client):
        """Test logging with invalid API key"""
        response = client.get(
            "/log",
            params={"event_key": "test_event", "value": "test_value", "key": "wrong-key"}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    def test_logs_with_valid_key(self, client, api_key):
        """Test getting logs with valid API key"""
        response = client.get("/logs", params={"key": api_key})
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_logs_with_invalid_key(self, client):
        """Test getting logs with invalid API key"""
        response = client.get("/logs", params={"key": "wrong-key"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}


class TestLogEndpoint:
    """Test /log endpoint functionality"""

    def test_log_single_event(self, client, api_key):
        """Test logging a single event"""
        response = client.get(
            "/log",
            params={"event_key": "temperature", "value": "25.5", "key": api_key}
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_log_multiple_events(self, client, api_key):
        """Test logging multiple events"""
        events = [
            {"event_key": "temperature", "value": "25.5"},
            {"event_key": "humidity", "value": "60"},
            {"event_key": "pressure", "value": "1013"},
        ]

        for event in events:
            response = client.get(
                "/log",
                params={**event, "key": api_key}
            )
            assert response.status_code == 200
            assert response.json() == {"ok": True}

    def test_log_with_special_characters(self, client, api_key):
        """Test logging with special characters in values"""
        response = client.get(
            "/log",
            params={
                "event_key": "message",
                "value": "Test with spaces & special chars!",
                "key": api_key
            }
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_log_empty_values(self, client, api_key):
        """Test logging with empty event_key or value"""
        response = client.get(
            "/log",
            params={"event_key": "", "value": "", "key": api_key}
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class TestLogsEndpoint:
    """Test /logs endpoint functionality"""

    def test_get_empty_logs(self, client, api_key):
        """Test getting logs when database is empty"""
        response = client.get("/logs", params={"key": api_key})
        assert response.status_code == 200
        assert response.json() == []

    def test_get_logs_after_logging(self, client, api_key):
        """Test getting logs after logging some events"""
        # Log some events
        events = [
            {"event_key": "event1", "value": "value1"},
            {"event_key": "event2", "value": "value2"},
            {"event_key": "event3", "value": "value3"},
        ]

        for event in events:
            client.get("/log", params={**event, "key": api_key})

        # Get logs
        response = client.get("/logs", params={"key": api_key})
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) == 3

        # Verify logs are in descending order (most recent first)
        assert logs[0]["event_key"] == "event3"
        assert logs[1]["event_key"] == "event2"
        assert logs[2]["event_key"] == "event1"

    def test_logs_structure(self, client, api_key):
        """Test that logs have the correct structure"""
        # Log an event
        client.get(
            "/log",
            params={"event_key": "test", "value": "test_value", "key": api_key}
        )

        # Get logs
        response = client.get("/logs", params={"key": api_key})
        logs = response.json()

        assert len(logs) == 1
        log = logs[0]

        # Check structure
        assert "id" in log
        assert "event_key" in log
        assert "value" in log
        assert "timestamp" in log

        # Check values
        assert log["event_key"] == "test"
        assert log["value"] == "test_value"
        assert isinstance(log["id"], int)
        assert isinstance(log["timestamp"], str)


class TestDatabaseIntegration:
    """Test database persistence and integration"""

    def test_event_persisted_in_database(self, client, api_key, temp_db):
        """Test that logged events are actually persisted in the database"""
        # Log an event
        client.get(
            "/log",
            params={"event_key": "persist_test", "value": "persist_value", "key": api_key}
        )

        # Query database directly using temp_db fixture
        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT event_key, value FROM events WHERE event_key = ?",
            ("persist_test",)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "persist_test"
        assert row[1] == "persist_value"

    def test_timestamp_format(self, client, api_key):
        """Test that timestamps are stored in ISO format"""
        # Log an event
        client.get(
            "/log",
            params={"event_key": "timestamp_test", "value": "test", "key": api_key}
        )

        # Get the log
        response = client.get("/logs", params={"key": api_key})
        logs = response.json()

        assert len(logs) > 0
        timestamp = logs[0]["timestamp"]

        # Check it's a valid ISO format string (should contain T and possibly microseconds)
        assert "T" in timestamp
        assert len(timestamp) > 10  # More than just a date
