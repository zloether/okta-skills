#!/usr/bin/env python3
"""Read Okta system log events via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / 'shared'))
from okta_client import get_session, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.since:
        params['since'] = args.since
    if args.until:
        params['until'] = args.until
    if args.filter:
        params['filter'] = args.filter
    if args.q:
        params['q'] = args.q
    if args.sort_order:
        params['sortOrder'] = args.sort_order
    return paginated_get(session, f'{base_url}/api/v1/logs', params, limit=args.limit)


def main():
    parser = argparse.ArgumentParser(description='Read Okta system log events')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List log events')
    p_list.add_argument('--since', help='Start time in ISO 8601 format (e.g. 2024-01-01T00:00:00Z)')
    p_list.add_argument('--until', help='End time in ISO 8601 format')
    p_list.add_argument('--filter', help='SCIM filter expression (e.g. eventType eq "user.session.start" or outcome.result eq "FAILURE")')
    p_list.add_argument('--q', help='Keyword search (case-insensitive, matches against log event properties)')
    p_list.add_argument('--sort-order', dest='sort_order', choices=['ASCENDING', 'DESCENDING'], help='Sort order by published timestamp (default: ASCENDING)')
    p_list.add_argument('--limit', type=int, help='Maximum number of events to return (max 1000)')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'list':
            result = cmd_list(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
