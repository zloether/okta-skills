#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta realms and realm assignments via the Okta API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run
from okta_client import get_resource, paginated_get


def cmd_list_realms(session, base_url, args):
    params = {}
    if args.search:
        params['search'] = args.search
    if args.sort_by:
        params['sortBy'] = args.sort_by
    if args.sort_order:
        params['sortOrder'] = args.sort_order
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(session, f'{base_url}/api/v1/realms', params, limit=args.limit)


def cmd_get_realm(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/realms/{args.id}')


def cmd_list_realm_assignments(session, base_url, args):
    params = {}
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(session, f'{base_url}/api/v1/realm-assignments', params, limit=args.limit)


def cmd_get_realm_assignment(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/realm-assignments/{args.id}')


def cmd_list_realm_assignment_operations(session, base_url, args):
    params = {}
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(session, f'{base_url}/api/v1/realm-assignments/operations', params, limit=args.limit)


def main():
    parser = argparse.ArgumentParser(description='Read Okta realms and realm assignments')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list_realms = sub.add_parser('list-realms', help='List all realms')
    p_list_realms.add_argument('--search', help='Filter expression, e.g. \'profile.name co "Realm"\'')
    p_list_realms.add_argument('--sort-by', help='Property to sort by (search queries only)')
    p_list_realms.add_argument('--sort-order', choices=['asc', 'desc'], help='Sort order (search queries only)')
    p_list_realms.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_realm = sub.add_parser('get-realm', help='Get a realm by ID')
    p_get_realm.add_argument('id', help='Realm ID')

    p_list_assignments = sub.add_parser('list-realm-assignments', help='List all realm assignments')
    p_list_assignments.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_assignment = sub.add_parser('get-realm-assignment', help='Get a realm assignment by ID')
    p_get_assignment.add_argument('id', help='Realm assignment ID')

    p_list_operations = sub.add_parser('list-realm-assignment-operations', help='List all realm assignment operations')
    p_list_operations.add_argument('--limit', type=int, help='Maximum number of results')

    run(parser, {
        'list-realms': cmd_list_realms,
        'get-realm': cmd_get_realm,
        'list-realm-assignments': cmd_list_realm_assignments,
        'get-realm-assignment': cmd_get_realm_assignment,
        'list-realm-assignment-operations': cmd_list_realm_assignment_operations,
    })


if __name__ == '__main__':
    main()
