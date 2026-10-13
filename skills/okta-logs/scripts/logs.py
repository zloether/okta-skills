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
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import STREAMED, add_page_size, apply_output_options, run, with_page_size
from okta_client import paginated_get


def _quote(value, flag):
    # Not urllib.parse.quote: this is a filter *expression* value sent via
    # params=, which requests URL-encodes automatically — it's not a raw
    # URL path segment.
    if '"' in value:
        raise ValueError(f'{flag} value cannot contain a double-quote character')
    return value


def _get_path(obj, path):
    for key in path.split('.'):
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj


def _member_ids(session, base_url, group_id):
    users = paginated_get(session, '{base}/api/v1/groups/{id}/users', path_params={'base': base_url, 'id': group_id})
    return {u['id'] for u in users}


def _in_group(event, ids):
    return event.get('actor', {}).get('id') in ids or any(t.get('id') in ids for t in event.get('target') or [])


def _fetch(session, base_url, args, params):
    """Fetch events, reporting progress on stderr and optionally streaming JSON Lines to stdout.

    Returns the event list, or STREAMED if --jsonl already printed them.
    """
    member_ids = _member_ids(session, base_url, args.member_of) if getattr(args, 'member_of', None) else None
    jsonl = getattr(args, 'jsonl', False)

    def on_page(items, total):
        if total > len(items):  # only chatter once a pull spans multiple pages
            print(f'[okta-skills] fetched {total} events (up to {items[-1].get("published")})', file=sys.stderr, flush=True)
        if jsonl:
            for e in items[: max(0, (args.limit or total) - (total - len(items)))]:
                if member_ids is None or _in_group(e, member_ids):
                    print(json.dumps(apply_output_options(args, e)), flush=True)

    events = paginated_get(session, f'{base_url}/api/v1/logs', with_page_size(params, args, 1000), limit=args.limit, on_page=on_page)
    if jsonl:
        return STREAMED
    if member_ids is not None:
        events = [e for e in events if _in_group(e, member_ids)]
    return events


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
    if args.count_by and args.jsonl:
        raise ValueError('--count-by and --jsonl cannot be combined')
    events = _fetch(session, base_url, args, params)
    if args.count_by:
        counts = {}
        for e in events:
            v = _get_path(e, args.count_by)
            key = '(none)' if v is None else str(v)
            counts[key] = counts.get(key, 0) + 1
        return {
            'field': args.count_by,
            'total': len(events),
            'counts': dict(sorted(counts.items(), key=lambda x: -x[1])),
        }
    return events


def _timeline_row(e):
    targets = e.get('target') or []
    app = next((t for t in targets if t.get('type') == 'AppInstance'), None)
    return {
        'published': e.get('published'),
        'eventType': e.get('eventType'),
        'result': _get_path(e, 'outcome.result'),
        'reason': _get_path(e, 'outcome.reason'),
        'actor': _get_path(e, 'actor.alternateId'),
        'app': (app.get('displayName') or app.get('id')) if app else None,
        'ip': _get_path(e, 'client.ipAddress'),
        'grantType': _get_path(e, 'debugContext.debugData.grantType'),
        'transactionId': _get_path(e, 'transaction.id'),
        'rootSessionId': _get_path(e, 'authenticationContext.rootSessionId'),
    }


def cmd_timeline(session, base_url, args):
    clauses = []
    if args.user:
        u = _quote(args.user, '--user')
        # On OAuth token events the actor is the client app and the user is only in target[]
        clauses.append(f'(actor.alternateId eq "{u}" or target.alternateId eq "{u}")')
    if args.app:
        clauses.append(f'target.id eq "{_quote(args.app, "--app")}"')
    if args.filter:
        clauses.append(f'({args.filter})')
    params = {'sortOrder': 'ASCENDING'}
    if clauses:
        params['filter'] = ' and '.join(clauses)
    if args.since:
        params['since'] = args.since
    if args.until:
        params['until'] = args.until

    jsonl = args.jsonl
    args.jsonl = False  # rows are reshaped below, so stream here rather than in _fetch
    events = _fetch(session, base_url, args, params)
    rows = [_timeline_row(e) for e in events]
    if jsonl:
        for r in rows:
            print(json.dumps(apply_output_options(args, r)), flush=True)
        return STREAMED
    return rows


def cmd_login_failures(session, base_url, args):
    # Default to last 24 hours if no --since provided
    since = args.since or (
        datetime.now(UTC) - timedelta(hours=24)
    ).strftime('%Y-%m-%dT%H:%M:%SZ')

    outcome_expr = 'outcome.result eq "FAILURE" or outcome.result eq "DENY"'
    if args.user:
        f = f'actor.alternateId eq "{_quote(args.user, "--user")}" and ({outcome_expr})'
    else:
        f = outcome_expr

    params = {'since': since, 'filter': f}
    if args.until:
        params['until'] = args.until
    if args.q:
        params['q'] = args.q
    if args.sort_order:
        params['sortOrder'] = args.sort_order

    all_events = paginated_get(session, f'{base_url}/api/v1/logs', with_page_size(params, args, 1000), limit=args.limit)

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
            'truncated': bool(args.limit) and len(all_events) >= args.limit,
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
    p_list.add_argument('--jsonl', action='store_true', help='Print one JSON event per line as each page arrives, instead of one array at the end')
    p_list.add_argument('--count-by', dest='count_by', help='Instead of events, return counts grouped by this dotted field (e.g. eventType, outcome.result, client.ipAddress)')
    p_list.add_argument('--member-of', dest='member_of', metavar='GROUP_ID', help='Keep only events whose actor or target is a member of this group (filtered client-side after fetching; combine with --filter/--since to bound the pull)')
    add_page_size(p_list, 1000)

    p_timeline = sub.add_parser('timeline', help='Compact chronological view of one user\'s and/or one app\'s events')
    p_timeline.add_argument('--user', help='User login / email; matches events where the user is the actor or a target')
    p_timeline.add_argument('--app', help='Application ID; matches events targeting that app')
    p_timeline.add_argument('--filter', help='Additional SCIM filter expression, ANDed with --user/--app')
    p_timeline.add_argument('--since', help='Start time in ISO 8601 format')
    p_timeline.add_argument('--until', help='End time in ISO 8601 format')
    p_timeline.add_argument('--limit', type=int, help='Maximum number of events to return')
    p_timeline.add_argument('--jsonl', action='store_true', help='Print one compact JSON row per line instead of one array')
    add_page_size(p_timeline, 1000)

    p_failures = sub.add_parser('login-failures', help='Summarize login failures and denials')
    p_failures.add_argument('--since', help='Start time in ISO 8601 format (defaults to 24 hours ago)')
    p_failures.add_argument('--until', help='End time in ISO 8601 format')
    p_failures.add_argument('--user', help='Filter by user login / email (actor.alternateId)')
    p_failures.add_argument('--q', help='Keyword search (case-insensitive, matches against log event properties)')
    p_failures.add_argument('--sort-order', dest='sort_order', choices=['ASCENDING', 'DESCENDING'], help='Sort order by published timestamp (default: ASCENDING)')
    p_failures.add_argument('--limit', type=int, help='Maximum number of events to return')
    add_page_size(p_failures, 1000)

    run(parser, {
        'list': cmd_list,
        'timeline': cmd_timeline,
        'login-failures': cmd_login_failures,
    })


if __name__ == '__main__':
    main()
