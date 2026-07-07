#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta applications via the Okta API."""
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
    return paginated_get(session, f'{base_url}/api/v1/apps', params, limit=args.limit)


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}')


def cmd_get_users(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/users')


def cmd_get_groups(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/groups')


def cmd_get_group(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/groups/{args.group_id}')


def cmd_get_connection(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/connections/default')


def cmd_get_connection_jwks(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/connections/default/jwks')


def cmd_list_csrs(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/credentials/csrs')


def cmd_get_csr(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/credentials/csrs/{args.csr_id}')


def cmd_list_jwks(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/credentials/jwks')


def cmd_get_jwk(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/credentials/jwks/{args.key_id}')


def cmd_list_keys(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/credentials/keys')


def cmd_get_key(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/credentials/keys/{args.key_id}')


def cmd_list_secrets(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/credentials/secrets')


def cmd_get_secret(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/credentials/secrets/{args.secret_id}')


def cmd_list_cwo_connections(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/cwo/connections', limit=args.limit)


def cmd_get_cwo_connection(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/cwo/connections/{args.connection_id}')


def cmd_list_features(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/features')


def cmd_get_feature(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/features/{args.feature_name}')


def cmd_list_federated_claims(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/federated-claims')


def cmd_get_federated_claim(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/federated-claims/{args.claim_id}')


def cmd_list_grants(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/grants')


def cmd_get_grant(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/grants/{args.grant_id}')


def cmd_list_group_push_mappings(session, base_url, args):
    return paginated_get(
        session, f'{base_url}/api/v1/apps/{args.id}/group-push/mappings', limit=args.limit
    )


def cmd_get_group_push_mapping(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/group-push/mappings/{args.mapping_id}')


def cmd_list_interclient_allowed_apps(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/interclient-allowed-apps')


def cmd_list_interclient_target_apps(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/interclient-target-apps')


def cmd_get_saml_metadata(session, base_url, args):
    resp = session.get(
        f'{base_url}/api/v1/apps/{args.id}/sso/saml/metadata',
        params={'kid': args.kid},
        headers={'Accept': 'text/xml'},
    )
    resp.raise_for_status()
    return resp.text


def cmd_list_tokens(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/tokens', limit=args.limit)


def cmd_get_token(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/tokens/{args.token_id}')


def cmd_get_user(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/users/{args.user_id}')


def _add_limit_arg(parser):
    parser.add_argument('--limit', type=int, help='Maximum number of results')


def main():
    parser = argparse.ArgumentParser(description='Read Okta applications')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List applications')
    p_list.add_argument('--filter', help='Filter expression (e.g. status eq "ACTIVE")')
    _add_limit_arg(p_list)

    p_get = sub.add_parser('get', help='Get an application by ID')
    p_get.add_argument('id', help='Application ID')

    p_users = sub.add_parser('get-users', help='List users assigned to an application')
    p_users.add_argument('id', help='Application ID')

    p_groups = sub.add_parser('get-groups', help='List groups assigned to an application')
    p_groups.add_argument('id', help='Application ID')

    p_group = sub.add_parser('get-group', help='Get a specific group assignment for an application')
    p_group.add_argument('id', help='Application ID')
    p_group.add_argument('group_id', help='Group ID')

    p_conn = sub.add_parser('get-connection', help='Get the default provisioning connection for an application')
    p_conn.add_argument('id', help='Application ID')

    p_conn_jwks = sub.add_parser(
        'get-connection-jwks', help='Get the JWKS for the default provisioning connection'
    )
    p_conn_jwks.add_argument('id', help='Application ID')

    p_list_csrs = sub.add_parser('list-csrs', help='List certificate signing requests for an application')
    p_list_csrs.add_argument('id', help='Application ID')

    p_get_csr = sub.add_parser('get-csr', help='Get a certificate signing request for an application')
    p_get_csr.add_argument('id', help='Application ID')
    p_get_csr.add_argument('csr_id', help='CSR ID')

    p_list_jwks = sub.add_parser('list-jwks', help="List an application's OAuth 2.0 client JWKs")
    p_list_jwks.add_argument('id', help='Application ID')

    p_get_jwk = sub.add_parser('get-jwk', help="Get a specific OAuth 2.0 client JWK")
    p_get_jwk.add_argument('id', help='Application ID')
    p_get_jwk.add_argument('key_id', help='Key ID')

    p_list_keys = sub.add_parser('list-keys', help="List an application's key credentials")
    p_list_keys.add_argument('id', help='Application ID')

    p_get_key = sub.add_parser('get-key', help='Get a specific key credential')
    p_get_key.add_argument('id', help='Application ID')
    p_get_key.add_argument('key_id', help='Key ID')

    p_list_secrets = sub.add_parser('list-secrets', help="List an application's OAuth 2.0 client secrets")
    p_list_secrets.add_argument('id', help='Application ID')

    p_get_secret = sub.add_parser('get-secret', help='Get a specific OAuth 2.0 client secret')
    p_get_secret.add_argument('id', help='Application ID')
    p_get_secret.add_argument('secret_id', help='Secret ID')

    p_list_cwo = sub.add_parser(
        'list-cwo-connections', help='List Cross App Access connections for an application (EA)'
    )
    p_list_cwo.add_argument('id', help='Application ID')
    _add_limit_arg(p_list_cwo)

    p_get_cwo = sub.add_parser('get-cwo-connection', help='Get a specific Cross App Access connection (EA)')
    p_get_cwo.add_argument('id', help='Application ID')
    p_get_cwo.add_argument('connection_id', help='Connection ID')

    p_list_features = sub.add_parser('list-features', help='List features enabled for an application')
    p_list_features.add_argument('id', help='Application ID')

    p_get_feature = sub.add_parser('get-feature', help='Get a specific application feature')
    p_get_feature.add_argument('id', help='Application ID')
    p_get_feature.add_argument('feature_name', help='Feature name')

    p_list_claims = sub.add_parser(
        'list-federated-claims', help='List configured federated claims for an application'
    )
    p_list_claims.add_argument('id', help='Application ID')

    p_get_claim = sub.add_parser('get-federated-claim', help='Get a specific federated claim')
    p_get_claim.add_argument('id', help='Application ID')
    p_get_claim.add_argument('claim_id', help='Federated claim ID')

    p_list_grants = sub.add_parser('list-grants', help='List scope consent grants for an application')
    p_list_grants.add_argument('id', help='Application ID')

    p_get_grant = sub.add_parser('get-grant', help='Get a specific scope consent grant')
    p_get_grant.add_argument('id', help='Application ID')
    p_get_grant.add_argument('grant_id', help='Grant ID')

    p_list_gpm = sub.add_parser(
        'list-group-push-mappings', help='List group push mappings for an application'
    )
    p_list_gpm.add_argument('id', help='Application ID')
    _add_limit_arg(p_list_gpm)

    p_get_gpm = sub.add_parser('get-group-push-mapping', help='Get a specific group push mapping')
    p_get_gpm.add_argument('id', help='Application ID')
    p_get_gpm.add_argument('mapping_id', help='Mapping ID')

    p_list_ica = sub.add_parser(
        'list-interclient-allowed-apps', help='List apps allowed to call this application (EA)'
    )
    p_list_ica.add_argument('id', help='Application ID')

    p_list_ict = sub.add_parser(
        'list-interclient-target-apps', help='List target apps this application can call (EA)'
    )
    p_list_ict.add_argument('id', help='Application ID')

    p_saml = sub.add_parser('get-saml-metadata', help='Get the SAML metadata (XML) for an application')
    p_saml.add_argument('id', help='Application ID')
    p_saml.add_argument('--kid', required=True, help='Key ID of the signing certificate')

    p_list_tokens = sub.add_parser('list-tokens', help='List OAuth 2.0 refresh tokens for an application')
    p_list_tokens.add_argument('id', help='Application ID')
    _add_limit_arg(p_list_tokens)

    p_get_token = sub.add_parser('get-token', help='Get a specific OAuth 2.0 refresh token')
    p_get_token.add_argument('id', help='Application ID')
    p_get_token.add_argument('token_id', help='Token ID')

    p_get_user = sub.add_parser('get-user', help='Get a specific user assignment for an application')
    p_get_user.add_argument('id', help='Application ID')
    p_get_user.add_argument('user_id', help='User ID')

    args = parser.parse_args()
    session, base_url = get_session()

    # command -> (handler, is_raw_output); is_raw_output=True prints the
    # result as-is instead of JSON-encoding it (get-saml-metadata returns XML)
    commands = {
        'list': (cmd_list, False),
        'get': (cmd_get, False),
        'get-users': (cmd_get_users, False),
        'get-groups': (cmd_get_groups, False),
        'get-group': (cmd_get_group, False),
        'get-connection': (cmd_get_connection, False),
        'get-connection-jwks': (cmd_get_connection_jwks, False),
        'list-csrs': (cmd_list_csrs, False),
        'get-csr': (cmd_get_csr, False),
        'list-jwks': (cmd_list_jwks, False),
        'get-jwk': (cmd_get_jwk, False),
        'list-keys': (cmd_list_keys, False),
        'get-key': (cmd_get_key, False),
        'list-secrets': (cmd_list_secrets, False),
        'get-secret': (cmd_get_secret, False),
        'list-cwo-connections': (cmd_list_cwo_connections, False),
        'get-cwo-connection': (cmd_get_cwo_connection, False),
        'list-features': (cmd_list_features, False),
        'get-feature': (cmd_get_feature, False),
        'list-federated-claims': (cmd_list_federated_claims, False),
        'get-federated-claim': (cmd_get_federated_claim, False),
        'list-grants': (cmd_list_grants, False),
        'get-grant': (cmd_get_grant, False),
        'list-group-push-mappings': (cmd_list_group_push_mappings, False),
        'get-group-push-mapping': (cmd_get_group_push_mapping, False),
        'list-interclient-allowed-apps': (cmd_list_interclient_allowed_apps, False),
        'list-interclient-target-apps': (cmd_list_interclient_target_apps, False),
        'get-saml-metadata': (cmd_get_saml_metadata, True),
        'list-tokens': (cmd_list_tokens, False),
        'get-token': (cmd_get_token, False),
        'get-user': (cmd_get_user, False),
    }

    try:
        handler, is_raw_output = commands[args.command]
        result = handler(session, base_url, args)
        if is_raw_output:
            print(result)
        else:
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
