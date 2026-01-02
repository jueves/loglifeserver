#!/usr/bin/env python3
"""LogLife Client - Simple CLI for recording life data."""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


def load_config():
    """Load server URL and API key from environment."""
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent if script_dir.name == 'scripts' else script_dir
    env_file = repo_root / '.env'

    if env_file.exists():
        load_dotenv(env_file)

    return (
        os.getenv('LOGLIFE_SERVER', 'http://localhost:3001'),
        os.getenv('LOGLIFE_API_KEY', 'change-me-in-production')
    )


def api_request(server, api_key, method, endpoint, json_data=None):
    """Make API request and return JSON response."""
    url = f"{server.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
    verify = not server.startswith('https://')

    try:
        response = httpx.request(method, url, headers=headers, json=json_data,
                                verify=verify, timeout=30.0)
        return response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def parse_key_values(args):
    """Convert key:value args to dict with type detection."""
    result = {}
    for arg in args:
        if ':' not in arg:
            raise ValueError(f"Invalid format '{arg}'. Expected key:value")

        key, _, value = arg.partition(':')

        # Try to convert to number
        try:
            result[key] = int(value) if '.' not in value else float(value)
        except ValueError:
            result[key] = value

    return result


def cmd_log(args, server, api_key):
    """Log data using key:value pairs."""
    data = parse_key_values(args.pairs)
    body = {'data': data}
    if args.timestamp:
        body['timestamp'] = args.timestamp

    response = api_request(server, api_key, 'POST', '/record', body)
    if response.get('ok'):
        print(f"✓ Recorded (ID: {response.get('id')})")
    else:
        print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
        sys.exit(1)


def cmd_record(args, server, api_key):
    """Record data using raw JSON."""
    try:
        data = json.loads(args.json_data)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    body = {'data': data}
    if args.timestamp:
        body['timestamp'] = args.timestamp

    response = api_request(server, api_key, 'POST', '/record', body)
    if response.get('ok'):
        print(f"✓ Recorded (ID: {response.get('id')})")
    else:
        print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args, server, api_key):
    """Delete a record by ID."""
    response = api_request(server, api_key, 'DELETE', f'/record/{args.record_id}')
    if response.get('ok'):
        print(f"✓ Deleted record {args.record_id}")
    else:
        print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
        sys.exit(1)


def cmd_query(args, server, api_key):
    """Query recent records."""
    response = api_request(server, api_key, 'GET', f'/records?limit={args.limit}')
    if 'data' in response:
        for record in response['data']:
            print(f"{record['id']}\t{record['timestamp']}\t{json.dumps(record['data'])}")
    else:
        print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
        sys.exit(1)


def cmd_export(args, server, api_key):
    """Export all records to JSON file."""
    response = api_request(server, api_key, 'GET', '/export')
    if 'records' in response:
        Path(args.output_file).write_text(json.dumps(response, indent=2))
        print(f"✓ Exported {response.get('count', 0)} records to {args.output_file}")
    else:
        print(f"✗ Failed: {json.dumps(response)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='LogLife Client')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Log command
    log_parser = subparsers.add_parser('log', help='Record data using key:value pairs')
    log_parser.add_argument('--timestamp', help='ISO 8601 timestamp')
    log_parser.add_argument('pairs', nargs='+', metavar='key:value')

    # Record command
    record_parser = subparsers.add_parser('record', help='Record data using raw JSON')
    record_parser.add_argument('--timestamp', help='ISO 8601 timestamp')
    record_parser.add_argument('json_data')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a record by ID')
    delete_parser.add_argument('record_id', type=int)

    # Query command
    query_parser = subparsers.add_parser('query', help='Query recent records')
    query_parser.add_argument('--limit', type=int, default=100)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export all records')
    export_parser.add_argument('output_file', nargs='?', default='loglife_export.json')

    args = parser.parse_args()
    server, api_key = load_config()

    # Dispatch to command handler
    commands = {
        'log': cmd_log,
        'record': cmd_record,
        'delete': cmd_delete,
        'query': cmd_query,
        'export': cmd_export
    }

    try:
        commands[args.command](args, server, api_key)
    except (ValueError, KeyboardInterrupt) as e:
        if isinstance(e, ValueError):
            print(f"✗ Error: {e}", file=sys.stderr)
        else:
            print("\n✗ Interrupted", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
