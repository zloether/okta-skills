#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta groups via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session, get_resource, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.filter:
        params['filter'] = args.filter
    if args.search:
        params['search'] = args.search
    if args.q:
        params['q'] = args.q
    if args.expand:
        params['expand'] = args.expand
    if args.sort_by:
        params['sortBy'] = args.sort_by
    if args.sort_order:
        params['sortOrder'] = args.sort_order
    return paginated_get(session, f'{base_url}/api/v1/groups', params, limit=args.limit)


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/groups/{args.id}')


def cmd_get_members(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/groups/{args.id}/users', limit=args.limit)


def cmd_search(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/groups', {'q': args.query})


def cmd_get_apps(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/groups/{args.id}/apps', limit=args.limit)


def cmd_get_owners(session, base_url, args):
    params = {}
    if args.search:
        params['search'] = args.search
    return paginated_get(session, f'{base_url}/api/v1/groups/{args.id}/owners', params, limit=args.limit)


def cmd_list_rules(session, base_url, args):
    params = {}
    if args.search:
        params['search'] = args.search
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/groups/rules', params, limit=args.limit)


def cmd_get_rule(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/groups/rules/{args.id}')


def cmd_list_roles(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/groups/{args.id}/roles', params)


def cmd_get_role(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/groups/{args.id}/roles/{args.role_id}')


def cmd_list_role_app_targets(session, base_url, args):
    return paginated_get(
        session,
        f'{base_url}/api/v1/groups/{args.id}/roles/{args.role_id}/targets/catalog/apps',
        limit=args.limit,
    )


def cmd_list_role_group_targets(session, base_url, args):
    return paginated_get(
        session,
        f'{base_url}/api/v1/groups/{args.id}/roles/{args.role_id}/targets/groups',
        limit=args.limit,
    )


def main():
    parser = argparse.ArgumentParser(description='Read Okta groups')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List groups')
    p_list_grp = p_list.add_mutually_exclusive_group()
    p_list_grp.add_argument('--filter', help='Filter expression (id, type, lastUpdated, lastMembershipUpdated only)')
    p_list_grp.add_argument('--search', help='Search expression (any profile attribute; recommended over --filter)')
    p_list_grp.add_argument('--q', help='Search groups by name prefix. Note: disables pagination and defaults to a 300-result limit per the Okta API')
    p_list.add_argument('--expand', help='Expand response, e.g. stats (member count) or app')
    p_list.add_argument('--sort-by', help='Property to sort by (search queries only)')
    p_list.add_argument('--sort-order', choices=['asc', 'desc'], help='Sort order (search queries only)')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get a group by ID')
    p_get.add_argument('id', help='Group ID')

    p_members = sub.add_parser('get-members', help='List users in a group')
    p_members.add_argument('id', help='Group ID')
    p_members.add_argument('--limit', type=int, help='Maximum number of results')

    p_search = sub.add_parser('search', help='Search groups by name')
    p_search.add_argument('query', help='Search query')

    p_apps = sub.add_parser('get-apps', help='List apps assigned to a group')
    p_apps.add_argument('id', help='Group ID')
    p_apps.add_argument('--limit', type=int, help='Maximum number of results')

    p_owners = sub.add_parser('get-owners', help='List owners of a group')
    p_owners.add_argument('id', help='Group ID')
    p_owners.add_argument('--search', help='Search expression to filter owners')
    p_owners.add_argument('--limit', type=int, help='Maximum number of results')

    p_list_rules = sub.add_parser('list-rules', help='List all group rules in the org')
    p_list_rules.add_argument('--search', help='Keyword to search rules for')
    p_list_rules.add_argument('--expand', help='Expand response, e.g. groupIdToGroupNameMap')
    p_list_rules.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_rule = sub.add_parser('get-rule', help='Get a group rule by ID')
    p_get_rule.add_argument('id', help='Group rule ID')

    p_list_roles = sub.add_parser('list-roles', help='List role assignments for a group')
    p_list_roles.add_argument('id', help='Group ID')
    p_list_roles.add_argument('--expand', help='Expand response')

    p_get_role = sub.add_parser('get-role', help='Get a specific role assignment for a group')
    p_get_role.add_argument('id', help='Group ID')
    p_get_role.add_argument('role_id', help='Role assignment ID')

    p_role_app_targets = sub.add_parser(
        'list-role-app-targets', help="List app targets for a group's admin role"
    )
    p_role_app_targets.add_argument('id', help='Group ID')
    p_role_app_targets.add_argument('role_id', help='Role assignment ID')
    p_role_app_targets.add_argument('--limit', type=int, help='Maximum number of results')

    p_role_group_targets = sub.add_parser(
        'list-role-group-targets', help="List group targets for a group's role"
    )
    p_role_group_targets.add_argument('id', help='Group ID')
    p_role_group_targets.add_argument('role_id', help='Role assignment ID')
    p_role_group_targets.add_argument('--limit', type=int, help='Maximum number of results')

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
        elif args.command == 'get-apps':
            result = cmd_get_apps(session, base_url, args)
        elif args.command == 'get-owners':
            result = cmd_get_owners(session, base_url, args)
        elif args.command == 'list-rules':
            result = cmd_list_rules(session, base_url, args)
        elif args.command == 'get-rule':
            result = cmd_get_rule(session, base_url, args)
        elif args.command == 'list-roles':
            result = cmd_list_roles(session, base_url, args)
        elif args.command == 'get-role':
            result = cmd_get_role(session, base_url, args)
        elif args.command == 'list-role-app-targets':
            result = cmd_list_role_app_targets(session, base_url, args)
        elif args.command == 'list-role-group-targets':
            result = cmd_list_role_group_targets(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
