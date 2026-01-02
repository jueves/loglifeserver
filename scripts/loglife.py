#!/usr/bin/env python3
"""LogLife Client - Record data with flexible JSON structure."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv


class LogLifeClient:
    """Client for interacting with the LogLife API."""

    def __init__(self, server: str, api_key: str):
        """Initialize the LogLife client.

        Args:
            server: The LogLife server URL
            api_key: The API key for authentication
        """
        self.server = server.rstrip('/')
        self.api_key = api_key
        self.verify_ssl = not server.startswith('https://')

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the LogLife API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            json_data: Optional JSON data to send

        Returns:
            Response data as a dictionary

        Raises:
            SystemExit: If the request fails
        """
        url = f"{self.server}/{endpoint.lstrip('/')}"
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }

        try:
            response = httpx.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                verify=self.verify_ssl,
                timeout=30.0
            )
            return response.json()
        except httpx.HTTPError as e:
            print(f"✗ HTTP Error: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON response: {e}", file=sys.stderr)
            sys.exit(1)

    def log(self, key_values: Dict[str, Any], timestamp: Optional[str] = None) -> None:
        """Record data using key-value pairs.

        Args:
            key_values: Dictionary of data to record
            timestamp: Optional ISO 8601 timestamp
        """
        request_body = {'data': key_values}
        if timestamp:
            request_body['timestamp'] = timestamp

        response = self._make_request('POST', '/record', request_body)

        if response.get('ok'):
            record_id = response.get('id')
            print(f"✓ Recorded (ID: {record_id})")
        else:
            print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
            sys.exit(1)

    def record(self, json_data: Dict[str, Any], timestamp: Optional[str] = None) -> None:
        """Record data using raw JSON.

        Args:
            json_data: JSON data to record
            timestamp: Optional ISO 8601 timestamp
        """
        self.log(json_data, timestamp)

    def delete(self, record_id: int) -> None:
        """Delete a record by ID.

        Args:
            record_id: The record ID to delete
        """
        response = self._make_request('DELETE', f'/record/{record_id}')

        if response.get('ok'):
            print(f"✓ Deleted record {record_id}")
        else:
            print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
            sys.exit(1)

    def query(self, limit: int = 100) -> None:
        """Query recent records.

        Args:
            limit: Maximum number of records to return
        """
        response = self._make_request('GET', f'/records?limit={limit}')

        if 'data' in response:
            for record in response['data']:
                record_id = record.get('id')
                timestamp = record.get('timestamp')
                data = json.dumps(record.get('data', {}))
                print(f"{record_id}\t{timestamp}\t{data}")
        else:
            print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
            sys.exit(1)

    def export(self, output_file: str = 'loglife_export.json') -> None:
        """Export all records to a JSON file.

        Args:
            output_file: Path to the output file
        """
        response = self._make_request('GET', '/export')

        if 'records' in response:
            output_path = Path(output_file)
            output_path.write_text(json.dumps(response, indent=2))
            record_count = response.get('count', 0)
            print(f"✓ Exported {record_count} records to {output_file}")
        else:
            print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
            sys.exit(1)


def parse_key_value_pairs(args: list[str]) -> Dict[str, Any]:
    """Parse command-line arguments into key-value pairs.

    Args:
        args: List of key:value strings

    Returns:
        Dictionary of parsed key-value pairs

    Raises:
        ValueError: If a key:value pair is invalid
    """
    result = {}

    for arg in args:
        if ':' not in arg:
            raise ValueError(f"Invalid format '{arg}'. Expected key:value")

        # Split on first colon only
        key, _, value = arg.partition(':')

        # Try to detect numbers
        try:
            # Try integer first
            if '.' not in value:
                result[key] = int(value)
            else:
                result[key] = float(value)
        except ValueError:
            # It's a string
            result[key] = value

    return result


def load_config() -> tuple[str, str]:
    """Load configuration from environment variables and .env file.

    Returns:
        Tuple of (server_url, api_key)
    """
    # Find .env file in repo root
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent if script_dir.name == 'scripts' else script_dir
    env_file = repo_root / '.env'

    if env_file.exists():
        load_dotenv(env_file)

    server = os.getenv('LOGLIFE_SERVER', 'http://localhost:3001')
    api_key = os.getenv('LOGLIFE_API_KEY', 'change-me-in-production')

    return server, api_key


def main() -> None:
    """Main entry point for the LogLife CLI."""
    parser = argparse.ArgumentParser(
        description='LogLife Client - Record data with flexible JSON structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Log data (easy format)
  %(prog)s log temperature:25.5 humidity:60
  %(prog)s log workout:running duration:30 distance:"5 km"
  %(prog)s log --timestamp '2025-12-20T14:30:00' mood:happy notes:"Had a great day!"

  # Record data (JSON format)
  %(prog)s record '{"temperature":25.5,"humidity":60}'
  %(prog)s record --timestamp '2025-12-20T14:30:00' '{"workout":"running","duration":30}'

  # Delete a record
  %(prog)s delete 123

  # Query recent records
  %(prog)s query
  %(prog)s query --limit 50

  # Export all data
  %(prog)s export
  %(prog)s export my_data.json

Configure via .env file:
  LOGLIFE_SERVER=http://localhost:3001
  LOGLIFE_API_KEY=your-api-key
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Log command
    log_parser = subparsers.add_parser(
        'log',
        help='Record data using key:value pairs'
    )
    log_parser.add_argument(
        '--timestamp',
        type=str,
        help='ISO 8601 timestamp (e.g., 2025-12-20T14:30:00)'
    )
    log_parser.add_argument(
        'pairs',
        nargs='+',
        metavar='key:value',
        help='Key-value pairs to record'
    )

    # Record command
    record_parser = subparsers.add_parser(
        'record',
        help='Record data using raw JSON'
    )
    record_parser.add_argument(
        '--timestamp',
        type=str,
        help='ISO 8601 timestamp (e.g., 2025-12-20T14:30:00)'
    )
    record_parser.add_argument(
        'json_data',
        type=str,
        help='JSON data to record'
    )

    # Delete command
    delete_parser = subparsers.add_parser(
        'delete',
        help='Delete a record by ID'
    )
    delete_parser.add_argument(
        'record_id',
        type=int,
        help='Record ID to delete'
    )

    # Query command
    query_parser = subparsers.add_parser(
        'query',
        help='Query recent records'
    )
    query_parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum number of records to return (default: 100)'
    )

    # Export command
    export_parser = subparsers.add_parser(
        'export',
        help='Export all records to a JSON file'
    )
    export_parser.add_argument(
        'output_file',
        nargs='?',
        default='loglife_export.json',
        help='Output file path (default: loglife_export.json)'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load configuration
    server, api_key = load_config()
    client = LogLifeClient(server, api_key)

    # Execute command
    try:
        if args.command == 'log':
            key_values = parse_key_value_pairs(args.pairs)
            client.log(key_values, args.timestamp)

        elif args.command == 'record':
            json_data = json.loads(args.json_data)
            client.record(json_data, args.timestamp)

        elif args.command == 'delete':
            client.delete(args.record_id)

        elif args.command == 'query':
            client.query(args.limit)

        elif args.command == 'export':
            client.export(args.output_file)

    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✗ Interrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
