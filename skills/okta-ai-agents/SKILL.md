---
name: okta-ai-agents
description: Read Okta for AI Agents (workload principals) — registered AI agents, their resource connections and public keys, agent providers (platform integrations) and staged imports, delegation links, and virtual MCP servers with their connections and capabilities. Use when asked which AI agents exist, what an agent can access and how it authenticates, who owns or imported an agent, which MCP tools are exposed, or why an agent operation failed.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. Beta API — requires an Okta for AI Agents subscription and a SUPER_ADMIN token or OAuth app.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py <command> [options]
```

All endpoints are under `/workload-principals/api/v1/`. The API is **Beta** and may change.

### Agents: list / get / get-schema / get-provider-attributes
```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py list
uv run skills/okta-ai-agents/scripts/ai_agents.py list --search 'status eq "ACTIVE" and profile.platform eq "AWS_BEDROCK_AGENTS"'
uv run skills/okta-ai-agents/scripts/ai_agents.py list --provider-id aap1... --expand sources
uv run skills/okta-ai-agents/scripts/ai_agents.py list --owner-orn orn:okta:directory:00o...:users:00u...
uv run skills/okta-ai-agents/scripts/ai_agents.py get wlp1...
uv run skills/okta-ai-agents/scripts/ai_agents.py get-schema
uv run skills/okta-ai-agents/scripts/ai_agents.py get-provider-attributes aws --platform AWS_BEDROCK_AGENTS
```
`--search` supports `eq` on `id`, `status`, `signOnProvider.appInstanceId`, `oauthClient.type`; `sw`/`co`/`eq` on `profile.name` and `profile.platform`; and `eq`/`gt`/`ge`/`lt`/`le` on `createdDate` and `lastUpdate`. `--owner-orn` takes up to 10 comma-separated ORNs. `get-schema` returns the default agent profile schema (base + custom attributes).

### Connections and keys: list-connections / get-connection / list-jwks / get-jwk
What an agent is allowed to reach, and the public keys it authenticates with.
```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py list-connections wlp1...
uv run skills/okta-ai-agents/scripts/ai_agents.py list-connections wlp1... --filter 'connectionType eq "IDENTITY_ASSERTION_MCP_SERVER" and status eq "ACTIVE"'
uv run skills/okta-ai-agents/scripts/ai_agents.py get-connection wlp1... rcn1...
uv run skills/okta-ai-agents/scripts/ai_agents.py list-jwks wlp1...
uv run skills/okta-ai-agents/scripts/ai_agents.py get-jwk wlp1... <keyId>
```
`--filter` supports only `eq` combined with `and`, on `connectionType`, `status`, `resourceIndicator`, `authorizationServer.orn`, `resource.orn`.

### list-potential-connections
Resources an agent *could* be connected to (not existing connections). `--filter` is required.
```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py list-potential-connections --filter 'connectionType eq "IDENTITY_ASSERTION_CUSTOM_AS"'
uv run skills/okta-ai-agents/scripts/ai_agents.py list-potential-connections --filter 'connectionType eq "STS_VAULT_SECRET"' --match prod
uv run skills/okta-ai-agents/scripts/ai_agents.py list-potential-connections --filter 'connectionType eq "IDENTITY_ASSERTION_APP_INSTANCE"' --actor-id wlp1...
```
`--match` is a case-insensitive prefix-friendly substring on the resource name. `--actor-id` makes app-instance identity assertions include `clientIdAtResource` for that agent.

### Operations: list-operations / get-operation
Async jobs behind agent and virtual-MCP lifecycle changes (register, activate, import, staging, …).
```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py list-operations --sort-by createdDate --sort-order desc
uv run skills/okta-ai-agents/scripts/ai_agents.py get-operation wpo1...
```

### Providers: list-providers / get-provider / list-provider-priorities / list-provider-stats / get-provider-profile-mappings
Agent providers are integrations that import agents from a platform (Bedrock, Copilot Studio, Agentforce, …).
```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py list-providers --expand profileMapping
uv run skills/okta-ai-agents/scripts/ai_agents.py get-provider aap1...
uv run skills/okta-ai-agents/scripts/ai_agents.py list-provider-priorities
uv run skills/okta-ai-agents/scripts/ai_agents.py list-provider-stats aap1... aap2...
uv run skills/okta-ai-agents/scripts/ai_agents.py get-provider-profile-mappings aap1...
```
`list-provider-stats` takes up to 200 provider IDs; an ID missing from the result has `agentCount` 0.

### Provider staging: list-provider-staging / get-provider-staging-stats / get-provider-staging / get-provider-staging-review
Imported agents held for conflict resolution before they become real agents.
```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py get-provider-staging-stats aap1...
uv run skills/okta-ai-agents/scripts/ai_agents.py list-provider-staging aap1... --type DUPLICATE
uv run skills/okta-ai-agents/scripts/ai_agents.py get-provider-staging aap1... <stagingId>
uv run skills/okta-ai-agents/scripts/ai_agents.py get-provider-staging-review aap1... <stagingId>
```
`get-provider-staging-review` only applies to `DUPLICATE` items and shows an attribute-by-attribute diff.

### Delegation links: list-delegation-links / get-delegation-link
Which token sources may be exchanged for access to which target resource.
```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py list-delegation-links --filter 'from.clientOrn eq "orn:okta:idp:00o...:apps:oauth2:0oa..."'
uv run skills/okta-ai-agents/scripts/ai_agents.py list-delegation-links --filter 'to.resourceOrn eq "orn:..."' --expand agentMetadata --expand customAuthorizationServerMetadata
uv run skills/okta-ai-agents/scripts/ai_agents.py get-delegation-link dl1...
```
`--filter` is required and must include `to.resourceOrn` and/or `from.clientOrn` (`eq`; multiple values with `OR`).

### Virtual MCP servers: list-virtual-mcp-servers / get-virtual-mcp-server / list-virtual-mcp-connections / get-virtual-mcp-connection / list-virtual-mcp-capabilities / get-virtual-mcp-capability
Okta-hosted MCP servers that front upstream MCP servers/APIs and expose a curated set of tools.
```bash
uv run skills/okta-ai-agents/scripts/ai_agents.py list-virtual-mcp-servers --filter 'status eq "ACTIVE"'
uv run skills/okta-ai-agents/scripts/ai_agents.py get-virtual-mcp-server vmcp1...
uv run skills/okta-ai-agents/scripts/ai_agents.py list-virtual-mcp-connections vmcp1...
uv run skills/okta-ai-agents/scripts/ai_agents.py list-virtual-mcp-capabilities vmcp1... rcn1... --input-schema
uv run skills/okta-ai-agents/scripts/ai_agents.py get-virtual-mcp-capability vmcp1... rcn1... <capabilityId>
```
`--filter` supports `eq` on `status` and `sw`/`co`/`eq` on `profile.displayName`.

On every list command that has them, `--limit` caps total results and is also sent as the API `limit` when `--page-size` isn't given; `--page-size 1-200` sets items per request (API default 20). Output is complete across pages unless `--limit` is set. `list-jwks`, `list-provider-stats` and `get-provider-attributes` are not paginated.

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions (must belong to a `SUPER_ADMIN`) |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

**Required OAuth scopes** (`OKTA_CLIENT_SCOPES`): `okta.aiAgents.read` for all agent, connection, key, provider, staging, delegation-link, operation and potential-connection commands; `okta.resourceServers.virtualMcpServers.read` for the `*-virtual-mcp-*` commands. A `401`/`403` on one group only usually means that scope was not granted.

## Output

JSON to stdout. `list-`-prefixed commands return an array of the response's `data` items (paginated via cursor). `get-`-prefixed commands return a single object, except `get-provider-attributes`, which returns an array. Errors are JSON with an `error` key on stderr; exit code 1. Wrapper fields that sit beside `data` are not included in the output; the one that matters, `reconciliationInProgress` on `list-provider-priorities`, is reported as a `warning:` line on stderr when true.

## Output Schema

### Agent object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Agent ID — use with `get`, `list-connections`, `list-jwks` |
| `externalId` | string | ID of the agent on its hosting platform |
| `platform` | string | Hosting platform, e.g. `AWS_BEDROCK_AGENTS`, `MICROSOFT_COPILOT_STUDIO`, `SALESFORCE_AGENTFORCE` |
| `profile.name` / `profile.description` | string | Unique name and description (custom profile attributes may also appear) |
| `status` | string | `STAGED` (created, not yet usable), `ACTIVE`, or `INACTIVE` |
| `oauthClient.clientId` / `oauthClient.type` | string | The agent's OAuth client; type `CIMD` for CIMD-registered agents |
| `signOnProvider.appInstanceId` | string | App instance bound to the agent |
| `appId` | string | Deprecated connected-app ID — use delegation links instead |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |
| `_embedded.sources` | object | Present with `--expand sources` |

### Connection object (`list-connections` / `get-connection`)

Common fields: `id`, `orn`, `connectionType`, `status` (`ACTIVE`/`INACTIVE`), `resourceIndicator`. Remaining fields depend on `connectionType`:

| `connectionType` | Extra fields |
|---|---|
| `IDENTITY_ASSERTION_CUSTOM_AS` | `authorizationServer.{name,issuerUrl,orn}`, `scopeCondition`, `scopes` |
| `IDENTITY_ASSERTION_APP_INSTANCE` | `appInstance.{name,orn}`, `clientIdAtResource`, `scopeCondition`, `scopes` |
| `IDENTITY_ASSERTION_A2A_SERVER` | `resource.{name,orn}` (A2A server), `authorizationServer`, `scopeCondition`, `scopes` |
| `IDENTITY_ASSERTION_MCP_SERVER` | `resource.{name,orn}` (MCP server), `authorizationServer`, `scopeCondition`, `scopes` |
| `STS_SERVICE_ACCOUNT` | `serviceAccount.{name,orn}`, `app.{name,orn}` |
| `STS_VAULT_SECRET` | `secret.{name,description,path,orn}` (Okta Privileged Access vaulted secret) |
| `STS_ACCESS_TOKEN` | `resource.resourceType` = `APP_INSTANCE` (`appInstanceId`, `appInstanceName`), `MCP_SERVER` (`mcpServerId`, `name`, `endpointUrl`) or `API_SERVER` (`apiServerId`, `name`, `resourceUrl`); plus `clientAuthSettings` |

`scopeCondition` is `ALL_SCOPES`, `INCLUDE_ONLY` or `EXCLUDE`; `scopes` lists the scopes the condition applies to. Potential connections (`list-potential-connections`) have the same shape without `id`, `orn`, `status`, `scopeCondition` and `scopes`.

### JWK object (`list-jwks` / `get-jwk`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta ID of the key record |
| `kid` | string | Key ID in the agent's JWKS |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `kty` | string | `RSA` (`n`, `e`) or `EC` (`crv` = `P-256`/`P-384`/`P-521`, `x`, `y`) |
| `alg` / `use` | string | Signing algorithm; `use` is always `sig` |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Operation object (`list-operations` / `get-operation`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Operation ID |
| `type` | string | e.g. `ai-agent:Register`, `ai-agent:Import`, `ai-agent:Staging`, `virtual-mcp:Register`, `virtual-mcp:ReplaceCapabilities` |
| `status` | string | `SCHEDULED`, `IN_PROGRESS`, `COMPLETED`, or `FAILED` |
| `resource.{id,type,status}` | object | Affected resource; `type` is `ai_agent` or `virtual_mcp` (available once the operation has progressed) |
| `errorDetails.{code,message}` | object | Present when `FAILED` |
| `operationMetadata` | object | Operation-specific details |
| `created` / `started` / `completed` | ISO 8601 string | Timestamps |

### Provider object (`list-providers` / `get-provider`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Provider ID |
| `sourceId` / `sourceName` / `sourceType` / `sourceOrn` | string | The integration source (app instance) |
| `status` | string | `ACTIVE`, `INACTIVE`, `REAUTHENTICATE`, or `REVALIDATE` |
| `schedule.{cron,timezone}` | object | Import schedule |
| `integrationDate` / `lastImportDate` / `nextScheduledImportDate` | ISO 8601 string | Import timeline |
| `importInProgress` | boolean | An import is queued or running |
| `stage` | string | Preview: `AUTO_MERGE`, `DUPLICATE`, or `NEWLY_IMPORTED` — how conflicting imports are handled |
| `deDupExpression` | string | Expression that decides when an imported agent matches an existing one |
| `owners.{groupOrn,userOrns}` | object | Resource owners |
| `_embedded.profileMapping.propertyMappings[]` | array | `{sourceExpression, targetField}`; present with `--expand profileMapping` |

`list-provider-priorities` items: `id` (source app instance), `providerId`, `priority` (lower wins), `enabledPlatforms`. `list-provider-stats` items: `providerId`, `agentCount`, `stagedAgentCount`, `mappedAttributeCount`. `get-provider-profile-mappings`: `propertyMappings[]` of `{sourceExpression, targetField}`. `get-provider-attributes` items: `name`, `type` (`string`/`integer`/`boolean`).

### Staging item (`list-provider-staging` / `get-provider-staging`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Staging item ID |
| `type` | string | `NEW`, `DUPLICATE`, or `IGNORED` |
| `incomingAgent` | object | Agent object as imported from the platform |
| `existingAgent` | object | Agent it collides with (`DUPLICATE`) |

`get-provider-staging-stats`: `newCount`, `duplicateCount`, `ignoredCount`. `get-provider-staging-review`: `matchingCriteria` (evaluated dedup expression), `incomingAgent` / `existingAgent` (`{agent, sourceId, sourcePriority}`), and `attributeDifferences[]` of `{attribute, incomingValue, existingValue, status}` where `status` is `MATCH` or `OVERWRITING` (incoming value would replace the existing one on merge).

### Delegation link (`list-delegation-links` / `get-delegation-link`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Delegation link ID |
| `from.type` | string | `OKTA_AUTHORIZATION_SERVER` (with `clientOrn`) or `SAML_APPLICATION` (with `appInstanceOrn`) |
| `from.tokenType` | string | `ACCESS_TOKEN`, `ID_TOKEN`, or `SAML_ASSERTION` |
| `to.resourceOrn` | string | Target resource |
| `to.authorizationServerOrn` | string | Authorization server for the target |
| `_embedded.{agentMetadata,appMetadata,customAuthorizationServerMetadata}` | object | Present with the matching `--expand` |

### Virtual MCP server (`list-virtual-mcp-servers` / `get-virtual-mcp-server`)

| Field | Type | Description |
|---|---|---|
| `id` / `orn` | string | Identifiers |
| `profile.displayName` / `profile.description` | string | Admin-editable profile |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

Virtual MCP connections (`list-virtual-mcp-connections`) are `STS_ACCESS_TOKEN` connection objects (see above).

### Virtual MCP capability (`list-virtual-mcp-capabilities` / `get-virtual-mcp-capability`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Capability ID |
| `type` | string | Capability type (e.g. tool) |
| `profile.name` / `profile.description` | string | As reported by the upstream MCP server |
| `profile.alias` | string | Admin-defined name exposed instead of `profile.name` |
| `status` | string | `VALID` or `INVALID` (no longer valid against the upstream server) |
| `connectionOrn` / `sourceOrn` | string | Owning connection and upstream source |
| `_embedded.inputSchema` | object | JSON Schema for inputs; present with `--input-schema` |

## Interpretation

### What to look for

- **Agent `status: STAGED`**: created but missing credentials or owners; it cannot act yet.
- **Agents with no connections** (`list-connections` empty) cannot reach any resource; agents with many `STS_*` or `ALL_SCOPES` connections have a wide blast radius — review `scopeCondition: ALL_SCOPES` and `EXCLUDE` first.
- **`STS_VAULT_SECRET` / `STS_SERVICE_ACCOUNT` connections** give the agent stored credentials rather than user-delegated access; confirm each is intended.
- **Connection `status: INACTIVE`** is configured but not usable.
- **Agents with no active JWK** (`list-jwks`) cannot authenticate with a signed assertion.
- **Operations `FAILED`**: read `errorDetails`; `resource.id` links back to the agent or virtual MCP server.
- **Provider `status` of `REAUTHENTICATE` / `REVALIDATE`**: imports from that platform are blocked until an admin re-authorizes. `importInProgress: true` with an old `lastImportDate` suggests a stuck import.
- **Staging backlog** (`get-provider-staging-stats` with high `duplicateCount`/`newCount`): imported agents are waiting on an admin; use `get-provider-staging-review` and look for `OVERWRITING` attributes before merging.
- **Capability `status: INVALID`**: the upstream MCP server removed or changed that tool.

### Cross-skill references

- `signOnProvider.appInstanceId`, `from.appInstanceOrn`, `appInstance.orn` → `okta-apps get <id>` (the id is the last ORN segment)
- `owners.userOrns`, `--owner-orn` user ORNs → `okta-users get <id>`; group ORNs → `okta-groups get <id>`
- `authorizationServer.orn` / `to.authorizationServerOrn` → `okta-authorization-servers get <id>`
- `oauthClient.clientId` / `from.clientOrn` → `okta-apps get <clientId>` for the OAuth client behind an agent
- Agent activity → `okta-logs list` filtered on the agent's ID or client ID
