#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta session information via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session  # noqa: E402


def cmd_get(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/sessions/{args.id}')
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description='Read Okta session information')
    sub = parser.add_subparsers(dest='command', required=True)

    p_get = sub.add_parser('get', help='Get session information by session ID')
    p_get.add_argument('id', help='Session ID')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'get':
            result = cmd_get(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
