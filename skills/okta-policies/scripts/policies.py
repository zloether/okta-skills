#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta policies via the Okta API."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / 'shared'))
from okta_client import get_session, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/policies', {'type': args.type})


def cmd_get(session, base_url, args):
    resp = session.get(f'{base_url}/api/v1/policies/{args.id}')
    resp.raise_for_status()
    return resp.json()


def cmd_get_rules(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/policies/{args.id}/rules')


def main():
    parser = argparse.ArgumentParser(description='Read Okta policies')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List policies')
    p_list.add_argument(
        '--type',
        required=True,
        help='Policy type (e.g. OKTA_SIGN_ON, MFA_ENROLL, PASSWORD, ACCESS_POLICY)',
    )

    p_get = sub.add_parser('get', help='Get a policy by ID')
    p_get.add_argument('id', help='Policy ID')

    p_rules = sub.add_parser('get-rules', help='List rules for a policy')
    p_rules.add_argument('id', help='Policy ID')

    args = parser.parse_args()
    session, base_url = get_session()

    try:
        if args.command == 'list':
            result = cmd_list(session, base_url, args)
        elif args.command == 'get':
            result = cmd_get(session, base_url, args)
        elif args.command == 'get-rules':
            result = cmd_get_rules(session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
