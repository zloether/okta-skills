#!/usr/bin/env python3
"""Read Okta groups via the Okta API."""
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
    return paginated_get(session, f'{base_url}/api/v1/groups', params, limit=args.limit)


def cmd_get(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/groups/{args.id}')
    resp.raise_for_status()
    return resp.json()


def cmd_get_members(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/groups/{args.id}/users')


def cmd_search(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/groups', {'q': args.query})


def main():
    parser = argparse.ArgumentParser(description='Read Okta groups')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List groups')
    p_list.add_argument('--filter', help='SCIM filter expression')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get a group by ID')
    p_get.add_argument('id', help='Group ID')

    p_members = sub.add_parser('get-members', help='List users in a group')
    p_members.add_argument('id', help='Group ID')

    p_search = sub.add_parser('search', help='Search groups by name')
    p_search.add_argument('query', help='Search query')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'list':
            result = cmd_list(session, base_url, args)
        elif args.command == 'get':
            result = cmd_get(session, base_url, args)
        elif args.command == 'get-members':
            result = cmd_get_members(session, base_url, args)
        elif args.command == 'search':
            result = cmd_search(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
