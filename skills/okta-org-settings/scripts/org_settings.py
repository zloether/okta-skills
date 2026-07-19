#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta org settings via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from okta_client import get_session, get_resource, paginated_get  # noqa: E402


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org')


def cmd_list_contact_types(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/org/contacts')


def cmd_get_contact(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/contacts/{args.contact_type}')


def cmd_get_captcha_settings(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/captcha')


def cmd_get_third_party_admin_setting(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/orgSettings/thirdPartyAdminSetting')


def cmd_get_preferences(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/preferences')


def cmd_get_aerial_consent(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/privacy/aerial')


def cmd_get_communication_settings(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/privacy/oktaCommunication')


def cmd_get_support_settings(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/privacy/oktaSupport')


def cmd_list_support_cases(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/privacy/oktaSupport/cases')


def cmd_get_auto_assign_admin_app_setting(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/settings/autoAssignAdminAppSetting')


def cmd_get_client_privileges_setting(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/settings/clientPrivilegesSetting')


def cmd_list_yubikey_tokens(session, base_url, args):
    params = {}
    if args.filter:
        params['filter'] = args.filter
    if args.expand_user:
        params['expand'] = 'user'
    return paginated_get(session, f'{base_url}/api/v1/org/factors/yubikey_token/tokens', params, limit=args.limit)


def cmd_get_yubikey_token(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/org/factors/yubikey_token/tokens/{args.id}')


def main():
    parser = argparse.ArgumentParser(description='Read Okta org settings')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('get', help="Get the org's general settings")

    sub.add_parser('list-contact-types', help='List all org contact types')

    p_get_contact = sub.add_parser('get-contact', help='Get the user assigned to a contact type')
    p_get_contact.add_argument('contact_type', choices=['BILLING', 'TECHNICAL'], help='Contact type')

    sub.add_parser('get-captcha-settings', help="Get the org-wide CAPTCHA settings")

    sub.add_parser('get-third-party-admin-setting', help="Get the org's third-party admin setting")

    sub.add_parser('get-preferences', help="Get the org's end-user UI preferences")

    sub.add_parser('get-aerial-consent', help='Get the Okta Aerial consent grant details for the org')

    sub.add_parser('get-communication-settings', help="Get the org's Okta communication opt-in settings")

    sub.add_parser('get-support-settings', help="Get the org's Okta Support access settings")

    sub.add_parser('list-support-cases', help='List all open Okta Support cases')

    sub.add_parser('get-auto-assign-admin-app-setting', help='Get the auto-assign Admin Console app setting')

    sub.add_parser('get-client-privileges-setting', help='Get the default public client app role setting')

    p_list_yubikey = sub.add_parser('list-yubikey-tokens', help='List all YubiKey OTP tokens provisioned in the org')
    p_list_yubikey.add_argument('--filter', help='Filter expression, e.g. \'status eq "ACTIVE"\'')
    p_list_yubikey.add_argument('--limit', type=int, help='Maximum number of results')
    p_list_yubikey.add_argument('--expand-user', action='store_true', help='Embed the assigned user resource')

    p_get_yubikey = sub.add_parser('get-yubikey-token', help='Get a YubiKey OTP token by ID')
    p_get_yubikey.add_argument('id', help='YubiKey OTP token ID')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'get':
            result = cmd_get(session, base_url, args)
        elif args.command == 'list-contact-types':
            result = cmd_list_contact_types(session, base_url, args)
        elif args.command == 'get-contact':
            result = cmd_get_contact(session, base_url, args)
        elif args.command == 'get-captcha-settings':
            result = cmd_get_captcha_settings(session, base_url, args)
        elif args.command == 'get-third-party-admin-setting':
            result = cmd_get_third_party_admin_setting(session, base_url, args)
        elif args.command == 'get-preferences':
            result = cmd_get_preferences(session, base_url, args)
        elif args.command == 'get-aerial-consent':
            result = cmd_get_aerial_consent(session, base_url, args)
        elif args.command == 'get-communication-settings':
            result = cmd_get_communication_settings(session, base_url, args)
        elif args.command == 'get-support-settings':
            result = cmd_get_support_settings(session, base_url, args)
        elif args.command == 'list-support-cases':
            result = cmd_list_support_cases(session, base_url, args)
        elif args.command == 'get-auto-assign-admin-app-setting':
            result = cmd_get_auto_assign_admin_app_setting(session, base_url, args)
        elif args.command == 'get-client-privileges-setting':
            result = cmd_get_client_privileges_setting(session, base_url, args)
        elif args.command == 'list-yubikey-tokens':
            result = cmd_list_yubikey_tokens(session, base_url, args)
        elif args.command == 'get-yubikey-token':
            result = cmd_get_yubikey_token(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
