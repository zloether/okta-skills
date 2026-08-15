#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
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
    if args.q:
        params['q'] = args.q
    if args.expand:
        params['expand'] = args.expand
    if args.use_optimization:
        params['useOptimization'] = 'true'
    if args.always_include_vpn_settings:
        params['alwaysIncludeVpnSettings'] = 'true'
    if args.include_non_deleted:
        params['includeNonDeleted'] = 'true'
    return paginated_get(session, f'{base_url}/api/v1/apps', params, limit=args.limit)


def cmd_get(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}', params=params)


def cmd_get_users(session, base_url, args):
    params = {}
    if args.q:
        params['q'] = args.q
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/users', params, limit=args.limit)


def cmd_get_groups(session, base_url, args):
    params = {}
    if args.q:
        params['q'] = args.q
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/groups', params, limit=args.limit)


def cmd_get_group(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/groups/{args.group_id}', params=params)


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
    params = {}
    if args.status:
        params['status'] = args.status
    if args.requesting_app_id:
        params['requestingAppId'] = args.requesting_app_id
    if args.resource_app_id:
        params['resourceAppId'] = args.resource_app_id
    if args.active_apps_only:
        params['activeAppsOnly'] = 'true'
    if args.requesting_app_name:
        params['requestingAppName'] = args.requesting_app_name
    if args.resource_app_name:
        params['resourceAppName'] = args.resource_app_name
    return paginated_get(
        session, f'{base_url}/api/v1/apps/{args.id}/cwo/connections', params, limit=args.limit
    )


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
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/grants', params)


def cmd_get_grant(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/grants/{args.grant_id}', params=params)


def cmd_list_group_push_mappings(session, base_url, args):
    params = {}
    if args.last_updated:
        params['lastUpdated'] = args.last_updated
    if args.source_group_id:
        params['sourceGroupId'] = args.source_group_id
    if args.status:
        params['status'] = args.status
    return paginated_get(
        session, f'{base_url}/api/v1/apps/{args.id}/group-push/mappings', params, limit=args.limit
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
    return {'metadata': resp.text}


def cmd_list_tokens(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return paginated_get(session, f'{base_url}/api/v1/apps/{args.id}/tokens', params, limit=args.limit)


def cmd_get_token(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/tokens/{args.token_id}', params=params)


def cmd_get_user(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(session, f'{base_url}/api/v1/apps/{args.id}/users/{args.user_id}', params=params)


def _add_limit_arg(parser):
    parser.add_argument('--limit', type=int, help='Maximum number of results')


def main():
    parser = argparse.ArgumentParser(description='Read Okta applications')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List applications')
    p_list_grp = p_list.add_mutually_exclusive_group()
    p_list_grp.add_argument('--filter', help='Filter expression (e.g. status eq "ACTIVE")')
    p_list_grp.add_argument('--q', help='Search apps by name prefix')
    p_list.add_argument('--expand', help='Expand response, e.g. user/{userId} (must be paired with --filter)')
    p_list.add_argument('--use-optimization', action='store_true', help='Use query optimization')
    p_list.add_argument(
        '--always-include-vpn-settings', action='store_true', help='Always include VPN settings in the response'
    )
    p_list.add_argument('--include-non-deleted', action='store_true', help='Include non-deleted applications')
    _add_limit_arg(p_list)

    p_get = sub.add_parser('get', help='Get an application by ID')
    p_get.add_argument('id', help='Application ID')
    p_get.add_argument('--expand', help='Expand response, e.g. user/{userId}')

    p_users = sub.add_parser('get-users', help='List users assigned to an application')
    p_users.add_argument('id', help='Application ID')
    p_users.add_argument('--q', help='Search assigned users by profile prefix')
    p_users.add_argument('--expand', help='Expand response')
    _add_limit_arg(p_users)

    p_groups = sub.add_parser('get-groups', help='List groups assigned to an application')
    p_groups.add_argument('id', help='Application ID')
    p_groups.add_argument('--q', help='Search assigned groups by name prefix')
    p_groups.add_argument('--expand', help='Expand response')
    _add_limit_arg(p_groups)

    p_group = sub.add_parser('get-group', help='Get a specific group assignment for an application')
    p_group.add_argument('id', help='Application ID')
    p_group.add_argument('group_id', help='Group ID')
    p_group.add_argument('--expand', help='Expand response')

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
    p_list_cwo.add_argument('--status', choices=['ACTIVE', 'INACTIVE'], help='Filter by connection status')
    p_list_cwo.add_argument('--requesting-app-id', help='Filter by requesting application ID')
    p_list_cwo.add_argument('--resource-app-id', help='Filter by resource application ID')
    p_list_cwo.add_argument('--active-apps-only', action='store_true', help='Only include active apps')
    p_list_cwo.add_argument('--requesting-app-name', help='Filter by requesting application name')
    p_list_cwo.add_argument('--resource-app-name', help='Filter by resource application name')
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
    p_list_grants.add_argument('--expand', help='Expand response to inline scope details')

    p_get_grant = sub.add_parser('get-grant', help='Get a specific scope consent grant')
    p_get_grant.add_argument('id', help='Application ID')
    p_get_grant.add_argument('grant_id', help='Grant ID')
    p_get_grant.add_argument('--expand', help='Expand response to inline scope details')

    p_list_gpm = sub.add_parser(
        'list-group-push-mappings', help='List group push mappings for an application'
    )
    p_list_gpm.add_argument('id', help='Application ID')
    p_list_gpm.add_argument('--last-updated', help='Filter by last updated timestamp expression')
    p_list_gpm.add_argument('--source-group-id', help='Filter by source group ID')
    p_list_gpm.add_argument('--status', help='Filter by mapping status')
    _add_limit_arg(p_list_gpm)

    p_get_gpm = sub.add_parser('get-group-push-mapping', help='Get a specific group push mapping')
    p_get_gpm.add_argument('id', help='Application ID')
    p_get_gpm.add_argument('mapping_id', help='Mapping ID')

    p_list_ica = sub.add_parser(
        'list-interclient-allowed-apps', help='List apps allowed to call this application (Limited GA)'
    )
    p_list_ica.add_argument('id', help='Application ID')

    p_list_ict = sub.add_parser(
        'list-interclient-target-apps', help='List target apps this application can call (Limited GA)'
    )
    p_list_ict.add_argument('id', help='Application ID')

    p_saml = sub.add_parser('get-saml-metadata', help='Get the SAML metadata (XML) for an application')
    p_saml.add_argument('id', help='Application ID')
    p_saml.add_argument('--kid', required=True, help='Key ID of the signing certificate')

    p_list_tokens = sub.add_parser('list-tokens', help='List OAuth 2.0 refresh tokens for an application')
    p_list_tokens.add_argument('id', help='Application ID')
    p_list_tokens.add_argument('--expand', help='Expand response to inline scope details')
    _add_limit_arg(p_list_tokens)

    p_get_token = sub.add_parser('get-token', help='Get a specific OAuth 2.0 refresh token')
    p_get_token.add_argument('id', help='Application ID')
    p_get_token.add_argument('token_id', help='Token ID')
    p_get_token.add_argument('--expand', help='Expand response to inline scope details')

    p_get_user = sub.add_parser('get-user', help='Get a specific user assignment for an application')
    p_get_user.add_argument('id', help='Application ID')
    p_get_user.add_argument('user_id', help='User ID')
    p_get_user.add_argument('--expand', help='Expand response')

    args = parser.parse_args()
    session, base_url = get_session()

    commands = {
        'list': cmd_list,
        'get': cmd_get,
        'get-users': cmd_get_users,
        'get-groups': cmd_get_groups,
        'get-group': cmd_get_group,
        'get-connection': cmd_get_connection,
        'get-connection-jwks': cmd_get_connection_jwks,
        'list-csrs': cmd_list_csrs,
        'get-csr': cmd_get_csr,
        'list-jwks': cmd_list_jwks,
        'get-jwk': cmd_get_jwk,
        'list-keys': cmd_list_keys,
        'get-key': cmd_get_key,
        'list-secrets': cmd_list_secrets,
        'get-secret': cmd_get_secret,
        'list-cwo-connections': cmd_list_cwo_connections,
        'get-cwo-connection': cmd_get_cwo_connection,
        'list-features': cmd_list_features,
        'get-feature': cmd_get_feature,
        'list-federated-claims': cmd_list_federated_claims,
        'get-federated-claim': cmd_get_federated_claim,
        'list-grants': cmd_list_grants,
        'get-grant': cmd_get_grant,
        'list-group-push-mappings': cmd_list_group_push_mappings,
        'get-group-push-mapping': cmd_get_group_push_mapping,
        'list-interclient-allowed-apps': cmd_list_interclient_allowed_apps,
        'list-interclient-target-apps': cmd_list_interclient_target_apps,
        'get-saml-metadata': cmd_get_saml_metadata,
        'list-tokens': cmd_list_tokens,
        'get-token': cmd_get_token,
        'get-user': cmd_get_user,
    }

    try:
        result = commands[args.command](session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
