#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta devices via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.search:
        params['search'] = args.search
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/devices', params, limit=args.limit)


def cmd_get(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/devices/{args.id}')
    resp.raise_for_status()
    return resp.json()


def cmd_get_users(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/devices/{args.id}/users')


def cmd_get_os_accounts(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/devices/{args.id}/os-accounts', params)


def cmd_get_os_account(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    resp = session.get(
        f'{base_url}/api/v1/devices/{args.id}/os-accounts/{args.os_account_id}', params=params
    )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description='Read Okta devices')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List devices')
    p_list.add_argument('--search', help='SCIM search expression (e.g. status eq "ACTIVE")')
    p_list.add_argument('--expand', choices=['user', 'userSummary'], help='Embed associated-user detail')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get a device by ID')
    p_get.add_argument('id', help='Device ID')

    p_users = sub.add_parser('get-users', help='List users associated with a device')
    p_users.add_argument('id', help='Device ID')

    p_os_accounts = sub.add_parser(
        'get-os-accounts', help='List all OS accounts for a device (EA)'
    )
    p_os_accounts.add_argument('id', help='Device ID')
    p_os_accounts.add_argument(
        '--expand', help='Comma-separated related resources to embed: users, account_linked_enrollments'
    )

    p_os_account = sub.add_parser(
        'get-os-account', help='Get a specific OS account for a device (EA)'
    )
    p_os_account.add_argument('id', help='Device ID')
    p_os_account.add_argument('os_account_id', help='OS account ID')
    p_os_account.add_argument(
        '--expand', help='Comma-separated related resources to embed: users, account_linked_enrollments'
    )

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'list':
            result = cmd_list(session, base_url, args)
        elif args.command == 'get':
            result = cmd_get(session, base_url, args)
        elif args.command == 'get-users':
            result = cmd_get_users(session, base_url, args)
        elif args.command == 'get-os-accounts':
            result = cmd_get_os_accounts(session, base_url, args)
        elif args.command == 'get-os-account':
            result = cmd_get_os_account(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
