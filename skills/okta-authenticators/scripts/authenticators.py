#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta authenticators, their methods, and custom AAGUIDs via the Okta API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run
from okta_client import get_resource, paginated_get


def cmd_list(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/authenticators')


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/authenticators/{args.authenticator_id}')


def cmd_list_methods(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/authenticators/{args.authenticator_id}/methods')


def cmd_get_method(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/authenticators/{args.authenticator_id}/methods/{args.method_type}',
    )


def cmd_list_aaguids(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/authenticators/{args.authenticator_id}/aaguids')


def cmd_get_aaguid(session, base_url, args):
    return get_resource(
        session,
        f'{base_url}/api/v1/authenticators/{args.authenticator_id}/aaguids/{args.aaguid}',
    )


def main():
    parser = argparse.ArgumentParser(description='Read Okta authenticators, methods, and custom AAGUIDs')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list', help='List all authenticators')

    p_get = sub.add_parser('get', help='Get an authenticator by ID')
    p_get.add_argument('authenticator_id', help='Authenticator ID')

    p_list_methods = sub.add_parser('list-methods', help='List all methods of an authenticator')
    p_list_methods.add_argument('authenticator_id', help='Authenticator ID')

    p_get_method = sub.add_parser('get-method', help='Get a specific authenticator method')
    p_get_method.add_argument('authenticator_id', help='Authenticator ID')
    p_get_method.add_argument('method_type', help='Method type, e.g. sms, push, webauthn')

    p_list_aaguids = sub.add_parser(
        'list-aaguids', help='List custom AAGUIDs for an authenticator'
    )
    p_list_aaguids.add_argument('authenticator_id', help='Authenticator ID')

    p_get_aaguid = sub.add_parser('get-aaguid', help='Get a specific custom AAGUID')
    p_get_aaguid.add_argument('authenticator_id', help='Authenticator ID')
    p_get_aaguid.add_argument('aaguid', help='Custom AAGUID')

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
        'list-methods': cmd_list_methods,
        'get-method': cmd_get_method,
        'list-aaguids': cmd_list_aaguids,
        'get-aaguid': cmd_get_aaguid,
    })


if __name__ == '__main__':
    main()
