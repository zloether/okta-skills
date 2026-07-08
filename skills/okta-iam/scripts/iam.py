#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta custom admin roles, resource sets, and governance bundles via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session, get_resource, paginated_get_wrapped  # noqa: E402


def cmd_list(session, base_url, args):
    return paginated_get_wrapped(session, f'{base_url}/api/v1/iam/roles', 'roles', limit=args.limit)


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/iam/roles/{args.role_id}')


def cmd_list_permissions(session, base_url, args):
    result = get_resource(session, f'{base_url}/api/v1/iam/roles/{args.role_id}/permissions')
    return result.get('permissions', [])


def cmd_get_permission(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/iam/roles/{args.role_id}/permissions/{args.permission_type}'
    )


def cmd_list_assignees(session, base_url, args):
    return paginated_get_wrapped(
        session, f'{base_url}/api/v1/iam/assignees/users', 'value', limit=args.limit
    )


def cmd_list_resource_sets(session, base_url, args):
    return paginated_get_wrapped(
        session, f'{base_url}/api/v1/iam/resource-sets', 'resource-sets', limit=args.limit
    )


def cmd_get_resource_set(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/iam/resource-sets/{args.resource_set_id}')


def cmd_list_bindings(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{args.resource_set_id}/bindings',
        'roles',
        limit=args.limit,
    )


def cmd_get_binding(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{args.resource_set_id}/bindings/{args.role_id}',
    )


def cmd_list_binding_members(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{args.resource_set_id}/bindings/{args.role_id}/members',
        'members',
        limit=args.limit,
    )


def cmd_get_binding_member(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{args.resource_set_id}/bindings/'
        f'{args.role_id}/members/{args.member_id}',
    )


def cmd_list_resources(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{args.resource_set_id}/resources',
        'resources',
        limit=args.limit,
    )


def cmd_get_resource(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{args.resource_set_id}/resources/{args.resource_id}',
    )


def cmd_list_bundles(session, base_url, args):
    return paginated_get_wrapped(
        session, f'{base_url}/api/v1/iam/governance/bundles', 'bundles', limit=args.limit
    )


def cmd_get_bundle(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/iam/governance/bundles/{args.bundle_id}')


def cmd_list_bundle_entitlements(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/governance/bundles/{args.bundle_id}/entitlements',
        'entitlements',
        limit=args.limit,
    )


def cmd_list_bundle_entitlement_values(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/governance/bundles/{args.bundle_id}/'
        f'entitlements/{args.entitlement_id}/values',
        'entitlementValues',
        limit=args.limit,
    )


def cmd_get_opt_in_status(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/iam/governance/optIn')


def cmd_list_role_subscriptions(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/roles/{args.role_ref}/subscriptions')


def cmd_get_role_subscription(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/roles/{args.role_ref}/subscriptions/{args.notification_type}'
    )


def main():
    parser = argparse.ArgumentParser(description='Read Okta admin roles, resource sets, and governance bundles')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List custom roles')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get a custom role by ID or label')
    p_get.add_argument('role_id', help='Role ID or label')

    p_list_perms = sub.add_parser('list-permissions', help='List permissions for a custom role')
    p_list_perms.add_argument('role_id', help='Role ID or label')

    p_get_perm = sub.add_parser('get-permission', help='Get a specific permission for a custom role')
    p_get_perm.add_argument('role_id', help='Role ID or label')
    p_get_perm.add_argument('permission_type', help='Permission type, e.g. okta.users.manage')

    p_list_assignees = sub.add_parser(
        'list-assignees', help='List all users with any role assignment'
    )
    p_list_assignees.add_argument('--limit', type=int, help='Maximum number of results')

    p_list_rs = sub.add_parser('list-resource-sets', help='List all resource sets')
    p_list_rs.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_rs = sub.add_parser('get-resource-set', help='Get a resource set by ID or label')
    p_get_rs.add_argument('resource_set_id', help='Resource set ID or label')

    p_list_bindings = sub.add_parser(
        'list-bindings', help='List all role bindings for a resource set'
    )
    p_list_bindings.add_argument('resource_set_id', help='Resource set ID or label')
    p_list_bindings.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_binding = sub.add_parser(
        'get-binding', help='Get a specific role binding for a resource set'
    )
    p_get_binding.add_argument('resource_set_id', help='Resource set ID or label')
    p_get_binding.add_argument('role_id', help='Role ID or label')

    p_list_binding_members = sub.add_parser(
        'list-binding-members', help='List members of a role resource set binding'
    )
    p_list_binding_members.add_argument('resource_set_id', help='Resource set ID or label')
    p_list_binding_members.add_argument('role_id', help='Role ID or label')
    p_list_binding_members.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_binding_member = sub.add_parser(
        'get-binding-member', help='Get a specific member of a role resource set binding'
    )
    p_get_binding_member.add_argument('resource_set_id', help='Resource set ID or label')
    p_get_binding_member.add_argument('role_id', help='Role ID or label')
    p_get_binding_member.add_argument('member_id', help='Binding member ID')

    p_list_resources = sub.add_parser(
        'list-resources', help='List all resources in a resource set'
    )
    p_list_resources.add_argument('resource_set_id', help='Resource set ID or label')
    p_list_resources.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_resource = sub.add_parser(
        'get-resource', help='Get a specific resource in a resource set'
    )
    p_get_resource.add_argument('resource_set_id', help='Resource set ID or label')
    p_get_resource.add_argument('resource_id', help='Resource ID')

    p_list_bundles = sub.add_parser(
        'list-bundles', help='List all governance bundles (Limited GA)'
    )
    p_list_bundles.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_bundle = sub.add_parser('get-bundle', help='Get a governance bundle by ID (Limited GA)')
    p_get_bundle.add_argument('bundle_id', help='Governance bundle ID')

    p_list_bundle_entitlements = sub.add_parser(
        'list-bundle-entitlements', help='List entitlements for a governance bundle (Limited GA)'
    )
    p_list_bundle_entitlements.add_argument('bundle_id', help='Governance bundle ID')
    p_list_bundle_entitlements.add_argument('--limit', type=int, help='Maximum number of results')

    p_list_bundle_entitlement_values = sub.add_parser(
        'list-bundle-entitlement-values',
        help='List values for a governance bundle entitlement (Limited GA)',
    )
    p_list_bundle_entitlement_values.add_argument('bundle_id', help='Governance bundle ID')
    p_list_bundle_entitlement_values.add_argument('entitlement_id', help='Bundle entitlement ID')
    p_list_bundle_entitlement_values.add_argument(
        '--limit', type=int, help='Maximum number of results'
    )

    sub.add_parser(
        'get-opt-in-status', help='Get the Admin Console governance opt-in status (Limited GA)'
    )

    p_list_role_subs = sub.add_parser(
        'list-role-subscriptions', help='List notification subscriptions for a role'
    )
    p_list_role_subs.add_argument('role_ref', help='Role type (e.g. SUPER_ADMIN) or custom role ID')

    p_get_role_sub = sub.add_parser(
        'get-role-subscription', help='Get a specific notification subscription for a role'
    )
    p_get_role_sub.add_argument('role_ref', help='Role type (e.g. SUPER_ADMIN) or custom role ID')
    p_get_role_sub.add_argument('notification_type', help='Notification type')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'list':
            result = cmd_list(session, base_url, args)
        elif args.command == 'get':
            result = cmd_get(session, base_url, args)
        elif args.command == 'list-permissions':
            result = cmd_list_permissions(session, base_url, args)
        elif args.command == 'get-permission':
            result = cmd_get_permission(session, base_url, args)
        elif args.command == 'list-assignees':
            result = cmd_list_assignees(session, base_url, args)
        elif args.command == 'list-resource-sets':
            result = cmd_list_resource_sets(session, base_url, args)
        elif args.command == 'get-resource-set':
            result = cmd_get_resource_set(session, base_url, args)
        elif args.command == 'list-bindings':
            result = cmd_list_bindings(session, base_url, args)
        elif args.command == 'get-binding':
            result = cmd_get_binding(session, base_url, args)
        elif args.command == 'list-binding-members':
            result = cmd_list_binding_members(session, base_url, args)
        elif args.command == 'get-binding-member':
            result = cmd_get_binding_member(session, base_url, args)
        elif args.command == 'list-resources':
            result = cmd_list_resources(session, base_url, args)
        elif args.command == 'get-resource':
            result = cmd_get_resource(session, base_url, args)
        elif args.command == 'list-bundles':
            result = cmd_list_bundles(session, base_url, args)
        elif args.command == 'get-bundle':
            result = cmd_get_bundle(session, base_url, args)
        elif args.command == 'list-bundle-entitlements':
            result = cmd_list_bundle_entitlements(session, base_url, args)
        elif args.command == 'list-bundle-entitlement-values':
            result = cmd_list_bundle_entitlement_values(session, base_url, args)
        elif args.command == 'get-opt-in-status':
            result = cmd_get_opt_in_status(session, base_url, args)
        elif args.command == 'list-role-subscriptions':
            result = cmd_list_role_subscriptions(session, base_url, args)
        elif args.command == 'get-role-subscription':
            result = cmd_get_role_subscription(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
