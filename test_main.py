import pytest
import os
import sqlite3
import json
import tempfile
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def temp_db():
    """Create a temporary database file"""
    temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db_path = temp_db_file.name
    temp_db_file.close()

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
        from main import app, init_db
        # Re-initialize the database with the temp path
        init_db()
        client = TestClient(app)
        yield client


@pytest.fixture
def api_key():
    """Return the API key for testing"""
    return os.getenv("LOGLIFE_API_KEY", "my-secret-key")


class TestAuthentication:
    """Test authentication functionality"""

    def test_record_with_valid_key(self, client, api_key):
        """Test creating record with valid API key"""
        response = client.post(
            "/record",
            json={"data": {"temperature": 25.5}},
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        assert "id" in response.json()

    def test_record_with_invalid_key(self, client):
        """Test creating record with invalid API key"""
        response = client.post(
            "/record",
            json={"data": {"temperature": 25.5}},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    def test_record_without_key(self, client):
        """Test creating record without API key"""
        response = client.post(
            "/record",
            json={"data": {"temperature": 25.5}}
        )
        assert response.status_code == 401

    def test_records_with_valid_key(self, client, api_key):
        """Test getting records with valid API key"""
        response = client.get(
            "/records",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        assert "data" in response.json()
        assert isinstance(response.json()["data"], list)

    def test_records_with_invalid_key(self, client):
        """Test getting records with invalid API key"""
        response = client.get(
            "/records",
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401

    def test_delete_with_valid_key(self, client, api_key):
        """Test deleting record with valid API key"""
        # First create a record
        create_response = client.post(
            "/record",
            json={"data": {"test": "value"}},
            headers={"X-API-Key": api_key}
        )
        record_id = create_response.json()["id"]

        # Then delete it
        response = client.delete(
            f"/record/{record_id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_delete_with_invalid_key(self, client, api_key):
        """Test deleting record with invalid API key"""
        # First create a record
        create_response = client.post(
            "/record",
            json={"data": {"test": "value"}},
            headers={"X-API-Key": api_key}
        )
        record_id = create_response.json()["id"]

        # Try to delete with wrong key
        response = client.delete(
            f"/record/{record_id}",
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401


class TestRecordEndpoint:
    """Test POST /record endpoint functionality"""

    def test_create_simple_record(self, client, api_key):
        """Test creating a simple record with current timestamp"""
        response = client.post(
            "/record",
            json={"data": {"temperature": 25.5, "humidity": 60}},
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        assert isinstance(response.json()["id"], int)

    def test_create_record_with_custom_timestamp(self, client, api_key):
        """Test creating a record with a custom timestamp"""
        custom_timestamp = "2025-12-20T14:30:00"
        response = client.post(
            "/record",
            json={
                "timestamp": custom_timestamp,
                "data": {"workout": "running", "duration": 30}
            },
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_create_record_with_invalid_timestamp(self, client, api_key):
        """Test creating a record with an invalid timestamp format"""
        response = client.post(
            "/record",
            json={
                "timestamp": "not-a-valid-timestamp",
                "data": {"test": "value"}
            },
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 400
        assert "Invalid timestamp format" in response.json()["detail"]

    def test_create_record_with_complex_data(self, client, api_key):
        """Test creating a record with nested JSON data"""
        complex_data = {
            "workout": "running",
            "duration": 30,
            "distance": 5.2,
            "splits": [6.0, 5.8, 5.7],
            "location": {
                "city": "SF",
                "park": "Golden Gate"
            }
        }
        response = client.post(
            "/record",
            json={"data": complex_data},
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_create_record_without_data(self, client, api_key):
        """Test that creating a record requires data field"""
        response = client.post(
            "/record",
            json={},
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 422  # Validation error


class TestDeleteEndpoint:
    """Test DELETE /record/{id} endpoint functionality"""

    def test_delete_existing_record(self, client, api_key):
        """Test deleting an existing record"""
        # Create a record
        create_response = client.post(
            "/record",
            json={"data": {"test": "value"}},
            headers={"X-API-Key": api_key}
        )
        record_id = create_response.json()["id"]

        # Delete it
        delete_response = client.delete(
            f"/record/{record_id}",
            headers={"X-API-Key": api_key}
        )
        assert delete_response.status_code == 200
        assert delete_response.json() == {"ok": True}

        # Verify it's deleted
        records_response = client.get(
            "/records",
            headers={"X-API-Key": api_key}
        )
        records = records_response.json()["data"]
        assert not any(r["id"] == record_id for r in records)

    def test_delete_nonexistent_record(self, client, api_key):
        """Test deleting a record that doesn't exist"""
        response = client.delete(
            "/record/99999",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Record not found"}


class TestRecordsEndpoint:
    """Test GET /records endpoint functionality"""

    def test_get_empty_records(self, client, api_key):
        """Test getting records when database is empty"""
        response = client.get(
            "/records",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        assert response.json() == {"data": []}

    def test_get_records_after_creating(self, client, api_key):
        """Test getting records after creating some"""
        # Create multiple records
        records_data = [
            {"temperature": 25.5},
            {"humidity": 60},
            {"pressure": 1013}
        ]

        for data in records_data:
            client.post(
                "/record",
                json={"data": data},
                headers={"X-API-Key": api_key}
            )

        # Get records
        response = client.get(
            "/records",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        records = response.json()["data"]
        assert len(records) == 3

    def test_records_ordered_by_timestamp_desc(self, client, api_key):
        """Test that records are ordered by timestamp descending"""
        # Create records with different timestamps
        timestamps = [
            "2025-12-20T10:00:00",
            "2025-12-20T12:00:00",
            "2025-12-20T11:00:00"
        ]

        for ts in timestamps:
            client.post(
                "/record",
                json={"timestamp": ts, "data": {"time": ts}},
                headers={"X-API-Key": api_key}
            )

        # Get records
        response = client.get(
            "/records",
            headers={"X-API-Key": api_key}
        )
        records = response.json()["data"]

        # Should be in descending order
        assert records[0]["timestamp"] == "2025-12-20T12:00:00"
        assert records[1]["timestamp"] == "2025-12-20T11:00:00"
        assert records[2]["timestamp"] == "2025-12-20T10:00:00"

    def test_records_structure(self, client, api_key):
        """Test that records have the correct structure"""
        # Create a record
        client.post(
            "/record",
            json={"data": {"test": "value"}},
            headers={"X-API-Key": api_key}
        )

        # Get records
        response = client.get(
            "/records",
            headers={"X-API-Key": api_key}
        )
        records = response.json()["data"]

        assert len(records) == 1
        record = records[0]

        # Check structure
        assert "id" in record
        assert "timestamp" in record
        assert "data" in record
        assert "created_at" in record

        # Check types
        assert isinstance(record["id"], int)
        assert isinstance(record["timestamp"], str)
        assert isinstance(record["data"], dict)
        assert isinstance(record["created_at"], str)

    def test_filter_by_limit(self, client, api_key):
        """Test filtering records by limit"""
        # Create 5 records
        for i in range(5):
            client.post(
                "/record",
                json={"data": {"index": i}},
                headers={"X-API-Key": api_key}
            )

        # Get with limit=2
        response = client.get(
            "/records?limit=2",
            headers={"X-API-Key": api_key}
        )
        records = response.json()["data"]
        assert len(records) == 2


class TestExportEndpoint:
    """Test GET /export endpoint functionality"""

    def test_export_empty_database(self, client, api_key):
        """Test exporting when database is empty"""
        response = client.get(
            "/export",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "count" in data
        assert data["count"] == 0
        assert data["records"] == []

    def test_export_with_records(self, client, api_key):
        """Test exporting records"""
        # Create some records
        records_data = [
            {"temperature": 25.5},
            {"humidity": 60},
            {"pressure": 1013}
        ]

        for data in records_data:
            client.post(
                "/record",
                json={"data": data},
                headers={"X-API-Key": api_key}
            )

        # Export
        response = client.get(
            "/export",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        export_data = response.json()

        assert export_data["count"] == 3
        assert len(export_data["records"]) == 3

        # Verify all records are present
        exported_records = export_data["records"]
        assert any(r["data"].get("temperature") == 25.5 for r in exported_records)
        assert any(r["data"].get("humidity") == 60 for r in exported_records)
        assert any(r["data"].get("pressure") == 1013 for r in exported_records)

    def test_export_ordered_by_timestamp_asc(self, client, api_key):
        """Test that exported records are ordered by timestamp ascending"""
        # Create records with different timestamps
        timestamps = [
            "2025-12-20T12:00:00",
            "2025-12-20T10:00:00",
            "2025-12-20T11:00:00"
        ]

        for ts in timestamps:
            client.post(
                "/record",
                json={"timestamp": ts, "data": {"time": ts}},
                headers={"X-API-Key": api_key}
            )

        # Export
        response = client.get(
            "/export",
            headers={"X-API-Key": api_key}
        )
        records = response.json()["records"]

        # Should be in ascending order
        assert records[0]["timestamp"] == "2025-12-20T10:00:00"
        assert records[1]["timestamp"] == "2025-12-20T11:00:00"
        assert records[2]["timestamp"] == "2025-12-20T12:00:00"

    def test_export_structure(self, client, api_key):
        """Test that exported records have the correct structure"""
        # Create a record
        client.post(
            "/record",
            json={"data": {"test": "value"}},
            headers={"X-API-Key": api_key}
        )

        # Export
        response = client.get(
            "/export",
            headers={"X-API-Key": api_key}
        )
        export_data = response.json()

        assert "records" in export_data
        assert "count" in export_data
        assert isinstance(export_data["records"], list)
        assert isinstance(export_data["count"], int)

        record = export_data["records"][0]
        assert "id" in record
        assert "timestamp" in record
        assert "data" in record
        assert "created_at" in record

    def test_export_requires_authentication(self, client):
        """Test that export requires valid API key"""
        response = client.get(
            "/export",
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401


class TestDatabaseIntegration:
    """Test database persistence and migration"""

    def test_record_persisted_in_database(self, client, api_key, temp_db):
        """Test that records are actually persisted in the database"""
        # Create a record
        response = client.post(
            "/record",
            json={"data": {"persist_test": "persist_value"}},
            headers={"X-API-Key": api_key}
        )
        record_id = response.json()["id"]

        # Query database directly
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT id, data FROM records WHERE id = ?",
                (record_id,)
            )
            row = cursor.fetchone()

        assert row is not None
        assert row[0] == record_id
        data = json.loads(row[1])
        assert data["persist_test"] == "persist_value"

    def test_migration_from_old_events_table(self, temp_db):
        """Test that old events table is migrated to new records table"""
        # Create old events table with some data
        with sqlite3.connect(temp_db) as conn:
            conn.execute("""
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_key TEXT,
                    value TEXT,
                    timestamp DATETIME
                )
            """)
            conn.execute(
                "INSERT INTO events (event_key, value, timestamp) VALUES (?, ?, ?)",
                ("temperature", "25.5", "2025-12-20T10:00:00")
            )
            conn.execute(
                "INSERT INTO events (event_key, value, timestamp) VALUES (?, ?, ?)",
                ("humidity", "60", "2025-12-20T10:05:00")
            )
            conn.commit()

        # Now initialize the app (which should trigger migration)
        with patch('main.DB_PATH', temp_db):
            from main import init_db
            init_db()

        # Verify migration
        with sqlite3.connect(temp_db) as conn:
            # Check old table is gone
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
            )
            assert cursor.fetchone() is None

            # Check records table exists and has migrated data
            cursor = conn.execute("SELECT COUNT(*) FROM records")
            assert cursor.fetchone()[0] == 2

            # Check data format
            cursor = conn.execute("SELECT data FROM records ORDER BY timestamp")
            rows = cursor.fetchall()

            data1 = json.loads(rows[0][0])
            assert data1 == {"temperature": "25.5"}

            data2 = json.loads(rows[1][0])
            assert data2 == {"humidity": "60"}

    def test_timestamp_format(self, client, api_key):
        """Test that timestamps are stored in ISO format"""
        # Create a record
        client.post(
            "/record",
            json={"data": {"timestamp_test": "test"}},
            headers={"X-API-Key": api_key}
        )

        # Get the record
        response = client.get(
            "/records",
            headers={"X-API-Key": api_key}
        )
        records = response.json()["data"]

        assert len(records) > 0
        timestamp = records[0]["timestamp"]
        created_at = records[0]["created_at"]

        # Check they're valid ISO format strings
        assert "T" in timestamp
        assert "T" in created_at
