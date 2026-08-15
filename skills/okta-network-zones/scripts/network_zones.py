#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta network zones via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.type:
        params['filter'] = f'type eq "{args.type}"'
    elif args.usage:
        params['filter'] = f'usage eq "{args.usage}"'
    elif args.system is not None:
        params['filter'] = f'system eq {"true" if args.system else "false"}'
    return paginated_get(session, f'{base_url}/api/v1/zones', params, limit=args.limit)


def cmd_get(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/zones/{args.id}')
    resp.raise_for_status()
    return resp.json()


def _parse_bool(value):
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    raise argparse.ArgumentTypeError(f"invalid value {value!r}, expected 'true' or 'false'")


def main():
    parser = argparse.ArgumentParser(description='Read Okta network zones')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List network zones')
    p_list_grp = p_list.add_mutually_exclusive_group()
    p_list_grp.add_argument(
        '--type',
        help='Filter by zone type (IP, DYNAMIC, DYNAMIC_V2) — note: the spec documents filtering '
        'as supported on id/usage/system, not type; verify against a live org',
    )
    p_list_grp.add_argument('--usage', choices=['POLICY', 'BLOCKLIST'], help='Filter by zone usage')
    p_list_grp.add_argument(
        '--system', type=_parse_bool, metavar='{true,false}',
        help='Filter to system-defined (true) or custom (false) zones',
    )
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

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
