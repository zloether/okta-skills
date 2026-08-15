#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta session information via the Okta API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run  # noqa: E402
from okta_client import get_resource  # noqa: E402


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/sessions/{args.id}')


def main():
    parser = argparse.ArgumentParser(description='Read Okta session information')
    sub = parser.add_subparsers(dest='command', required=True)

    p_get = sub.add_parser('get', help='Get session information by session ID')
    p_get.add_argument('id', help='Session ID')

    run(parser, {
        'get': cmd_get,
    })


if __name__ == '__main__':
    main()
