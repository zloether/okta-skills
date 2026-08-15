#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta authorization servers via the Okta API."""
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
    return paginated_get(session, f'{base_url}/api/v1/authorizationServers', params, limit=args.limit)


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/authorizationServers/{args.id}')


def cmd_list_associated_servers(session, base_url, args):
    params = {}
    if args.trusted:
        params['trusted'] = args.trusted
    if args.q:
        params['q'] = args.q
    return paginated_get(
        session,
        f'{base_url}/api/v1/authorizationServers/{args.id}/associatedServers',
        params,
        limit=args.limit,
    )


def cmd_list_claims(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/authorizationServers/{args.id}/claims', limit=args.limit)


def cmd_get_claim(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/authorizationServers/{args.id}/claims/{args.claim_id}'
    )


def cmd_list_clients(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/authorizationServers/{args.id}/clients', limit=args.limit)


def cmd_list_tokens(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(
        session,
        f'{base_url}/api/v1/authorizationServers/{args.id}/clients/{args.client_id}/tokens',
        params,
        limit=args.limit,
    )


def cmd_get_token(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(
        session,
        f'{base_url}/api/v1/authorizationServers/{args.id}/clients/{args.client_id}/tokens/{args.token_id}',
        params,
    )


def cmd_list_keys(session, base_url, args):
    return paginated_get(
        session, f'{base_url}/api/v1/authorizationServers/{args.id}/credentials/keys', limit=args.limit
    )


def cmd_get_key(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/authorizationServers/{args.id}/credentials/keys/{args.key_id}'
    )


def cmd_list_policies(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/authorizationServers/{args.id}/policies', limit=args.limit)


def cmd_get_policy(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/authorizationServers/{args.id}/policies/{args.policy_id}'
    )


def cmd_list_policy_rules(session, base_url, args):
    return paginated_get(
        session,
        f'{base_url}/api/v1/authorizationServers/{args.id}/policies/{args.policy_id}/rules',
        limit=args.limit,
    )


def cmd_get_policy_rule(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/authorizationServers/{args.id}/policies/{args.policy_id}/rules/{args.rule_id}',
    )


def cmd_list_resource_server_keys(session, base_url, args):
    return paginated_get(
        session,
        f'{base_url}/api/v1/authorizationServers/{args.id}/resourceservercredentials/keys',
        limit=args.limit,
    )


def cmd_get_resource_server_key(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/authorizationServers/{args.id}/resourceservercredentials/keys/{args.key_id}',
    )


def cmd_list_scopes(session, base_url, args):
    params = {}
    if args.q:
        params['q'] = args.q
    if args.filter:
        params['filter'] = args.filter
    return paginated_get(
        session,
        f'{base_url}/api/v1/authorizationServers/{args.id}/scopes',
        params,
        limit=args.limit,
    )


def cmd_get_scope(session, base_url, args):
    return get_resource(
        session, f'{base_url}/api/v1/authorizationServers/{args.id}/scopes/{args.scope_id}'
    )


def main():
    parser = argparse.ArgumentParser(description='Read Okta authorization servers')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List authorization servers')
    p_list.add_argument('--q', help='Search query (matches name or audience)')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get an authorization server by ID')
    p_get.add_argument('id', help='Authorization server ID')

    p_list_assoc = sub.add_parser(
        'list-associated-servers', help='List authorization servers trusted by or trusting this one'
    )
    p_list_assoc.add_argument('id', help='Authorization server ID')
    p_list_assoc.add_argument('--trusted', choices=['true', 'false'], help='Filter by trusted status')
    p_list_assoc.add_argument('--q', help='Search query (matches name or audience)')
    p_list_assoc.add_argument('--limit', type=int, help='Maximum number of results')

    p_list_claims = sub.add_parser('list-claims', help='List custom token claims for an authorization server')
    p_list_claims.add_argument('id', help='Authorization server ID')
    p_list_claims.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_claim = sub.add_parser('get-claim', help='Get a specific custom claim')
    p_get_claim.add_argument('id', help='Authorization server ID')
    p_get_claim.add_argument('claim_id', help='Claim ID')

    p_list_clients = sub.add_parser(
        'list-clients', help='List OAuth clients registered with an authorization server'
    )
    p_list_clients.add_argument('id', help='Authorization server ID')
    p_list_clients.add_argument('--limit', type=int, help='Maximum number of results')

    p_list_tokens = sub.add_parser(
        'list-tokens', help='List refresh tokens for a client on an authorization server'
    )
    p_list_tokens.add_argument('id', help='Authorization server ID')
    p_list_tokens.add_argument('client_id', help='OAuth client ID')
    p_list_tokens.add_argument('--expand', choices=['scope'], help='Embed scope details in the response')
    p_list_tokens.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_token = sub.add_parser('get-token', help='Get a specific refresh token')
    p_get_token.add_argument('id', help='Authorization server ID')
    p_get_token.add_argument('client_id', help='OAuth client ID')
    p_get_token.add_argument('token_id', help='Token ID')
    p_get_token.add_argument('--expand', choices=['scope'], help='Embed scope details in the response')

    p_list_keys = sub.add_parser('list-keys', help='List signing keys for an authorization server')
    p_list_keys.add_argument('id', help='Authorization server ID')
    p_list_keys.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_key = sub.add_parser('get-key', help='Get a specific signing key')
    p_get_key.add_argument('id', help='Authorization server ID')
    p_get_key.add_argument('key_id', help='Key ID (kid)')

    p_list_policies = sub.add_parser('list-policies', help='List policies for an authorization server')
    p_list_policies.add_argument('id', help='Authorization server ID')
    p_list_policies.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_policy = sub.add_parser('get-policy', help='Get a specific authorization server policy')
    p_get_policy.add_argument('id', help='Authorization server ID')
    p_get_policy.add_argument('policy_id', help='Policy ID')

    p_list_rules = sub.add_parser('list-policy-rules', help='List rules for an authorization server policy')
    p_list_rules.add_argument('id', help='Authorization server ID')
    p_list_rules.add_argument('policy_id', help='Policy ID')
    p_list_rules.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_rule = sub.add_parser('get-policy-rule', help='Get a specific authorization server policy rule')
    p_get_rule.add_argument('id', help='Authorization server ID')
    p_get_rule.add_argument('policy_id', help='Policy ID')
    p_get_rule.add_argument('rule_id', help='Rule ID')

    p_list_rsk = sub.add_parser(
        'list-resource-server-keys', help='List resource server public JWKs for an authorization server'
    )
    p_list_rsk.add_argument('id', help='Authorization server ID')
    p_list_rsk.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_rsk = sub.add_parser('get-resource-server-key', help='Get a specific resource server public JWK')
    p_get_rsk.add_argument('id', help='Authorization server ID')
    p_get_rsk.add_argument('key_id', help='Key ID')

    p_list_scopes = sub.add_parser('list-scopes', help='List custom scopes for an authorization server')
    p_list_scopes.add_argument('id', help='Authorization server ID')
    p_list_scopes.add_argument('--q', help='Search query (matches scope name)')
    p_list_scopes.add_argument('--filter', help='Filter expression')
    p_list_scopes.add_argument('--limit', type=int, help='Maximum number of results')

    p_get_scope = sub.add_parser('get-scope', help='Get a specific custom scope')
    p_get_scope.add_argument('id', help='Authorization server ID')
    p_get_scope.add_argument('scope_id', help='Scope ID')

    args = parser.parse_args()
    session, base_url = get_session()

    commands = {
        'list': cmd_list,
        'get': cmd_get,
        'list-associated-servers': cmd_list_associated_servers,
        'list-claims': cmd_list_claims,
        'get-claim': cmd_get_claim,
        'list-clients': cmd_list_clients,
        'list-tokens': cmd_list_tokens,
        'get-token': cmd_get_token,
        'list-keys': cmd_list_keys,
        'get-key': cmd_get_key,
        'list-policies': cmd_list_policies,
        'get-policy': cmd_get_policy,
        'list-policy-rules': cmd_list_policy_rules,
        'get-policy-rule': cmd_get_policy_rule,
        'list-resource-server-keys': cmd_list_resource_server_keys,
        'get-resource-server-key': cmd_get_resource_server_key,
        'list-scopes': cmd_list_scopes,
        'get-scope': cmd_get_scope,
    }

    try:
        result = commands[args.command](session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
