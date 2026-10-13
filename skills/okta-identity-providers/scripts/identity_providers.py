#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta identity providers (federation/social IdPs) via the Okta API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import add_page_size, run, with_page_size
from okta_client import get_resource, paginated_get


def cmd_list(session, base_url, args):
    params = {}
    if args.q:
        params['q'] = args.q
    if args.type:
        params['type'] = args.type
    with_page_size(params, args)
    return paginated_get(session, f'{base_url}/api/v1/idps', params, limit=args.limit)


def cmd_get(session, base_url, args):
    return get_resource(session, '{base}/api/v1/idps/{idp_id}', path_params={'base': base_url, 'idp_id': args.idp_id})


def cmd_list_keys(session, base_url, args):
    return paginated_get(
        session, f'{base_url}/api/v1/idps/credentials/keys', with_page_size({}, args), limit=args.limit
    )


def cmd_get_key(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/idps/credentials/keys/{kid}',
        path_params={'base': base_url, 'kid': args.kid},
    )


def cmd_list_csrs(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/idps/{idp_id}/credentials/csrs',
        path_params={'base': base_url, 'idp_id': args.idp_id},
    )


def cmd_get_csr(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/idps/{idp_id}/credentials/csrs/{idp_csr_id}',
        path_params={'base': base_url, 'idp_id': args.idp_id, 'idp_csr_id': args.idp_csr_id},
    )


def cmd_list_signing_keys(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/idps/{idp_id}/credentials/keys',
        path_params={'base': base_url, 'idp_id': args.idp_id},
    )


def cmd_get_active_signing_key(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/idps/{idp_id}/credentials/keys/active', allow_empty=True,
        path_params={'base': base_url, 'idp_id': args.idp_id},
    )


def cmd_get_signing_key(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/idps/{idp_id}/credentials/keys/{kid}',
        path_params={'base': base_url, 'idp_id': args.idp_id, 'kid': args.kid},
    )


def cmd_list_users(session, base_url, args):
    params = {}
    if args.q:
        params['q'] = args.q
    if args.expand:
        params['expand'] = args.expand
    with_page_size(params, args)
    return paginated_get(
        session, '{base}/api/v1/idps/{idp_id}/users', params, limit=args.limit,
        path_params={'base': base_url, 'idp_id': args.idp_id},
    )


def cmd_get_user(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/idps/{idp_id}/users/{user_id}',
        path_params={'base': base_url, 'idp_id': args.idp_id, 'user_id': args.user_id},
    )


def cmd_list_tokens(session, base_url, args):
    return get_resource(
        session, '{base}/api/v1/idps/{idp_id}/users/{user_id}/credentials/tokens',
        path_params={'base': base_url, 'idp_id': args.idp_id, 'user_id': args.user_id},
    )


def main():
    parser = argparse.ArgumentParser(description='Read Okta identity providers')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List identity providers')
    p_list.add_argument('--q', help='Search IdP name for matching value')
    p_list.add_argument('--type', help='Filter by IdP type, e.g. SAML2, OIDC, GOOGLE')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')
    add_page_size(p_list)

    p_get = sub.add_parser('get', help='Get an identity provider by ID')
    p_get.add_argument('idp_id', help='IdP ID')

    p_list_keys = sub.add_parser(
        'list-keys', help='List all IdP key credentials (org-wide key store, not tied to one IdP)'
    )
    p_list_keys.add_argument('--limit', type=int, help='Maximum number of results')
    add_page_size(p_list_keys)

    p_get_key = sub.add_parser(
        'get-key', help='Get an IdP key credential by kid (org-wide key store)'
    )
    p_get_key.add_argument('kid', help='Key credential ID')

    p_list_csrs = sub.add_parser('list-csrs', help='List certificate signing requests for an IdP')
    p_list_csrs.add_argument('idp_id', help='IdP ID')

    p_get_csr = sub.add_parser('get-csr', help='Get a specific CSR for an IdP')
    p_get_csr.add_argument('idp_id', help='IdP ID')
    p_get_csr.add_argument('idp_csr_id', help='CSR ID')

    p_list_signing_keys = sub.add_parser(
        'list-signing-keys', help='List signing key credentials for a specific IdP'
    )
    p_list_signing_keys.add_argument('idp_id', help='IdP ID')

    p_get_active_signing_key = sub.add_parser(
        'get-active-signing-key', help="List the active signing key credential for a specific IdP"
    )
    p_get_active_signing_key.add_argument('idp_id', help='IdP ID')

    p_get_signing_key = sub.add_parser(
        'get-signing-key', help='Get a specific signing key credential for an IdP by kid'
    )
    p_get_signing_key.add_argument('idp_id', help='IdP ID')
    p_get_signing_key.add_argument('kid', help='Signing key credential ID')

    p_list_users = sub.add_parser('list-users', help='List users linked to an IdP')
    p_list_users.add_argument('idp_id', help='IdP ID')
    p_list_users.add_argument('--q', help='Search linked users for matching value')
    p_list_users.add_argument('--expand', help='Expand user data, e.g. "user"')
    p_list_users.add_argument('--limit', type=int, help='Maximum number of results')
    add_page_size(p_list_users)

    p_get_user = sub.add_parser('get-user', help='Get a specific user linked to an IdP')
    p_get_user.add_argument('idp_id', help='IdP ID')
    p_get_user.add_argument('user_id', help='IdP-linked user ID')

    p_list_tokens = sub.add_parser(
        'list-tokens', help='List social auth tokens for an IdP-linked user (OIDC/social IdPs only)'
    )
    p_list_tokens.add_argument('idp_id', help='IdP ID')
    p_list_tokens.add_argument('user_id', help='IdP-linked user ID')

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
        'list-keys': cmd_list_keys,
        'get-key': cmd_get_key,
        'list-csrs': cmd_list_csrs,
        'get-csr': cmd_get_csr,
        'list-signing-keys': cmd_list_signing_keys,
        'get-active-signing-key': cmd_get_active_signing_key,
        'get-signing-key': cmd_get_signing_key,
        'list-users': cmd_list_users,
        'get-user': cmd_get_user,
        'list-tokens': cmd_list_tokens,
    })


if __name__ == '__main__':
    main()
