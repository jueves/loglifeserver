#!/usr/bin/env python3
"""
Example client demonstrating server identity verification via certificate pinning.

This client verifies the server's TLS certificate fingerprint before sending data,
protecting against man-in-the-middle attacks if your VPN disconnects.

Usage:
    # First time - retrieve and save fingerprint
    python example_client.py --server https://your-server:8443 --save-fingerprint

    # Regular use - verify fingerprint before every request
    python example_client.py --server https://your-server:8443 --api-key YOUR_KEY

    # Log an event
    python example_client.py --server https://your-server:8443 --api-key YOUR_KEY \\
        --log --event temperature --value 25.5

    # Retrieve logs
    python example_client.py --server https://your-server:8443 --api-key YOUR_KEY --get-logs
"""

import sys
import ssl
import hashlib
import argparse
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
import json
from pathlib import Path


class SecureLogClient:
    """Client that verifies server identity via certificate pinning."""

    def __init__(self, server_url, api_key=None, fingerprint=None, verify=True):
        """
        Initialize secure client.

        Args:
            server_url: Server URL (e.g., https://localhost:8443)
            api_key: API key for authentication
            fingerprint: Expected SHA-256 certificate fingerprint (hex string)
            verify: Whether to verify certificate fingerprint (default: True)
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.expected_fingerprint = fingerprint
        self.verify = verify

    def get_server_fingerprint(self):
        """
        Retrieve the actual certificate fingerprint from the server.
        This connects to the server and calculates the certificate fingerprint.

        Returns:
            str: SHA-256 fingerprint as hex string
        """
        # Create SSL context that doesn't verify (we'll verify manually)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Extract hostname and port from URL
        from urllib.parse import urlparse
        parsed = urlparse(self.server_url)
        hostname = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)

        # Connect and get certificate
        with ssl.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_der = ssock.getpeercert(binary_form=True)
                fingerprint = hashlib.sha256(cert_der).hexdigest()
                return fingerprint

    def verify_server_identity(self):
        """
        Verify the server's certificate fingerprint matches expected value.

        Returns:
            bool: True if fingerprint matches, False otherwise

        Raises:
            SecurityError: If fingerprint doesn't match (when verify=True)
        """
        if not self.verify:
            return True

        if not self.expected_fingerprint:
            raise ValueError("No expected fingerprint provided. Use --save-fingerprint first.")

        actual_fingerprint = self.get_server_fingerprint()

        if actual_fingerprint != self.expected_fingerprint:
            raise SecurityError(
                f"Server identity verification FAILED!\n"
                f"Expected: {self.expected_fingerprint}\n"
                f"Actual:   {actual_fingerprint}\n"
                f"⚠️  DO NOT SEND DATA - You may be connected to the wrong server!"
            )

        return True

    def make_request(self, endpoint, params=None):
        """
        Make a verified request to the server.

        Args:
            endpoint: API endpoint (e.g., '/log', '/logs')
            params: Query parameters as dict

        Returns:
            Response data as dict
        """
        # Verify server identity before making request
        if self.verify:
            self.verify_server_identity()
            print("✓ Server identity verified")

        # Build URL with parameters
        url = f"{self.server_url}{endpoint}"
        if params:
            url += f"?{urlencode(params)}"

        # Create SSL context (can accept self-signed certs since we verified fingerprint)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Make request
        try:
            with urlopen(url, context=context) as response:
                data = response.read()
                return json.loads(data.decode('utf-8'))
        except HTTPError as e:
            print(f"HTTP Error {e.code}: {e.reason}")
            sys.exit(1)
        except URLError as e:
            print(f"Connection Error: {e.reason}")
            sys.exit(1)

    def log_event(self, event_key, value):
        """Log an event to the server."""
        params = {
            'event_key': event_key,
            'value': value,
            'key': self.api_key
        }
        result = self.make_request('/log', params)
        print(f"✓ Event logged: {event_key}={value}")
        return result

    def get_logs(self):
        """Retrieve recent logs from the server."""
        params = {'key': self.api_key}
        logs = self.make_request('/logs', params)
        print(f"✓ Retrieved {len(logs)} log entries")
        return logs

    def get_fingerprint_from_api(self):
        """Get fingerprint from the /fingerprint endpoint (no verification)."""
        # Don't verify for this request (chicken-and-egg problem)
        old_verify = self.verify
        self.verify = False
        try:
            result = self.make_request('/fingerprint')
            return result['fingerprint']
        finally:
            self.verify = old_verify


class SecurityError(Exception):
    """Raised when server identity verification fails."""
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Secure LogLife client with certificate pinning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--server', required=True, help='Server URL (e.g., https://localhost:8443)')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--fingerprint', help='Expected certificate fingerprint (SHA-256 hex)')
    parser.add_argument('--fingerprint-file', default='.server_fingerprint',
                        help='File to store/load fingerprint (default: .server_fingerprint)')
    parser.add_argument('--no-verify', action='store_true', help='Skip fingerprint verification (insecure)')

    # Actions
    parser.add_argument('--save-fingerprint', action='store_true',
                        help='Save server fingerprint to file for future use')
    parser.add_argument('--log', action='store_true', help='Log an event')
    parser.add_argument('--event', help='Event key (for --log)')
    parser.add_argument('--value', help='Event value (for --log)')
    parser.add_argument('--get-logs', action='store_true', help='Retrieve recent logs')

    args = parser.parse_args()

    # Load fingerprint from file if exists and not provided
    fingerprint_path = Path(args.fingerprint_file)
    if args.fingerprint:
        fingerprint = args.fingerprint
    elif fingerprint_path.exists() and not args.save_fingerprint:
        fingerprint = fingerprint_path.read_text().strip()
        print(f"Loaded fingerprint from {args.fingerprint_file}")
    else:
        fingerprint = None

    # Create client
    client = SecureLogClient(
        server_url=args.server,
        api_key=args.api_key,
        fingerprint=fingerprint,
        verify=not args.no_verify
    )

    # Handle save fingerprint action
    if args.save_fingerprint:
        print("Retrieving server certificate fingerprint...")
        try:
            # Try to get from API endpoint first
            fp = client.get_fingerprint_from_api()
            print(f"✓ Retrieved from /fingerprint endpoint")
        except:
            # Fall back to direct certificate inspection
            fp = client.get_server_fingerprint()
            print(f"✓ Retrieved from certificate")

        print(f"\nServer fingerprint (SHA-256):")
        print(f"{fp}")

        # Save to file
        fingerprint_path.write_text(fp)
        print(f"\n✓ Fingerprint saved to {args.fingerprint_file}")
        print(f"\nYou can now use this client with automatic verification:")
        print(f"  python example_client.py --server {args.server} --api-key YOUR_KEY --get-logs")
        return

    # Handle log action
    if args.log:
        if not args.event or not args.value:
            print("Error: --log requires --event and --value")
            sys.exit(1)
        if not args.api_key:
            print("Error: --api-key required")
            sys.exit(1)

        client.log_event(args.event, args.value)

    # Handle get-logs action
    elif args.get_logs:
        if not args.api_key:
            print("Error: --api-key required")
            sys.exit(1)

        logs = client.get_logs()
        print("\nRecent logs:")
        print(json.dumps(logs, indent=2))

    else:
        print("No action specified. Use --save-fingerprint, --log, or --get-logs")
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except SecurityError as e:
        print(f"\n🚨 SECURITY ERROR 🚨")
        print(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
