#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta custom admin roles, resource sets, and governance bundles via the Okta API."""
import argparse
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run
from okta_client import get_resource, paginated_get_wrapped


def cmd_list(session, base_url, args):
    return paginated_get_wrapped(session, f'{base_url}/api/v1/iam/roles', 'roles', limit=args.limit)


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/iam/roles/{quote(args.role_id, safe="")}')


def cmd_list_permissions(session, base_url, args):
    result = get_resource(
        session, f'{base_url}/api/v1/iam/roles/{quote(args.role_id, safe="")}/permissions'
    )
    return result.get('permissions', [])


def cmd_get_permission(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/iam/roles/{quote(args.role_id, safe="")}'
        f'/permissions/{quote(args.permission_type, safe="")}',
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
    return get_resource(
        session, f'{base_url}/api/v1/iam/resource-sets/{quote(args.resource_set_id, safe="")}'
    )


def cmd_list_bindings(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{quote(args.resource_set_id, safe="")}/bindings',
        'roles',
        limit=args.limit,
    )


def cmd_get_binding(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{quote(args.resource_set_id, safe="")}'
        f'/bindings/{quote(args.role_id, safe="")}',
    )


def cmd_list_binding_members(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{quote(args.resource_set_id, safe="")}'
        f'/bindings/{quote(args.role_id, safe="")}/members',
        'members',
        limit=args.limit,
    )


def cmd_get_binding_member(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{quote(args.resource_set_id, safe="")}/bindings/'
        f'{quote(args.role_id, safe="")}/members/{quote(args.member_id, safe="")}',
    )


def cmd_list_resources(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{quote(args.resource_set_id, safe="")}/resources',
        'resources',
        limit=args.limit,
    )


def cmd_get_resource(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/iam/resource-sets/{quote(args.resource_set_id, safe="")}'
        f'/resources/{quote(args.resource_id, safe="")}',
    )


def cmd_list_bundles(session, base_url, args):
    return paginated_get_wrapped(
        session, f'{base_url}/api/v1/iam/governance/bundles', 'bundles', limit=args.limit
    )


def cmd_get_bundle(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/iam/governance/bundles/{quote(args.bundle_id, safe="")}'
    )


def cmd_list_bundle_entitlements(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/governance/bundles/{quote(args.bundle_id, safe="")}/entitlements',
        'entitlements',
        limit=args.limit,
    )


def cmd_list_bundle_entitlement_values(session, base_url, args):
    return paginated_get_wrapped(
        session,
        f'{base_url}/api/v1/iam/governance/bundles/{quote(args.bundle_id, safe="")}/'
        f'entitlements/{quote(args.entitlement_id, safe="")}/values',
        'entitlementValues',
        limit=args.limit,
    )


def cmd_get_opt_in_status(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/iam/governance/optIn')


def cmd_list_role_subscriptions(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/roles/{quote(args.role_ref, safe="")}/subscriptions'
    )


def cmd_get_role_subscription(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/roles/{quote(args.role_ref, safe="")}'
        f'/subscriptions/{quote(args.notification_type, safe="")}',
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

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
        'list-permissions': cmd_list_permissions,
        'get-permission': cmd_get_permission,
        'list-assignees': cmd_list_assignees,
        'list-resource-sets': cmd_list_resource_sets,
        'get-resource-set': cmd_get_resource_set,
        'list-bindings': cmd_list_bindings,
        'get-binding': cmd_get_binding,
        'list-binding-members': cmd_list_binding_members,
        'get-binding-member': cmd_get_binding_member,
        'list-resources': cmd_list_resources,
        'get-resource': cmd_get_resource,
        'list-bundles': cmd_list_bundles,
        'get-bundle': cmd_get_bundle,
        'list-bundle-entitlements': cmd_list_bundle_entitlements,
        'list-bundle-entitlement-values': cmd_list_bundle_entitlement_values,
        'get-opt-in-status': cmd_get_opt_in_status,
        'list-role-subscriptions': cmd_list_role_subscriptions,
        'get-role-subscription': cmd_get_role_subscription,
    })


if __name__ == '__main__':
    main()
