#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta users via the Okta API."""
import argparse
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import KeyedResults, add_page_size, run, with_page_size
from okta_client import get_resource, paginated_get, paginated_get_wrapped

USER_ID_RE = re.compile(r'^00u[a-zA-Z0-9]{17}$')


def resolve_user_id(session, base_url, value):
    """Only /users/{idOrLogin} accepts a login; sub-resource endpoints require the ID."""
    if USER_ID_RE.match(value):
        return value
    return get_resource(session, '{base}/api/v1/users/{id}', path_params={'base': base_url, 'id': value})['id']


def cmd_list(session, base_url, args):
    params = {}
    if args.filter:
        params['filter'] = args.filter
    if args.search:
        params['search'] = args.search
    if args.q:
        params['q'] = args.q
    if args.sort_by:
        params['sortBy'] = args.sort_by
    if args.sort_order:
        params['sortOrder'] = args.sort_order
    if args.fields:
        params['fields'] = args.fields
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/users', with_page_size(params, args), limit=args.limit)


def cmd_get(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(session, '{base}/api/v1/users/{id}', params=params, path_params={'base': base_url, 'id': args.id})


def cmd_search(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/users', with_page_size({'q': args.query}, args), limit=args.limit)


def cmd_get_apps(session, base_url, args):
    return paginated_get(session, '{base}/api/v1/users/{id}/appLinks', path_params={'base': base_url, 'id': args.id})


def cmd_get_blocks(session, base_url, args):
    return get_resource(session, '{base}/api/v1/users/{id}/blocks', path_params={'base': base_url, 'id': args.id})


def cmd_get_groups(session, base_url, args):
    return paginated_get(session, '{base}/api/v1/users/{id}/groups', path_params={'base': base_url, 'id': args.id})


def cmd_get_idps(session, base_url, args):
    return get_resource(session, '{base}/api/v1/users/{id}/idps', path_params={'base': base_url, 'id': args.id})


def cmd_get_linked_objects(session, base_url, args):
    return paginated_get(
        session,
        '{base}/api/v1/users/{id}/linkedObjects/{relationship}',
        path_params={'base': base_url, 'id': args.id, 'relationship': args.relationship},
    )


def _for_each_user(session, base_url, args, fetch):
    """Run fetch(user_id) for args.id, or for every ID/login in --ids-file ('-' = stdin).

    Batch mode returns {identifier: result}; a failure for one user is recorded
    as {"error": ...} under that key instead of aborting the whole batch.
    """
    if args.id and args.ids_file:
        raise ValueError('provide a user ID/login or --ids-file, not both')
    if not args.ids_file:
        if not args.id:
            raise ValueError('provide a user ID/login or --ids-file')
        return fetch(args.id)
    text = sys.stdin.read() if args.ids_file == '-' else Path(args.ids_file).read_text()
    lines = text.splitlines()
    results = KeyedResults()
    for ident in (line.strip() for line in lines):
        if not ident or ident.startswith('#'):
            continue
        try:
            results[ident] = fetch(resolve_user_id(session, base_url, ident))
        except requests.HTTPError as e:
            results[ident] = {'error': str(e)}
    return results


def cmd_get_enrollments(session, base_url, args):
    params = {}
    if args.disclose_identifiers:
        params['discloseIdentifiers'] = args.disclose_identifiers

    def fetch(user_id):
        return get_resource(
            session, '{base}/api/v1/users/{id}/authenticator-enrollments', params=params,
            path_params={'base': base_url, 'id': user_id},
        )

    return _for_each_user(session, base_url, args, fetch)


def cmd_get_classification(session, base_url, args):
    return get_resource(session, '{base}/api/v1/users/{id}/classification', path_params={'base': base_url, 'id': args.id})


def cmd_get_clients(session, base_url, args):
    return paginated_get(session, '{base}/api/v1/users/{id}/clients', path_params={'base': base_url, 'id': args.id})


def cmd_get_client_grants(session, base_url, args):
    params = {}
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        '{base}/api/v1/users/{id}/clients/{client_id}/grants',
        params,
        limit=args.limit,
        path_params={'base': base_url, 'id': args.id, 'client_id': args.client_id},
    )


def cmd_get_client_tokens(session, base_url, args):
    params = {}
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        '{base}/api/v1/users/{id}/clients/{client_id}/tokens',
        params,
        limit=args.limit,
        path_params={'base': base_url, 'id': args.id, 'client_id': args.client_id},
    )


def cmd_get_client_token(session, base_url, args):
    return get_resource(
        session,
        '{base}/api/v1/users/{id}/clients/{client_id}/tokens/{token_id}',
        path_params={'base': base_url, 'id': args.id, 'client_id': args.client_id, 'token_id': args.token_id},
    )


def cmd_get_devices(session, base_url, args):
    return get_resource(session, '{base}/api/v1/users/{id}/devices', path_params={'base': base_url, 'id': args.id})


def cmd_get_factors(session, base_url, args):
    def fetch(user_id):
        return get_resource(session, '{base}/api/v1/users/{id}/factors', path_params={'base': base_url, 'id': user_id})

    return _for_each_user(session, base_url, args, fetch)


def cmd_get_grants(session, base_url, args):
    params = {}
    if args.scope_id:
        params['scopeId'] = args.scope_id
    if args.expand:
        params['expand'] = args.expand
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        '{base}/api/v1/users/{id}/grants',
        params,
        limit=args.limit,
        path_params={'base': base_url, 'id': args.id},
    )


def cmd_get_grant(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(
        session, '{base}/api/v1/users/{id}/grants/{grant_id}', params=params,
        path_params={'base': base_url, 'id': args.id, 'grant_id': args.grant_id},
    )


def cmd_get_risk(session, base_url, args):
    return get_resource(session, '{base}/api/v1/users/{id}/risk', path_params={'base': base_url, 'id': args.id})


def cmd_get_roles(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, '{base}/api/v1/users/{id}/roles', params, path_params={'base': base_url, 'id': args.id})


def cmd_get_role(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/users/{id}/roles/{role_id}',
        path_params={'base': base_url, 'id': args.id, 'role_id': args.role_id},
    )


def cmd_get_subscriptions(session, base_url, args):
    return get_resource(session, '{base}/api/v1/users/{id}/subscriptions', path_params={'base': base_url, 'id': args.id})


def cmd_get_subscription(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/users/{id}/subscriptions/{notification_type}',
        path_params={'base': base_url, 'id': args.id, 'notification_type': args.notification_type},
    )


def cmd_get_factors_catalog(session, base_url, args):
    return get_resource(session, '{base}/api/v1/users/{id}/factors/catalog', path_params={'base': base_url, 'id': args.id})


def cmd_get_factors_questions(session, base_url, args):
    return get_resource(session, '{base}/api/v1/users/{id}/factors/questions', path_params={'base': base_url, 'id': args.id})


def cmd_get_factor(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/users/{id}/factors/{factor_id}',
        path_params={'base': base_url, 'id': args.id, 'factor_id': args.factor_id},
    )


def cmd_get_factor_transaction(session, base_url, args):
    return get_resource(
        session,
        '{base}/api/v1/users/{id}/factors/{factor_id}/transactions/{transaction_id}',
        path_params={
            'base': base_url, 'id': args.id,
            'factor_id': args.factor_id, 'transaction_id': args.transaction_id,
        },
    )


def cmd_get_enrollment(session, base_url, args):
    params = {}
    if args.disclose_identifiers:
        params['discloseIdentifiers'] = args.disclose_identifiers
    return get_resource(
        session,
        '{base}/api/v1/users/{id}/authenticator-enrollments/{enrollment_id}',
        params=params,
        path_params={'base': base_url, 'id': args.id, 'enrollment_id': args.enrollment_id},
    )


def cmd_get_role_governance(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/users/{id}/roles/{role_id}/governance',
        path_params={'base': base_url, 'id': args.id, 'role_id': args.role_id},
    )


def cmd_get_role_governance_grant(session, base_url, args):
    return get_resource(
        session,
        '{base}/api/v1/users/{id}/roles/{role_id}/governance/{grant_id}',
        path_params={'base': base_url, 'id': args.id, 'role_id': args.role_id, 'grant_id': args.grant_id},
    )


def cmd_get_role_governance_grant_resources(session, base_url, args):
    return paginated_get_wrapped(
        session,
        '{base}/api/v1/users/{id}/roles/{role_id}/governance/{grant_id}/resources',
        'resources',
        limit=args.limit,
        path_params={'base': base_url, 'id': args.id, 'role_id': args.role_id, 'grant_id': args.grant_id},
    )


def cmd_get_role_app_targets(session, base_url, args):
    params = {}
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        '{base}/api/v1/users/{id}/roles/{role_id}/targets/catalog/apps',
        params,
        limit=args.limit,
        path_params={'base': base_url, 'id': args.id, 'role_id': args.role_id},
    )


def cmd_get_role_group_targets(session, base_url, args):
    params = {}
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        '{base}/api/v1/users/{id}/roles/{role_id}/targets/groups',
        params,
        limit=args.limit,
        path_params={'base': base_url, 'id': args.id, 'role_id': args.role_id},
    )


def cmd_get_role_targets(session, base_url, args):
    params = {}
    if args.assignment_type:
        params['assignmentType'] = args.assignment_type
    if args.limit:
        params['limit'] = args.limit
    return paginated_get(
        session,
        '{base}/api/v1/users/{id}/roles/{role_id}/targets',
        params,
        limit=args.limit,
        path_params={'base': base_url, 'id': args.id, 'role_id': args.role_id},
    )


def main():
    parser = argparse.ArgumentParser(description='Read Okta users')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List users')
    p_list_grp = p_list.add_mutually_exclusive_group()
    p_list_grp.add_argument('--filter', help='SCIM filter expression')
    p_list_grp.add_argument('--search', help='Search expression (any profile attribute; recommended over --filter)')
    p_list_grp.add_argument('--q', help='Search users by name prefix. Note: disables pagination and defaults to a 10-result limit per the Okta API')
    p_list.add_argument('--sort-by', help='Property to sort by (search queries only)')
    p_list.add_argument('--sort-order', choices=['asc', 'desc'], help='Sort order (search queries only)')
    p_list.add_argument('--fields', help='Fields to include, e.g. id,status,profile:(login,email) (dotted profile.login is rejected by Okta)')
    p_list.add_argument('--expand', help='Expand response; only "classification" is supported on list (use `get --expand blocks` for blocks)')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')
    add_page_size(p_list)

    p_get = sub.add_parser('get', help='Get a user by ID or login')
    p_get.add_argument('id', help='User ID or login (email)')
    p_get.add_argument('--expand', help='Expand response, e.g. blocks')

    p_search = sub.add_parser(
        'search',
        help='Search users by name or email. Note: disables pagination and defaults to a 10-result limit per the Okta API',
    )
    p_search.add_argument('query', help='Search query')
    p_search.add_argument('--limit', type=int, help='Maximum number of results')
    add_page_size(p_search)

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
    p_get_enroll.add_argument('id', nargs='?', help='User ID or login')
    p_get_enroll.add_argument('--ids-file', help='File of user IDs/logins, one per line (- for stdin); returns {identifier: enrollments}')
    p_get_enroll.add_argument(
        '--disclose-identifiers', action='store_const', const='phone',
        help='Disclose enrollment identifiers (e.g. show the actual phone number)',
    )

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
    p_get_factors.add_argument('id', nargs='?', help='User ID or login')
    p_get_factors.add_argument('--ids-file', help='File of user IDs/logins, one per line (- for stdin); returns {identifier: factors}')

    p_get_grants = sub.add_parser('get-grants', help='List OAuth2 scope consent grants for a user')
    p_get_grants.add_argument('id', help='User ID or login')
    p_get_grants.add_argument('--scope-id', help='Filter by scope ID')
    p_get_grants.add_argument('--expand', help='Expand response, e.g. scope')
    p_get_grants.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_grant = sub.add_parser('get-grant', help='Get a specific OAuth2 grant for a user')
    p_get_grant.add_argument('id', help='User ID or login')
    p_get_grant.add_argument('grant_id', help='Grant ID')
    p_get_grant.add_argument('--expand', help='Expand response, e.g. scope')

    p_get_risk = sub.add_parser('get-risk', help='Retrieve user risk level')
    p_get_risk.add_argument('id', help='User ID')

    p_get_roles = sub.add_parser('get-roles', help='List admin roles assigned to a user')
    p_get_roles.add_argument('id', help='User ID or login')
    p_get_roles.add_argument('--expand', help='Expand response, e.g. targets/groups')

    p_get_role = sub.add_parser('get-role', help='Get a specific role assignment for a user')
    p_get_role.add_argument('id', help='User ID or login')
    p_get_role.add_argument('role_id', help='Role assignment ID')

    p_get_subs = sub.add_parser('get-subscriptions', help='List notification subscriptions for a user')
    p_get_subs.add_argument('id', help='User ID')

    p_get_sub = sub.add_parser('get-subscription', help='Get a specific notification subscription for a user')
    p_get_sub.add_argument('id', help='User ID')
    p_get_sub.add_argument('notification_type', help='Notification type')

    p_get_fc = sub.add_parser('get-factors-catalog', help='List factor types available for enrollment by a user')
    p_get_fc.add_argument('id', help='User ID or login')

    p_get_fq = sub.add_parser('get-factors-questions', help='List available security questions for a user')
    p_get_fq.add_argument('id', help='User ID or login')

    p_get_factor = sub.add_parser('get-factor', help='Get a specific enrolled factor for a user')
    p_get_factor.add_argument('id', help='User ID or login')
    p_get_factor.add_argument('factor_id', help='Factor ID')

    p_get_ft = sub.add_parser('get-factor-transaction', help='Get the status of a push factor verification transaction')
    p_get_ft.add_argument('id', help='User ID or login')
    p_get_ft.add_argument('factor_id', help='Factor ID')
    p_get_ft.add_argument('transaction_id', help='Transaction ID')

    p_get_enroll1 = sub.add_parser('get-enrollment', help='Get a specific authenticator enrollment for a user (OIE only)')
    p_get_enroll1.add_argument('id', help='User ID')
    p_get_enroll1.add_argument('enrollment_id', help='Enrollment ID')
    p_get_enroll1.add_argument(
        '--disclose-identifiers', action='store_const', const='phone',
        help='Disclose enrollment identifiers (e.g. show the actual phone number)',
    )

    p_get_rg = sub.add_parser('get-role-governance', help='Retrieve the governance sources of a role assignment (Limited GA)')
    p_get_rg.add_argument('id', help='User ID or login')
    p_get_rg.add_argument('role_id', help='Role assignment ID')

    p_get_rgg = sub.add_parser('get-role-governance-grant', help='Retrieve a governance source for a role assignment (Limited GA)')
    p_get_rgg.add_argument('id', help='User ID or login')
    p_get_rgg.add_argument('role_id', help='Role assignment ID')
    p_get_rgg.add_argument('grant_id', help='Governance grant ID')

    p_get_rggr = sub.add_parser('get-role-governance-grant-resources', help='List resources of a role governance source grant (Limited GA)')
    p_get_rggr.add_argument('id', help='User ID or login')
    p_get_rggr.add_argument('role_id', help='Role assignment ID')
    p_get_rggr.add_argument('grant_id', help='Governance grant ID')
    p_get_rggr.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_rat = sub.add_parser('get-role-app-targets', help='List app targets for an APP_ADMIN role assignment')
    p_get_rat.add_argument('id', help='User ID or login')
    p_get_rat.add_argument('role_id', help='Role assignment ID')
    p_get_rat.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_rgt = sub.add_parser('get-role-group-targets', help='List group targets for a role assignment')
    p_get_rgt.add_argument('id', help='User ID or login')
    p_get_rgt.add_argument('role_id', help='Role assignment ID')
    p_get_rgt.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_rt = sub.add_parser('get-role-targets', help='Retrieve role targets by user and role assignment type')
    p_get_rt.add_argument('id', help='User ID or login')
    p_get_rt.add_argument('role_id', help='Role ID or Base32-encoded role name')
    p_get_rt.add_argument('--assignment-type', choices=['USER', 'GROUP'], help='Filter by assignment type')
    p_get_rt.add_argument('--limit', type=int, help='Maximum number of results')

    def resolve_id(args, session, base_url):
        if args.command != 'get' and getattr(args, 'id', None) and not getattr(args, 'ids_file', None):
            args.id = resolve_user_id(session, base_url, args.id)

    run(parser, {
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
        'get-factors-catalog': cmd_get_factors_catalog,
        'get-factors-questions': cmd_get_factors_questions,
        'get-factor': cmd_get_factor,
        'get-factor-transaction': cmd_get_factor_transaction,
        'get-enrollment': cmd_get_enrollment,
        'get-role-governance': cmd_get_role_governance,
        'get-role-governance-grant': cmd_get_role_governance_grant,
        'get-role-governance-grant-resources': cmd_get_role_governance_grant_resources,
        'get-role-app-targets': cmd_get_role_app_targets,
        'get-role-group-targets': cmd_get_role_group_targets,
        'get-role-targets': cmd_get_role_targets,
    }, before=resolve_id)


if __name__ == '__main__':
    main()
