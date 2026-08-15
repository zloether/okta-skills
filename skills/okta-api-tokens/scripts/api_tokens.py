#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta API token metadata via the Okta API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run  # noqa: E402
from okta_client import get_resource, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/api-tokens')


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/api-tokens/{args.id}')


def main():
    parser = argparse.ArgumentParser(description='Read Okta API token metadata')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list', help='List metadata for all API tokens in the org')

    p_get = sub.add_parser('get', help='Get an API token\'s metadata by ID')
    p_get.add_argument('id', help='API token ID')

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
    })


if __name__ == '__main__':
    main()
