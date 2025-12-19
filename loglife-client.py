#!/usr/bin/env python3
"""
LogLife Client - Command-line client for LogLife logging server
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

# Default configuration
DEFAULT_CONFIG = {
    "server_url": "http://localhost:3001",
    "api_key": "change-me-in-production"
}

CONFIG_FILE = os.path.expanduser("~/.loglife-client.json")


def load_config():
    """Load configuration from file or create default"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}", file=sys.stderr)
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error: Could not save config file: {e}", file=sys.stderr)
        sys.exit(1)


def log_event(server_url, api_key, event_key, value):
    """Log an event to the server"""
    params = urlencode({
        'event_key': event_key,
        'value': value,
        'key': api_key
    })
    url = f"{server_url}/log?{params}"

    try:
        req = Request(url)
        with urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('ok'):
                print(f"✓ Logged: {event_key} = {value}")
                return True
            else:
                print(f"✗ Failed to log event", file=sys.stderr)
                return False
    except HTTPError as e:
        if e.code == 401:
            print("✗ Error: Unauthorized. Check your API key.", file=sys.stderr)
        else:
            print(f"✗ HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        return False
    except URLError as e:
        print(f"✗ Connection Error: {e.reason}", file=sys.stderr)
        print(f"  Make sure the server is running at {server_url}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return False


def get_logs(server_url, api_key, limit=None, event_filter=None):
    """Retrieve logs from the server"""
    params = urlencode({'key': api_key})
    url = f"{server_url}/logs?{params}"

    try:
        req = Request(url)
        with urlopen(req) as response:
            logs = json.loads(response.read().decode())

            # Filter by event_key if specified
            if event_filter:
                logs = [log for log in logs if log['event_key'] == event_filter]

            # Limit results if specified
            if limit:
                logs = logs[:limit]

            if not logs:
                print("No logs found.")
                return

            # Display logs in a nice format
            print(f"\n{'ID':<6} {'Timestamp':<20} {'Event Key':<20} {'Value':<30}")
            print("-" * 78)
            for log in logs:
                # Parse and format timestamp
                try:
                    ts = datetime.fromisoformat(log['timestamp'])
                    ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    ts_str = log['timestamp'][:19]

                print(f"{log['id']:<6} {ts_str:<20} {log['event_key']:<20} {log['value']:<30}")

            print(f"\nTotal: {len(logs)} log(s)")

    except HTTPError as e:
        if e.code == 401:
            print("✗ Error: Unauthorized. Check your API key.", file=sys.stderr)
        else:
            print(f"✗ HTTP Error {e.code}: {e.reason}", file=sys.stderr)
    except URLError as e:
        print(f"✗ Connection Error: {e.reason}", file=sys.stderr)
        print(f"  Make sure the server is running at {server_url}", file=sys.stderr)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='LogLife Client - Command-line client for logging events',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Log an event
  %(prog)s log temperature 25.5
  %(prog)s log "server status" "running"

  # Query logs
  %(prog)s query
  %(prog)s query --limit 10
  %(prog)s query --event temperature

  # Configuration
  %(prog)s config --server http://localhost:3001
  %(prog)s config --api-key your-secret-key
  %(prog)s config --show
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Log command
    log_parser = subparsers.add_parser('log', help='Log an event')
    log_parser.add_argument('event_key', help='Event key/name')
    log_parser.add_argument('value', help='Event value')
    log_parser.add_argument('--server', help='Server URL (overrides config)')
    log_parser.add_argument('--api-key', help='API key (overrides config)')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query logs')
    query_parser.add_argument('--limit', type=int, help='Limit number of results')
    query_parser.add_argument('--event', help='Filter by event key')
    query_parser.add_argument('--server', help='Server URL (overrides config)')
    query_parser.add_argument('--api-key', help='API key (overrides config)')

    # Config command
    config_parser = subparsers.add_parser('config', help='Configure client')
    config_parser.add_argument('--server', help='Set server URL')
    config_parser.add_argument('--api-key', help='Set API key')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load configuration
    config = load_config()

    # Handle config command
    if args.command == 'config':
        if args.show:
            print(f"Configuration file: {CONFIG_FILE}")
            print(f"Server URL: {config['server_url']}")
            print(f"API Key: {config['api_key'][:8]}..." if len(config['api_key']) > 8 else f"API Key: {config['api_key']}")
        else:
            if args.server:
                config['server_url'] = args.server
            if args.api_key:
                config['api_key'] = args.api_key
            save_config(config)
        return

    # Get server URL and API key (command line overrides config)
    server_url = args.server if hasattr(args, 'server') and args.server else config['server_url']
    api_key = args.api_key if hasattr(args, 'api_key') and args.api_key else config['api_key']

    # Handle log command
    if args.command == 'log':
        success = log_event(server_url, api_key, args.event_key, args.value)
        sys.exit(0 if success else 1)

    # Handle query command
    elif args.command == 'query':
        get_logs(server_url, api_key, limit=args.limit, event_filter=args.event)


if __name__ == '__main__':
    main()
