#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta ThreatInsight, security events provider (SSF), and bot protection settings via the Okta API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run  # noqa: E402
from okta_client import get_resource, paginated_get  # noqa: E402


def cmd_get_threat_insight_config(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/threats/configuration')


def cmd_list_security_events_providers(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/security-events-providers')


def cmd_get_security_events_provider(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/security-events-providers/{args.id}')


def cmd_get_ssf_streams(session, base_url, args):
    params = {}
    if args.stream_id:
        params['stream_id'] = args.stream_id
    return get_resource(session, f'{base_url}/api/v1/ssf/stream', params=params)


def cmd_get_ssf_stream_status(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/ssf/stream/status', params={'stream_id': args.stream_id})


def cmd_get_bot_protection_config(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/bot-protection/configuration')


def main():
    parser = argparse.ArgumentParser(
        description='Read Okta ThreatInsight, security events provider (SSF), and bot protection settings'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('get-threat-insight-config', help='Get the ThreatInsight configuration')

    sub.add_parser('list-security-events-providers', help='List all security events providers (SSF receivers)')

    p_sep = sub.add_parser('get-security-events-provider', help='Get a security events provider by ID')
    p_sep.add_argument('id', help='Security events provider ID')

    p_ssf_streams = sub.add_parser('get-ssf-streams', help='Get all SSF stream configurations, or one if --stream-id is given')
    p_ssf_streams.add_argument('--stream-id', help='Restrict to a single SSF stream configuration')

    p_ssf_status = sub.add_parser('get-ssf-stream-status', help='Get the status of an SSF stream')
    p_ssf_status.add_argument('stream_id', help='SSF stream configuration ID')

    sub.add_parser('get-bot-protection-config', help='Get the bot protection configuration')

    run(parser, {
        'get-threat-insight-config': cmd_get_threat_insight_config,
        'list-security-events-providers': cmd_list_security_events_providers,
        'get-security-events-provider': cmd_get_security_events_provider,
        'get-ssf-streams': cmd_get_ssf_streams,
        'get-ssf-stream-status': cmd_get_ssf_stream_status,
        'get-bot-protection-config': cmd_get_bot_protection_config,
    })


if __name__ == '__main__':
    main()
