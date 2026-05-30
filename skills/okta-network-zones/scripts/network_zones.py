#!/usr/bin/env python3
"""Read Okta network zones via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / 'shared'))
from okta_client import get_session, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.type:
        params['filter'] = f'type eq "{args.type}"'
    return paginated_get(session, f'{base_url}/api/v1/zones', params)


def cmd_get(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/zones/{args.id}')
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description='Read Okta network zones')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List network zones')
    p_list.add_argument('--type', help='Zone type (IP, DYNAMIC, DYNAMIC_V2)')

    p_get = sub.add_parser('get', help='Get a network zone by ID')
    p_get.add_argument('id', help='Zone ID')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'list':
            result = cmd_list(session, base_url, args)
        elif args.command == 'get':
            result = cmd_get(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
