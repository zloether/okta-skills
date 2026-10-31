#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta network zones via the Okta API."""
import argparse
import ipaddress
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import add_page_size, run, with_page_size
from okta_client import get_resource, paginated_get


def cmd_list(session, base_url, args):
    params = {}
    if args.usage:
        # Not urllib.parse.quote: this is a filter *expression* value sent via
        # params=, which requests URL-encodes automatically — it's not a raw
        # URL path segment.
        params['filter'] = f'usage eq "{args.usage}"'
    elif args.system is not None:
        params['filter'] = f'system eq {"true" if args.system else "false"}'
    with_page_size(params, args)
    zones = paginated_get(session, f'{base_url}/api/v1/zones', params, limit=args.limit)
    if not args.cidrs:
        return zones
    return [
        {'id': z.get('id'), 'name': z.get('name'), 'usage': z.get('usage'), 'status': z.get('status'),
         'gateways': _to_cidrs(z.get('gateways')), 'proxies': _to_cidrs(z.get('proxies'))}
        for z in zones if z.get('type') == 'IP'
    ]


def _to_cidrs(entries):
    # Gateway/proxy values are "a.b.c.d/n", a bare "a.b.c.d", or a RANGE "start-end"
    cidrs = []
    for entry in entries or []:
        start, _, end = entry['value'].partition('-')
        if end:
            cidrs += ipaddress.summarize_address_range(ipaddress.ip_address(start.strip()), ipaddress.ip_address(end.strip()))
        else:
            cidrs.append(ipaddress.ip_network(start.strip(), strict=False))
    return [str(c) for c in cidrs]


def cmd_get(session, base_url, args):
    return get_resource(session, '{base}/api/v1/zones/{id}', path_params={'base': base_url, 'id': args.id})


def _parse_bool(value):
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    raise argparse.ArgumentTypeError(f"invalid value {value!r}, expected 'true' or 'false'")


def main():
    parser = argparse.ArgumentParser(description='Read Okta network zones')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List network zones')
    p_list_grp = p_list.add_mutually_exclusive_group()
    p_list_grp.add_argument('--usage', choices=['POLICY', 'BLOCKLIST'], help='Filter by zone usage')
    p_list_grp.add_argument(
        '--system', type=_parse_bool, metavar='{true,false}',
        help='Filter to system-defined (true) or custom (false) zones',
    )
    p_list.add_argument('--limit', type=int, help='Maximum number of results')
    p_list.add_argument(
        '--cidrs', action='store_true',
        help='Return only IP zones as {id, name, usage, status, gateways, proxies} with every entry normalized to CIDR',
    )
    add_page_size(p_list)

    p_get = sub.add_parser('get', help='Get a network zone by ID')
    p_get.add_argument('id', help='Zone ID')

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
    })


if __name__ == '__main__':
    main()
