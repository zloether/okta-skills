#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta system log events via the Okta API."""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
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


def cmd_login_failures(session, base_url, args):
    # Default to last 24 hours if no --since provided
    since = args.since or (
        datetime.now(timezone.utc) - timedelta(hours=24)
    ).strftime('%Y-%m-%dT%H:%M:%SZ')

    outcome_expr = 'outcome.result eq "FAILURE" or outcome.result eq "DENY"'
    if args.user:
        if '"' in args.user:
            raise ValueError('--user value cannot contain a double-quote character')
        f = f'actor.alternateId eq "{args.user}" and ({outcome_expr})'
    else:
        f = outcome_expr

    params = {'since': since, 'filter': f}
    if args.until:
        params['until'] = args.until
    if args.q:
        params['q'] = args.q
    if args.sort_order:
        params['sortOrder'] = args.sort_order

    all_events = paginated_get(session, f'{base_url}/api/v1/logs', params, limit=args.limit)

    by_outcome = {'FAILURE': 0, 'DENY': 0}
    by_event_type = {}
    for event in all_events:
        outcome = event.get('outcome', {}).get('result', 'unknown')
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
        et = event.get('eventType', 'unknown')
        by_event_type[et] = by_event_type.get(et, 0) + 1

    return {
        'summary': {
            'since': since,
            'until': args.until,
            'user': args.user,
            'total': len(all_events),
            'by_outcome': by_outcome,
            'by_event_type': dict(sorted(by_event_type.items(), key=lambda x: -x[1])),
        },
        'events': all_events,
    }


def main():
    parser = argparse.ArgumentParser(description='Read Okta system log events')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List log events')
    p_list.add_argument('--since', help='Start time in ISO 8601 format (e.g. 2024-01-01T00:00:00Z)')
    p_list.add_argument('--until', help='End time in ISO 8601 format')
    p_list.add_argument('--filter', help='SCIM filter expression (e.g. eventType eq "user.session.start" or outcome.result eq "FAILURE")')
    p_list.add_argument('--q', help='Keyword search (case-insensitive, matches against log event properties)')
    p_list.add_argument('--sort-order', dest='sort_order', choices=['ASCENDING', 'DESCENDING'], help='Sort order by published timestamp (default: ASCENDING)')
    p_list.add_argument('--limit', type=int, help='Maximum number of events to return')

    p_failures = sub.add_parser('login-failures', help='Summarize login failures and denials')
    p_failures.add_argument('--since', help='Start time in ISO 8601 format (defaults to 24 hours ago)')
    p_failures.add_argument('--until', help='End time in ISO 8601 format')
    p_failures.add_argument('--user', help='Filter by user login / email (actor.alternateId)')
    p_failures.add_argument('--q', help='Keyword search (case-insensitive, matches against log event properties)')
    p_failures.add_argument('--sort-order', dest='sort_order', choices=['ASCENDING', 'DESCENDING'], help='Sort order by published timestamp (default: ASCENDING)')
    p_failures.add_argument('--limit', type=int, help='Maximum number of events to return')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'list':
            result = cmd_list(session, base_url, args)
        elif args.command == 'login-failures':
            result = cmd_login_failures(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
