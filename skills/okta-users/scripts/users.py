#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta users via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.filter:
        params['filter'] = args.filter
    return paginated_get(session, f'{base_url}/api/v1/users', params, limit=args.limit)


def cmd_get(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}')
    resp.raise_for_status()
    return resp.json()


def cmd_search(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/users', {'q': args.query})


def cmd_get_apps(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/users/{args.id}/appLinks')


def cmd_get_blocks(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/blocks')
    resp.raise_for_status()
    return resp.json()


def cmd_get_groups(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/users/{args.id}/groups')


def cmd_get_idps(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/idps')
    resp.raise_for_status()
    return resp.json()


def cmd_get_linked_objects(session, base_url, args):
    return paginated_get(
        session,
        f'{base_url}/api/v1/users/{args.id}/linkedObjects/{args.relationship}',
    )


def cmd_get_enrollments(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/authenticator-enrollments')
    resp.raise_for_status()
    return resp.json()


def cmd_get_classification(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/classification')
    resp.raise_for_status()
    return resp.json()


def cmd_get_clients(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/users/{args.id}/clients')


def cmd_get_client_grants(session, base_url, args):
    params = {}
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        f'{base_url}/api/v1/users/{args.id}/clients/{args.client_id}/grants',
        params,
        limit=args.limit,
    )


def cmd_get_client_tokens(session, base_url, args):
    params = {}
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        f'{base_url}/api/v1/users/{args.id}/clients/{args.client_id}/tokens',
        params,
        limit=args.limit,
    )


def cmd_get_client_token(session, base_url, args):
    resp = session.get(
        f'{base_url}/api/v1/users/{args.id}/clients/{args.client_id}/tokens/{args.token_id}'
    )
    resp.raise_for_status()
    return resp.json()


def cmd_get_devices(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/devices')
    resp.raise_for_status()
    return resp.json()


def cmd_get_factors(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/factors')
    resp.raise_for_status()
    return resp.json()


def cmd_get_grants(session, base_url, args):
    params = {}
    if args.scope_id:
        params['scopeId'] = args.scope_id
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        f'{base_url}/api/v1/users/{args.id}/grants',
        params,
        limit=args.limit,
    )


def cmd_get_grant(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/grants/{args.grant_id}')
    resp.raise_for_status()
    return resp.json()


def cmd_get_risk(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/risk')
    resp.raise_for_status()
    return resp.json()


def cmd_get_roles(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/users/{args.id}/roles')


def cmd_get_role(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/roles/{args.role_id}')
    resp.raise_for_status()
    return resp.json()


def cmd_get_subscriptions(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/users/{args.id}/subscriptions')
    resp.raise_for_status()
    return resp.json()


def cmd_get_subscription(session, base_url, args):
    resp = session.get(
        f'{base_url}/api/v1/users/{args.id}/subscriptions/{args.notification_type}'
    )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description='Read Okta users')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List users')
    p_list.add_argument('--filter', help='SCIM filter expression')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get a user by ID or login')
    p_get.add_argument('id', help='User ID or login (email)')

    p_search = sub.add_parser('search', help='Search users by name or email')
    p_search.add_argument('query', help='Search query')

    p_get_apps = sub.add_parser('get-apps', help='List all app links for a user')
    p_get_apps.add_argument('id', help='User ID or login')

    p_get_blocks = sub.add_parser('get-blocks', help='List blocks on a user account')
    p_get_blocks.add_argument('id', help='User ID or login')

    p_get_groups = sub.add_parser('get-groups', help='List all groups a user belongs to')
    p_get_groups.add_argument('id', help='User ID or login')

    p_get_idps = sub.add_parser('get-idps', help='List identity providers linked to a user')
    p_get_idps.add_argument('id', help='User ID or login')

    p_get_linked = sub.add_parser('get-linked-objects', help='List linked objects for a relationship')
    p_get_linked.add_argument('id', help='User ID or login')
    p_get_linked.add_argument('relationship', help='Relationship name (e.g. manager, subordinates)')

    p_get_enroll = sub.add_parser('get-enrollments', help='List authenticator enrollments (OIE only)')
    p_get_enroll.add_argument('id', help='User ID')

    p_get_class = sub.add_parser('get-classification', help='Retrieve user classification')
    p_get_class.add_argument('id', help='User ID')

    p_get_clients = sub.add_parser('get-clients', help='List OAuth clients with grants or tokens for a user')
    p_get_clients.add_argument('id', help='User ID or login')

    p_get_cg = sub.add_parser('get-client-grants', help='List grants for a user+client pair')
    p_get_cg.add_argument('id', help='User ID or login')
    p_get_cg.add_argument('client_id', help='OAuth client ID')
    p_get_cg.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_ct = sub.add_parser('get-client-tokens', help='List refresh tokens for a user+client pair')
    p_get_ct.add_argument('id', help='User ID or login')
    p_get_ct.add_argument('client_id', help='OAuth client ID')
    p_get_ct.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_ctoken = sub.add_parser('get-client-token', help='Get a specific refresh token for a user+client pair')
    p_get_ctoken.add_argument('id', help='User ID or login')
    p_get_ctoken.add_argument('client_id', help='OAuth client ID')
    p_get_ctoken.add_argument('token_id', help='Token ID')

    p_get_devices = sub.add_parser('get-devices', help='List enrolled devices for a user (OIE only)')
    p_get_devices.add_argument('id', help='User ID')

    p_get_factors = sub.add_parser('get-factors', help='List enrolled MFA factors for a user')
    p_get_factors.add_argument('id', help='User ID or login')

    p_get_grants = sub.add_parser('get-grants', help='List OAuth2 scope consent grants for a user')
    p_get_grants.add_argument('id', help='User ID or login')
    p_get_grants.add_argument('--scope-id', help='Filter by scope ID')
    p_get_grants.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_grant = sub.add_parser('get-grant', help='Get a specific OAuth2 grant for a user')
    p_get_grant.add_argument('id', help='User ID or login')
    p_get_grant.add_argument('grant_id', help='Grant ID')

    p_get_risk = sub.add_parser('get-risk', help='Retrieve user risk level')
    p_get_risk.add_argument('id', help='User ID')

    p_get_roles = sub.add_parser('get-roles', help='List admin roles assigned to a user')
    p_get_roles.add_argument('id', help='User ID or login')

    p_get_role = sub.add_parser('get-role', help='Get a specific role assignment for a user')
    p_get_role.add_argument('id', help='User ID or login')
    p_get_role.add_argument('role_id', help='Role assignment ID')

    p_get_subs = sub.add_parser('get-subscriptions', help='List notification subscriptions for a user')
    p_get_subs.add_argument('id', help='User ID')

    p_get_sub = sub.add_parser('get-subscription', help='Get a specific notification subscription for a user')
    p_get_sub.add_argument('id', help='User ID')
    p_get_sub.add_argument('notification_type', help='Notification type')

    args = parser.parse_args()
    session, base_url = get_session()

    commands = {
        'list': cmd_list,
        'get': cmd_get,
        'search': cmd_search,
        'get-apps': cmd_get_apps,
        'get-blocks': cmd_get_blocks,
        'get-groups': cmd_get_groups,
        'get-idps': cmd_get_idps,
        'get-linked-objects': cmd_get_linked_objects,
        'get-enrollments': cmd_get_enrollments,
        'get-classification': cmd_get_classification,
        'get-clients': cmd_get_clients,
        'get-client-grants': cmd_get_client_grants,
        'get-client-tokens': cmd_get_client_tokens,
        'get-client-token': cmd_get_client_token,
        'get-devices': cmd_get_devices,
        'get-factors': cmd_get_factors,
        'get-grants': cmd_get_grants,
        'get-grant': cmd_get_grant,
        'get-risk': cmd_get_risk,
        'get-roles': cmd_get_roles,
        'get-role': cmd_get_role,
        'get-subscriptions': cmd_get_subscriptions,
        'get-subscription': cmd_get_subscription,
    }

    try:
        result = commands[args.command](session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
