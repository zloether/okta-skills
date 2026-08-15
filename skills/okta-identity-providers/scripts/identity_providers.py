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
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session, get_resource, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.q:
        params['q'] = args.q
    if args.type:
        params['type'] = args.type
    return paginated_get(session, f'{base_url}/api/v1/idps', params, limit=args.limit)


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/idps/{args.idp_id}')


def cmd_list_keys(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/idps/credentials/keys', limit=args.limit)


def cmd_get_key(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/idps/credentials/keys/{args.kid}')


def cmd_list_csrs(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/idps/{args.idp_id}/credentials/csrs')


def cmd_get_csr(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/idps/{args.idp_id}/credentials/csrs/{args.idp_csr_id}'
    )


def cmd_list_signing_keys(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/idps/{args.idp_id}/credentials/keys')


def cmd_get_active_signing_key(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/idps/{args.idp_id}/credentials/keys/active', allow_empty=True
    )


def cmd_get_signing_key(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/idps/{args.idp_id}/credentials/keys/{args.kid}'
    )


def cmd_list_users(session, base_url, args):
    params = {}
    if args.q:
        params['q'] = args.q
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(
        session, f'{base_url}/api/v1/idps/{args.idp_id}/users', params, limit=args.limit
    )


def cmd_get_user(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/idps/{args.idp_id}/users/{args.user_id}'
    )


def cmd_list_tokens(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/idps/{args.idp_id}/users/{args.user_id}/credentials/tokens'
    )


def main():
    parser = argparse.ArgumentParser(description='Read Okta identity providers')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List identity providers')
    p_list.add_argument('--q', help='Search IdP name for matching value')
    p_list.add_argument('--type', help='Filter by IdP type, e.g. SAML2, OIDC, GOOGLE')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get an identity provider by ID')
    p_get.add_argument('idp_id', help='IdP ID')

    p_list_keys = sub.add_parser(
        'list-keys', help='List all IdP key credentials (org-wide key store, not tied to one IdP)'
    )
    p_list_keys.add_argument('--limit', type=int, help='Maximum number of results')

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

    p_get_user = sub.add_parser('get-user', help='Get a specific user linked to an IdP')
    p_get_user.add_argument('idp_id', help='IdP ID')
    p_get_user.add_argument('user_id', help='IdP-linked user ID')

    p_list_tokens = sub.add_parser(
        'list-tokens', help='List social auth tokens for an IdP-linked user (OIDC/social IdPs only)'
    )
    p_list_tokens.add_argument('idp_id', help='IdP ID')
    p_list_tokens.add_argument('user_id', help='IdP-linked user ID')

    args = parser.parse_args()
    session, base_url = get_session()

    commands = {
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
    }

    try:
        result = commands[args.command](session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
