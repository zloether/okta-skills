#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta for AI Agents (workload principals): agents, connections, providers, delegation links, and virtual MCP servers."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import add_page_size, run, with_page_size
from okta_client import get_resource, paginated_get_wrapped


def _params(args, **mapping):
    """Map {api_param: attr_name} to a params dict, skipping unset attributes, then apply paging."""
    params = {}
    for api_name, attr in mapping.items():
        value = getattr(args, attr, None)
        if value:
            params[api_name] = value
    return with_page_size(params, args)


def cmd_list(session, base_url, args):
    params = _params(
        args, search='search', expand='expand', providerId='provider_id', ownerOrn='owner_orn',
        orderBy='sort_by', sortOrder='sort_order',
    )
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/ai-agents', 'data', params, limit=args.limit,
        path_params={'base': base_url},
    )


def cmd_get(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agents/{id}',
        params=_expand(args), path_params={'base': base_url, 'id': args.id},
    )


def cmd_get_schema(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agents/schema/default', path_params={'base': base_url},
    )


def cmd_get_provider_attributes(session, base_url, args):
    params = {'platforms': args.platform} if args.platform else {}
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/ai-agents/provider-attributes/{name}', 'data', params,
        path_params={'base': base_url, 'name': args.provider_name},
    )


def cmd_list_connections(session, base_url, args):
    params = _params(args, filter='filter')
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/ai-agents/{agent_id}/connections', 'data', params,
        limit=args.limit, path_params={'base': base_url, 'agent_id': args.agent_id},
    )


def cmd_get_connection(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agents/{agent_id}/connections/{connection_id}',
        path_params={'base': base_url, 'agent_id': args.agent_id, 'connection_id': args.connection_id},
    )


def cmd_list_jwks(session, base_url, args):
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/ai-agents/{agent_id}/credentials/jwks', 'data',
        limit=args.limit, path_params={'base': base_url, 'agent_id': args.agent_id},
    )


def cmd_get_jwk(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agents/{agent_id}/credentials/jwks/{key_id}',
        path_params={'base': base_url, 'agent_id': args.agent_id, 'key_id': args.key_id},
    )


def cmd_list_potential_connections(session, base_url, args):
    params = _params(args, filter='filter', match='match', actorId='actor_id')
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/potential-connections', 'data', params,
        limit=args.limit, path_params={'base': base_url},
    )


def cmd_list_operations(session, base_url, args):
    params = _params(
        args, search='search', sourceInstanceName='source_instance_name', orderBy='sort_by', sortOrder='sort_order',
    )
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/operations', 'data', params, limit=args.limit,
        path_params={'base': base_url},
    )


def cmd_get_operation(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/operations/{id}', path_params={'base': base_url, 'id': args.id},
    )


def cmd_list_providers(session, base_url, args):
    params = _params(
        args, search='search', sourceInstanceName='source_instance_name', orderBy='sort_by',
        sortOrder='sort_order', expand='expand',
    )
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/ai-agent-providers', 'data', params, limit=args.limit,
        path_params={'base': base_url},
    )


def cmd_get_provider(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agent-providers/{id}',
        params=_expand(args), path_params={'base': base_url, 'id': args.id},
    )


def cmd_list_provider_priorities(session, base_url, args):
    params = _params(args, sourceInstanceName='source_instance_name')
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/ai-agent-providers/priorities', 'data', params,
        limit=args.limit, path_params={'base': base_url},
    )


def cmd_list_provider_stats(session, base_url, args):
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/ai-agent-providers/stats', 'data',
        {'ids': ','.join(args.ids)}, path_params={'base': base_url},
    )


def cmd_get_provider_profile_mappings(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agent-providers/{provider_id}/profile-mappings',
        path_params={'base': base_url, 'provider_id': args.provider_id},
    )


def cmd_list_provider_staging(session, base_url, args):
    params = _params(args, type='type')
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/ai-agent-providers/{provider_id}/staging', 'data', params,
        limit=args.limit, path_params={'base': base_url, 'provider_id': args.provider_id},
    )


def cmd_get_provider_staging_stats(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agent-providers/{provider_id}/staging/stats',
        path_params={'base': base_url, 'provider_id': args.provider_id},
    )


def cmd_get_provider_staging(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agent-providers/{provider_id}/staging/{id}',
        path_params={'base': base_url, 'provider_id': args.provider_id, 'id': args.id},
    )


def cmd_get_provider_staging_review(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/ai-agent-providers/{provider_id}/staging/{id}/review',
        path_params={'base': base_url, 'provider_id': args.provider_id, 'id': args.id},
    )


def cmd_list_delegation_links(session, base_url, args):
    params = _params(args, filter='filter', expand='expand')
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/delegation-links', 'data', params, limit=args.limit,
        path_params={'base': base_url},
    )


def cmd_get_delegation_link(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/delegation-links/{id}',
        path_params={'base': base_url, 'id': args.id},
    )


def cmd_list_virtual_mcp_servers(session, base_url, args):
    params = _params(args, filter='filter')
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/virtual-mcp-servers', 'data', params, limit=args.limit,
        path_params={'base': base_url},
    )


def cmd_get_virtual_mcp_server(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/virtual-mcp-servers/{id}',
        path_params={'base': base_url, 'id': args.id},
    )


def cmd_list_virtual_mcp_connections(session, base_url, args):
    params = _params(args)
    return paginated_get_wrapped(
        session, '{base}/workload-principals/api/v1/virtual-mcp-servers/{server_id}/connections', 'data', params,
        limit=args.limit, path_params={'base': base_url, 'server_id': args.server_id},
    )


def cmd_get_virtual_mcp_connection(session, base_url, args):
    return get_resource(
        session, '{base}/workload-principals/api/v1/virtual-mcp-servers/{server_id}/connections/{connection_id}',
        path_params={'base': base_url, 'server_id': args.server_id, 'connection_id': args.connection_id},
    )


def cmd_list_virtual_mcp_capabilities(session, base_url, args):
    params = _params(args)
    if args.input_schema:
        params['expand'] = 'inputSchema'
    return paginated_get_wrapped(
        session,
        '{base}/workload-principals/api/v1/virtual-mcp-servers/{server_id}/connections/{connection_id}/capabilities',
        'data', params, limit=args.limit,
        path_params={'base': base_url, 'server_id': args.server_id, 'connection_id': args.connection_id},
    )


def cmd_get_virtual_mcp_capability(session, base_url, args):
    return get_resource(
        session,
        '{base}/workload-principals/api/v1/virtual-mcp-servers/{server_id}/connections/{connection_id}/capabilities/{capability_id}',
        params={'expand': 'inputSchema'} if args.input_schema else None,
        path_params={
            'base': base_url, 'server_id': args.server_id, 'connection_id': args.connection_id,
            'capability_id': args.capability_id,
        },
    )


def _expand(args):
    return {'expand': args.expand} if args.expand else None


def _paged(parser):
    parser.add_argument('--limit', type=int, help='Maximum number of results')
    add_page_size(parser)
    return parser


def main():
    parser = argparse.ArgumentParser(description='Read Okta for AI Agents (workload principals) resources')
    sub = parser.add_subparsers(dest='command', required=True)

    p = _paged(sub.add_parser('list', help='List AI agents'))
    p.add_argument('--search', help='Search expression, e.g. \'profile.name sw "Sales" and status eq "ACTIVE"\'')
    p.add_argument('--provider-id', help='Only agents imported by this AI agent provider')
    p.add_argument('--owner-orn', help='Comma-separated user/group owner ORNs (max 10)')
    p.add_argument('--expand', choices=['sources'], help='Embed associated sources under _embedded.sources')
    p.add_argument('--sort-by', choices=['createdDate', 'lastUpdate'])
    p.add_argument('--sort-order', choices=['asc', 'desc'])

    p = sub.add_parser('get', help='Get an AI agent by ID')
    p.add_argument('id', help='AI agent ID')
    p.add_argument('--expand', choices=['sources'], help='Embed associated sources under _embedded.sources')

    sub.add_parser('get-schema', help='Get the default AI agent profile schema')

    p = sub.add_parser('get-provider-attributes', help='List source attributes available for provider profile mappings')
    p.add_argument('provider_name', help='Provider name (e.g. the integration source type)')
    p.add_argument('--platform', action='append', help='Limit to a platform, e.g. AWS_BEDROCK_AGENTS (repeatable)')

    p = _paged(sub.add_parser('list-connections', help="List an AI agent's resource connections"))
    p.add_argument('agent_id', help='AI agent ID')
    p.add_argument('--filter', help='e.g. \'connectionType eq "MCP_SERVER" and status eq "ACTIVE"\' (eq/and only)')

    p = sub.add_parser('get-connection', help="Get one of an AI agent's resource connections")
    p.add_argument('agent_id', help='AI agent ID')
    p.add_argument('connection_id', help='Connection ID')

    p = sub.add_parser('list-jwks', help="List an AI agent's public JSON Web Keys")
    p.add_argument('agent_id', help='AI agent ID')
    p.add_argument('--limit', type=int, help='Maximum number of results')

    p = sub.add_parser('get-jwk', help="Get one of an AI agent's public JSON Web Keys")
    p.add_argument('agent_id', help='AI agent ID')
    p.add_argument('key_id', help='Key ID')

    p = _paged(sub.add_parser('list-potential-connections', help='List resources an agent could be connected to'))
    p.add_argument('--filter', required=True, help='e.g. \'connectionType eq "IDENTITY_ASSERTION_CUSTOM_AS"\'')
    p.add_argument('--match', help='Case-insensitive substring match on the resource name')
    p.add_argument('--actor-id', help='AI agent ID; adds clientIdAtResource to app-instance identity assertions')

    p = _paged(sub.add_parser('list-operations', help='List workload principal (agent / virtual MCP) async operations'))
    p.add_argument('--search', help='Search expression')
    p.add_argument('--source-instance-name', help='Filter by integration source instance name')
    p.add_argument('--sort-by', choices=['createdDate', 'lastUpdate'])
    p.add_argument('--sort-order', choices=['asc', 'desc'])

    p = sub.add_parser('get-operation', help='Get a workload principal operation by ID')
    p.add_argument('id', help='Operation ID')

    p = _paged(sub.add_parser('list-providers', help='List AI agent providers (agent platform integrations)'))
    p.add_argument('--search', help='Search expression')
    p.add_argument('--source-instance-name', help='Filter by integration source instance name')
    p.add_argument('--expand', choices=['profileMapping'], help='Embed the profile mapping under _embedded')
    p.add_argument('--sort-by', choices=['createdDate', 'lastUpdate', 'lastImportedDate', 'nextImportDate'])
    p.add_argument('--sort-order', choices=['asc', 'desc'])

    p = sub.add_parser('get-provider', help='Get an AI agent provider by ID')
    p.add_argument('id', help='Provider ID')
    p.add_argument('--expand', choices=['profileMapping'], help='Embed the profile mapping under _embedded')

    p = _paged(sub.add_parser('list-provider-priorities', help='List provider integration-source priorities'))
    p.add_argument('--source-instance-name', help='Filter by integration source instance name')

    p = sub.add_parser('list-provider-stats', help='Agent / staged-agent counts per provider')
    p.add_argument('ids', nargs='+', help='Provider IDs (max 200); missing IDs have no agents')

    p = sub.add_parser('get-provider-profile-mappings', help="Get a provider's source-to-agent profile attribute mappings")
    p.add_argument('provider_id', help='Provider ID')

    p = _paged(sub.add_parser('list-provider-staging', help='List staged (unconfirmed) agents for a provider'))
    p.add_argument('provider_id', help='Provider ID')
    p.add_argument('--type', choices=['DUPLICATE', 'IGNORED', 'NEW'], help='Staging item type')

    p = sub.add_parser('get-provider-staging-stats', help='Count staging items by type for a provider')
    p.add_argument('provider_id', help='Provider ID')

    p = sub.add_parser('get-provider-staging', help='Get one staging item')
    p.add_argument('provider_id', help='Provider ID')
    p.add_argument('id', help='Staging item ID')

    p = sub.add_parser('get-provider-staging-review', help='Compare incoming vs existing agent for a DUPLICATE staging item')
    p.add_argument('provider_id', help='Provider ID')
    p.add_argument('id', help='Staging item ID')

    p = _paged(sub.add_parser('list-delegation-links', help='List delegation links (who may act on behalf of whom)'))
    p.add_argument(
        '--filter', required=True,
        help='e.g. \'from.clientOrn eq "orn:..."\' or \'to.resourceOrn eq "orn:..."\' (at least one required)',
    )
    p.add_argument(
        '--expand', action='append', choices=['agentMetadata', 'appMetadata', 'customAuthorizationServerMetadata'],
        help='Embed metadata under _embedded (repeatable)',
    )

    p = sub.add_parser('get-delegation-link', help='Get a delegation link by ID')
    p.add_argument('id', help='Delegation link ID')

    p = _paged(sub.add_parser('list-virtual-mcp-servers', help='List virtual MCP servers'))
    p.add_argument('--filter', help='e.g. \'status eq "ACTIVE"\' or \'profile.displayName sw "Sales"\'')

    p = sub.add_parser('get-virtual-mcp-server', help='Get a virtual MCP server by ID')
    p.add_argument('id', help='Virtual MCP server ID')

    p = _paged(sub.add_parser('list-virtual-mcp-connections', help="List a virtual MCP server's upstream connections"))
    p.add_argument('server_id', help='Virtual MCP server ID')

    p = sub.add_parser('get-virtual-mcp-connection', help="Get one of a virtual MCP server's connections")
    p.add_argument('server_id', help='Virtual MCP server ID')
    p.add_argument('connection_id', help='Connection ID')

    p = _paged(sub.add_parser('list-virtual-mcp-capabilities', help="List a virtual MCP connection's tools/capabilities"))
    p.add_argument('server_id', help='Virtual MCP server ID')
    p.add_argument('connection_id', help='Connection ID')
    p.add_argument('--input-schema', action='store_true', help='Include each capability\'s JSON input schema')

    p = sub.add_parser('get-virtual-mcp-capability', help='Get one virtual MCP connection capability')
    p.add_argument('server_id', help='Virtual MCP server ID')
    p.add_argument('connection_id', help='Connection ID')
    p.add_argument('capability_id', help='Capability ID')
    p.add_argument('--input-schema', action='store_true', help='Include the JSON input schema')

    run(parser, {
        name: globals()['cmd_' + name.replace('-', '_')]
        for name in sub.choices
    })


if __name__ == '__main__':
    main()
