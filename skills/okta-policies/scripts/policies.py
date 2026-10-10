#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta policies via the Okta API."""
import argparse
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run
from okta_client import get_resource, paginated_get


def cmd_list(session, base_url, args):
    params = {'type': args.type}
    if args.status:
        params['status'] = args.status
    if args.q:
        params['q'] = args.q
    if args.expand:
        params['expand'] = args.expand
    if args.sort_by:
        params['sortBy'] = args.sort_by
    if args.resource_id:
        params['resourceId'] = args.resource_id
    return paginated_get(session, f'{base_url}/api/v1/policies', params, limit=args.limit)


def cmd_get(session, base_url, args):
    params = {}
    if args.expand:
        params['expand'] = args.expand
    return get_resource(session, f'{base_url}/api/v1/policies/{quote(args.id, safe="")}', params=params)


def _prune(obj):
    """Recursively drop `_links`, nulls, and empty lists/dicts so rule conditions/actions read compactly."""
    if isinstance(obj, dict):
        pruned = {k: _prune(v) for k, v in obj.items() if k != '_links'}
        return {k: v for k, v in pruned.items() if v not in (None, [], {})}
    if isinstance(obj, list):
        return [_prune(v) for v in obj]
    return obj


def cmd_get_rules(session, base_url, args):
    rules = paginated_get(session, f'{base_url}/api/v1/policies/{quote(args.id, safe="")}/rules')
    if not args.summary:
        return rules
    # `conditions` is re-added after pruning: null there is meaningful (it marks the catch-all rule)
    return [
        _prune({k: v for k, v in rule.items() if k != 'created'}) | {'conditions': _prune(rule.get('conditions'))}
        for rule in rules
    ]


def cmd_get_rule(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/policies/{quote(args.id, safe="")}/rules/{quote(args.rule_id, safe="")}')


def cmd_list_mappings(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/policies/{quote(args.id, safe="")}/mappings')


def cmd_get_mapping(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/policies/{quote(args.id, safe="")}/mappings/{quote(args.mapping_id, safe="")}')


def main():
    parser = argparse.ArgumentParser(description='Read Okta policies')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List policies')
    p_list.add_argument(
        '--type',
        required=True,
        choices=[
            'ACCESS_POLICY', 'ENTITY_RISK', 'IDP_DISCOVERY', 'MFA_ENROLL', 'OKTA_SIGN_ON',
            'PASSWORD', 'POST_AUTH_SESSION', 'PROFILE_ENROLLMENT', 'DEVICE_SIGNAL_COLLECTION',
            'SESSION_VIOLATION_DETECTION', 'CLIENT_UPDATE', 'IDENTITY_CLAIM_SOURCING',
        ],
        help='Policy type',
    )
    p_list.add_argument('--status', choices=['ACTIVE', 'INACTIVE'], help='Filter by policy status')
    p_list.add_argument('--q', help='Search policies by name prefix')
    p_list.add_argument('--expand', help='Expand response, e.g. rules')
    p_list.add_argument('--sort-by', help='Property to sort by')
    p_list.add_argument('--resource-id', help='Scope to policies tied to a specific authorization server')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get a policy by ID')
    p_get.add_argument('id', help='Policy ID')
    p_get.add_argument('--expand', help='Expand response, e.g. rules')

    p_rules = sub.add_parser('get-rules', help='List rules for a policy')
    p_rules.add_argument('id', help='Policy ID')
    p_rules.add_argument('--summary', action='store_true', help='Compact output: drop _links, created, and null/empty fields from each rule (conditions: null is kept — it marks the catch-all rule)')

    p_rule = sub.add_parser('get-rule', help='Get a specific policy rule by ID')
    p_rule.add_argument('id', help='Policy ID')
    p_rule.add_argument('rule_id', help='Rule ID')

    p_mappings = sub.add_parser('list-mappings', help='List all resources mapped to a policy')
    p_mappings.add_argument('id', help='Policy ID')

    p_mapping = sub.add_parser('get-mapping', help='Get a specific policy resource mapping')
    p_mapping.add_argument('id', help='Policy ID')
    p_mapping.add_argument('mapping_id', help='Mapping ID')

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
        'get-rules': cmd_get_rules,
        'get-rule': cmd_get_rule,
        'list-mappings': cmd_list_mappings,
        'get-mapping': cmd_get_mapping,
    })


if __name__ == '__main__':
    main()
