#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta OAuth 2.0 client app role assignments via the Okta API."""
import argparse
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run
from okta_client import get_resource, paginated_get


def cmd_list(session, base_url, args):
    return paginated_get(session, f'{base_url}/oauth2/v1/clients/{quote(args.client_id, safe="")}/roles')


def cmd_get(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/oauth2/v1/clients/{quote(args.client_id, safe="")}'
        f'/roles/{quote(args.role_assignment_id, safe="")}',
    )


def cmd_list_app_targets(session, base_url, args):
    params = {'limit': args.limit} if args.limit else {}
    return paginated_get(
        session,
        f'{base_url}/oauth2/v1/clients/{quote(args.client_id, safe="")}'
        f'/roles/{quote(args.role_assignment_id, safe="")}/targets/catalog/apps',
        params,
        limit=args.limit,
    )


def cmd_list_group_targets(session, base_url, args):
    params = {'limit': args.limit} if args.limit else {}
    return paginated_get(
        session,
        f'{base_url}/oauth2/v1/clients/{quote(args.client_id, safe="")}'
        f'/roles/{quote(args.role_assignment_id, safe="")}/targets/groups',
        params,
        limit=args.limit,
    )


def main():
    parser = argparse.ArgumentParser(description='Read Okta OAuth 2.0 client app role assignments')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List all role assignments for a client app')
    p_list.add_argument('client_id', help='OAuth 2.0 client ID')

    p_get = sub.add_parser('get', help='Get a specific role assignment for a client app')
    p_get.add_argument('client_id', help='OAuth 2.0 client ID')
    p_get.add_argument('role_assignment_id', help='Role assignment ID')

    p_app_targets = sub.add_parser(
        'list-app-targets', help="List OIN app targets for a client's APP_ADMIN role assignment"
    )
    p_app_targets.add_argument('client_id', help='OAuth 2.0 client ID')
    p_app_targets.add_argument('role_assignment_id', help='Role assignment ID')
    p_app_targets.add_argument('--limit', type=int, help='Maximum number of results')

    p_group_targets = sub.add_parser(
        'list-group-targets',
        help="List group targets for a client's USER_ADMIN/HELP_DESK_ADMIN/GROUP_MEMBERSHIP_ADMIN role assignment",
    )
    p_group_targets.add_argument('client_id', help='OAuth 2.0 client ID')
    p_group_targets.add_argument('role_assignment_id', help='Role assignment ID')
    p_group_targets.add_argument('--limit', type=int, help='Maximum number of results')

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
        'list-app-targets': cmd_list_app_targets,
        'list-group-targets': cmd_list_group_targets,
    })


if __name__ == '__main__':
    main()
