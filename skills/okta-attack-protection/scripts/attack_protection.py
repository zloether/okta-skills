#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta Attack Protection settings via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session, get_resource  # noqa: E402


def cmd_get_authenticator_settings(session, base_url, args):
    return get_resource(session, f'{base_url}/attack-protection/api/v1/authenticator-settings')


def cmd_get_user_lockout_settings(session, base_url, args):
    return get_resource(session, f'{base_url}/attack-protection/api/v1/user-lockout-settings')


def main():
    parser = argparse.ArgumentParser(description='Read Okta Attack Protection settings')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('get-authenticator-settings', help="Get the org's authenticator lockout/enforcement settings")
    sub.add_parser('get-user-lockout-settings', help="Get the org's user lockout policy settings")

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'get-authenticator-settings':
            result = cmd_get_authenticator_settings(session, base_url, args)
        elif args.command == 'get-user-lockout-settings':
            result = cmd_get_user_lockout_settings(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
