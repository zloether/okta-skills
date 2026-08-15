#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta device posture checks via the Okta API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run
from okta_client import get_resource, paginated_get


def cmd_list(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/device-posture-checks')


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/device-posture-checks/{args.id}')


def cmd_list_defaults(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/device-posture-checks/default')


def main():
    parser = argparse.ArgumentParser(description='Read Okta device posture checks')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list', help='List device posture checks')

    p_get = sub.add_parser('get', help='Get a device posture check by ID')
    p_get.add_argument('id', help='Device posture check ID')

    sub.add_parser(
        'list-defaults', help='List Okta-built-in (BUILTIN) default device posture checks'
    )

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
        'list-defaults': cmd_list_defaults,
    })


if __name__ == '__main__':
    main()
