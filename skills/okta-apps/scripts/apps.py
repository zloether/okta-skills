#!/usr/bin/env python3
"""Read Okta applications via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / 'shared'))
from okta_client import get_session, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.filter:
        params['filter'] = args.filter
    return paginated_get(session, f'{base_url}/api/v1/apps', params, limit=args.limit)


def cmd_get(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/apps/{args.id}')
    resp.raise_for_status()
    return resp.json()


def cmd_get_users(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/users')


def cmd_get_groups(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/groups')


def main():
    parser = argparse.ArgumentParser(description='Read Okta applications')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List applications')
    p_list.add_argument('--filter', help='Filter expression (e.g. status eq "ACTIVE")')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get an application by ID')
    p_get.add_argument('id', help='Application ID')

    p_users = sub.add_parser('get-users', help='List users assigned to an application')
    p_users.add_argument('id', help='Application ID')

    p_groups = sub.add_parser('get-groups', help='List groups assigned to an application')
    p_groups.add_argument('id', help='Application ID')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'list':
            result = cmd_list(session, base_url, args)
        elif args.command == 'get':
            result = cmd_get(session, base_url, args)
        elif args.command == 'get-users':
            result = cmd_get_users(session, base_url, args)
        elif args.command == 'get-groups':
            result = cmd_get_groups(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
