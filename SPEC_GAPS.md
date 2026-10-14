# Spec Gap Report

Specs audited (downloaded 2026-10-14 with `scripts/update-specs.py`):

| Spec | Version | GET operations |
|---|---|---|
| `management-minimal.yaml` | 2026.09.2 | 289 non-deprecated |
| `workload-principals.yaml` (Okta for AI Agents, Beta) | none declared | 28 |

**Method:** `scripts/diff-spec-coverage.py` (run with `uv run --with pyyaml`) maps spec GET operations to skills via the AGENTS.md inventory prefixes and the URLs each script calls. Result: 0 gaps inside existing skills; 42 unmapped tags / 115 unmapped GET operations (87 from the management spec, all already tracked in `BACKLOG.md`; 28 from the workload-principals spec, new in section 1).

## 1. AI-agent API: `workload-principals` spec (implemented in `okta-ai-agents`)

**Status 2026-10-14:** all 28 GETs are now implemented in `skills/okta-ai-agents/` (`ai_agents.py`); the table below records the operation-to-subcommand mapping. The access notes still apply.

The AI agent APIs are **not in the management spec**. They are published only in the Okta for AI Agents docs (`developer.okta.com/docs/api/secures-ai/`), as a separate OpenAPI bundle that `scripts/update-specs.py` now downloads (see AGENTS.md, "API Spec"). All paths are under `/workload-principals/api/v1/`.

**Access constraints:** Beta; the org needs an Okta for AI Agents subscription (calls will 403/404 otherwise); every operation requires the `SUPER_ADMIN` admin role. OAuth scopes: `okta.aiAgents.read` for agent endpoints, `okta.resourceServers.virtualMcpServers.read` for virtual MCP endpoints. These must be added to `OKTA_CLIENT_SCOPES` for PrivateKey auth.

One skill, `okta-ai-agents`, covers agents, connections, providers, delegation links and virtual MCP servers, since they share a prefix and connection model.

| Area | Method + path | operationId | Suggested subcommand |
|---|---|---|---|
| Agents | `GET /ai-agents` | `listAIAgents` | `list` |
| | `GET /ai-agents/{agentId}` | `getAIAgent` | `get` |
| | `GET /ai-agents/schema/default` | `getAIAgentSchema` | `get-schema` |
| | `GET /ai-agents/provider-attributes/{providerName}` | `getAIAgentProviderAttributes` | `get-provider-attributes` |
| Connections | `GET /ai-agents/{agentId}/connections` | `listConnections` | `list-connections` |
| | `GET /ai-agents/{agentId}/connections/{connectionId}` | `getResourceConnection` | `get-connection` |
| Credentials | `GET /ai-agents/{agentId}/credentials/jwks` | `listAgentJwk` | `list-jwks` |
| | `GET /ai-agents/{agentId}/credentials/jwks/{keyId}` | `getAgentJwk` | `get-jwk` |
| Potential connections | `GET /potential-connections` (`filter` required, `match` optional) | `listPotentialConnectionsByType` | `list-potential-connections` |
| Operations | `GET /operations` | `listWorkloadPrincipalOperations` | `list-operations` |
| | `GET /operations/{operationId}` | `getWorkloadPrincipalOperation` | `get-operation` |
| Providers | `GET /ai-agent-providers` | `listAIAgentProviders` | `list-providers` |
| | `GET /ai-agent-providers/{providerId}` | `getAIAgentProvider` | `get-provider` |
| | `GET /ai-agent-providers/priorities` | `listAIAgentProviderSourcePriorities` | `list-provider-priorities` |
| | `GET /ai-agent-providers/stats` | `listAIAgentProviderStats` | `list-provider-stats` |
| | `GET /ai-agent-providers/{providerId}/profile-mappings` | `getAIAgentProviderProfileMapping` | `get-provider-profile-mappings` |
| Provider staging | `GET /ai-agent-providers/{providerId}/staging` | `listAIAgentProviderStaging` | `list-provider-staging` |
| | `GET /ai-agent-providers/{providerId}/staging/stats` | `getAIAgentProviderStagingStats` | `get-provider-staging-stats` |
| | `GET /ai-agent-providers/{providerId}/staging/{id}` | `getAIAgentProviderStaging` | `get-provider-staging` |
| | `GET /ai-agent-providers/{providerId}/staging/{id}/review` | `getAIAgentProviderStagingReview` | `get-provider-staging-review` |
| Delegation links | `GET /delegation-links` (`filter`, AND/OR with parentheses) | `listDelegationLinks` | `list-delegation-links` |
| | `GET /delegation-links/{delegationLinkId}` | `getDelegationLink` | `get-delegation-link` |
| Virtual MCP servers | `GET /virtual-mcp-servers` | `listVirtualMCPs` | `list-virtual-mcp-servers` |
| | `GET /virtual-mcp-servers/{virtualMcpServerId}` | `getVirtualMCP` | `get-virtual-mcp-server` |
| | `GET /virtual-mcp-servers/{id}/connections` | `listVirtualMCPConnections` | `list-virtual-mcp-connections` |
| | `GET /virtual-mcp-servers/{id}/connections/{connectionId}` | `getVirtualMCPConnection` | `get-virtual-mcp-connection` |
| | `GET /virtual-mcp-servers/{id}/connections/{connectionId}/capabilities` (`expand=inputSchema`) | `listVirtualMCPConnectionCapabilities` | `list-virtual-mcp-capabilities` |
| | `GET /virtual-mcp-servers/{id}/connections/{connectionId}/capabilities/{capabilityId}` | `getVirtualMCPConnectionCapability` | `get-virtual-mcp-capability` |

Connection types (for SKILL.md Output Schema): `IDENTITY_ASSERTION_CUSTOM_AS`, `IDENTITY_ASSERTION_APP_INSTANCE`, `IDENTITY_ASSERTION_A2A_SERVER`, `STS_SERVICE_ACCOUNT`, `STS_VAULT_SECRET`, `STS_ACCESS_TOKEN`, `MCP_SERVER`. Verify field-level schemas against `workload-principals.yaml` when implementing; this table was built from operation metadata only.

Write-only operations in this spec (~30 POST/PUT/PATCH/DELETE: register/replace/update/delete agents, activate/deactivate, create connections, add/remove JWKs, import and staging actions, providers CRUD, delegation links create/delete, virtual MCP CRUD) are out of scope for this read-only repo.

Remaining "agent" hits in the management spec are unrelated to AI: on-prem connector agents (tag `AgentPools`, uncovered, see section 2), the AD group attribute query (`submitGroupAttributeQuery`, write), and `LogUserAgent`.

### Adjacent areas relevant to agents and non-human identities

These cover how a non-human client (service app, agent) authenticates, is authorized, and is audited. Coverage is mostly good already.

| Area | GET operations | Covered by | Gap |
|---|---|---|---|
| Cross App Access (CWO), app-to-app delegation | `GET /api/v1/apps/{appId}/cwo/connections` (`getAllCrossAppAccessConnections`), `.../{connectionId}` (`getCrossAppAccessConnection`), EA | `okta-apps list-cwo-connections` / `get-cwo-connection` | none |
| Federated claims | `GET /api/v1/apps/{appId}/federated-claims[/{claimId}]` | `okta-apps` | none |
| Interclient trust | `GET .../interclient-allowed-apps`, `.../interclient-target-apps` (Limited GA) | `okta-apps` | none |
| App scope consent grants | `GET /api/v1/apps/{appId}/grants[/{grantId}]` | `okta-apps` | none |
| OAuth client admin roles | `GET /oauth2/v1/clients/{clientId}/roles...` (4 ops) | `okta-oauth-client-roles` | none |
| User-granted client consents/tokens | `GET /api/v1/users/{userId}/clients/...`, `/grants...` | `okta-users` | none |
| OAuth token exchange | grant type `urn:ietf:params:oauth:grant-type:token-exchange` appears in app schema enums (line ~69642) | schema only | no endpoint; mention in apps SKILL.md if not already |
| **NEW** Okta Privileged Access service accounts | see table below | none | uncovered |
| **NEW** Principal rate limits (per `SSWS_TOKEN` / `OAUTH_CLIENT` principal) | see table below | none | uncovered |
| API Service Integrations (OIN) | see table below | none | uncovered |

Agent-related write-only areas (context only, not implementable): `POST/PATCH/DELETE` on `/privileged-access/api/v1/service-accounts` and `/okta-service-accounts` (scopes `okta.serviceAccounts.manage` / `okta.serviceAccounts.okta.manage`), CWO connection create/update/delete, federated-claim create/replace/delete, interclient trust create/delete, `POST/PUT /api/v1/principal-rate-limits`, API service integration create/delete and secret create/activate/deactivate.

### Highest-value uncovered GETs for non-human identity visibility

| Method + path | operationId | Suggested subcommand | Suggested skill | Lifecycle / scope |
|---|---|---|---|---|
| `GET /privileged-access/api/v1/service-accounts` | `listAppServiceAccounts` | `list-app-service-accounts` | new `okta-service-accounts` | Limited GA; `okta.serviceAccounts.read` |
| `GET /privileged-access/api/v1/service-accounts/{id}` | `getAppServiceAccount` | `get-app-service-account` | new `okta-service-accounts` | same |
| `GET /privileged-access/api/v1/okta-service-accounts` | `listOktaManagedUserAccounts` | `list-okta-service-accounts` | new `okta-service-accounts` | Limited GA; `okta.serviceAccounts.okta.read` |
| `GET /privileged-access/api/v1/okta-service-accounts/{id}` | `getOktaManagedUserAccount` | `get-okta-service-account` | new `okta-service-accounts` | same |
| `GET /api/v1/principal-rate-limits` | `listPrincipalRateLimitEntities` | `list-principal-rate-limits` | new `okta-rate-limits` | GA; `okta.principalRateLimits.read`; supports `filter=principalType eq "OAUTH_CLIENT"` |
| `GET /api/v1/principal-rate-limits/{principalRateLimitId}` | `getPrincipalRateLimitEntity` | `get-principal-rate-limit` | new `okta-rate-limits` | same |
| `GET /integrations/api/v1/api-services` | `listApiServiceIntegrationInstances` | `list-api-services` | new `okta-api-services` (or `okta-apps`) | GA; `okta.oauthIntegrations.read` |
| `GET /integrations/api/v1/api-services/{apiServiceId}` | `getApiServiceIntegrationInstance` | `get-api-service` | same | same |
| `GET /integrations/api/v1/api-services/{apiServiceId}/credentials/secrets` | `listApiServiceIntegrationInstanceSecrets` | `list-api-service-secrets` | same | same |

BACKLOG.md currently marks `/integrations/api/v1/api-services` as "Not recommended" (ISV-only). It is the only place an OAuth service client's secrets are enumerable for an installed integration, so reconsider if non-human identity audit is a goal.

## 2. Other uncovered GET operations (management spec: 87 total, all in BACKLOG.md)

| Area (spec tag) | Count | GET paths | Suggested skill |
|---|---|---|---|
| Hooks (EventHook, InlineHook, HookKey) | 7 | `/api/v1/eventHooks[/{id}]`, `/api/v1/inlineHooks[/{id}]`, `/api/v1/hook-keys[/{id}]`, `/api/v1/hook-keys/public/{keyId}` | new `okta-hooks` |
| Brands, Themes, CustomPages, CustomTemplates, AssociatedDomainCustomizations | 3 + 2 + 10 + 8 + 3 | `/api/v1/brands...` incl. pages, themes, email templates, well-known-uris | new `okta-brands` (large; consider read-only listing plus `get`) |
| Domains / Email (CustomDomain, EmailDomain, EmailServer) | 6 | `/api/v1/domains`, `/api/v1/email-domains`, `/api/v1/email-servers` (+ `{id}`) | new `okta-domains` |
| Features | 4 | `/api/v1/features[/{id}]`, `.../dependencies`, `.../dependents` | new `okta-features` or `okta-org-settings` |
| LogStream | 2 | `/api/v1/logStreams[/{id}]` | `okta-schemas` already has log-stream schemas; add to `okta-logs` |
| TrustedOrigin | 2 | `/api/v1/trustedOrigins[/{id}]` | `okta-org-settings` |
| AgentPools (on-prem agents) | 4 | `/api/v1/agentPools`, `.../updates`, `.../updates/settings`, `.../updates/{updateId}` | new `okta-agent-pools` (scope `okta.agentPools.read`) |
| RateLimitSettings | 3 | `/api/v1/rate-limit-settings/{admin-notifications,per-client,warning-threshold}` | with principal rate limits (`okta-rate-limits`) |
| PushProvider, CustomTelephonyProvider, Template (SMS) | 2 + 2 + 2 | `/api/v1/push-providers`, `/api/v1/telephony-providers` (EA), `/api/v1/templates/sms` | `okta-authenticators` or new `okta-messaging` |
| CAPTCHA | 2 | `/api/v1/captchas[/{id}]` (Limited GA) | `okta-org-settings` (already has `get-captcha-settings`) |
| DisasterRecovery | 2 | `/api/v1/dr/status[/{domain}]` (EA) | `okta-org-settings` |
| OktaApplicationSettings | 1 | `/api/v1/first-party-app-settings/{appName}` | `okta-org-settings` |
| WebAuthnPreregistration | 1 | `/webauthn-registration/api/v1/users/{userId}/enrollments` (Limited GA) | `okta-authenticators` |
| IdentitySource | 5 | `/api/v1/identity-sources/{id}/{groups,sessions,users}...` | not recommended (needs known ID) |
| DirectoriesIntegration | 1 | `/api/v1/directories/{appInstanceId}/groups/{groupId}/query/{resultId}` | not recommended |
| Public `.well-known` (OrgSettingMetadata, SSFTransmitter, Authenticator, AssociatedDomain x3) | 6 | `/.well-known/*` | not recommended (unauthenticated) |
| Privileged Access service accounts | 4 | covered in section 1 | new `okta-service-accounts` |
| API Service Integrations | 3 | covered in section 1 | see section 1 |
| PrincipalRateLimit | 2 | covered in section 1 | see section 1 |

Counts are approximate groupings of the tool's 87-operation output.

## 3. Drift in implemented endpoints

- Every URL template called from `skills/*/scripts/*.py` (151 distinct normalized paths) exists in the spec as a GET. None are removed or non-GET.
- The only deprecated GET in the spec is `GET /api/v1/policies/{policyId}/app` (`listPolicyApps`); it is intentionally not implemented (replaced by `list-mappings`).
- No new in-prefix GETs appeared since the 2026-09-11 audit (diff tool reports 0 gaps in existing skills).
- Not checked (needs a manual pass): parameter-level changes since 2026.08.4 (new or renamed query params, enum changes). The diff tool only compares operations, not parameters.

## 4. Scope and auth notes

- The management spec defines two security schemes, `apiToken` (SSWS) and `oauth2`, and 107 distinct OAuth scopes. No scope contains `agent` other than `okta.agentPools.{read,manage}`. The workload-principals spec adds `okta.aiAgents.{read,manage}` and `okta.resourceServers.virtualMcpServers.{read,manage}`, plus an internal-only `ephemeralJwt` scheme to ignore.
- Scopes to add to `OKTA_CLIENT_SCOPES` when these features are built:
  `okta.aiAgents.read`, `okta.resourceServers.virtualMcpServers.read`, `okta.serviceAccounts.read`, `okta.serviceAccounts.okta.read`, `okta.principalRateLimits.read`, `okta.oauthIntegrations.read`, `okta.agentPools.read`.
- Already-used scopes relevant to non-human clients: `okta.apps.read` (CWO connections, federated claims), `okta.apps.interclientTrust.read`, `okta.appGrants.read`, `okta.roles.read` (OAuth client roles), `okta.users.read` (user client grants/tokens).
- Privileged Access service-account endpoints are under `/privileged-access/api/v1/...` (not `/api/v1`), so the skill inventory prefix in AGENTS.md must use that path for `diff-spec-coverage.py` to map them.
- Lifecycle: CWO connections are EA, interclient trust and privileged-access service accounts are Limited GA (`isGenerallyAvailable: false`); calls may 403/404 on orgs without the feature.

## Suggested next steps

1. ~~Build `okta-ai-agents`~~ — done 2026-10-14 (28 GETs).
2. Build `okta-service-accounts` and `okta-rate-limits` (principal-level) next; both are non-human-identity visibility.
3. Re-run `scripts/update-specs.py` and `scripts/diff-spec-coverage.py` periodically; the AI agents API is Beta and its paths may change.
