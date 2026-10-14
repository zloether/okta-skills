# Spec Gap Report

Spec: `management-minimal.yaml`, `info.version` 2026.09.2 (485 paths; 288 non-deprecated GET operations). Previous backlog audit was against 2026.08.4.

**Refresh status:** the `curl` refresh was denied by the permission system (twice), not a network failure. This report uses the existing local copy (mtime 2026-10-14 17:04). It was not re-downloaded this session, so treat it as unverified-fresh.

**Method:** `scripts/diff-spec-coverage.py` (run with `uv run --with pyyaml`) plus keyword/scope scans of the spec. The tool maps GET operations to skills via the AGENTS.md inventory prefixes and the URLs each script calls. Result: 0 gaps inside existing skills; 32 unmapped tags / 87 unmapped GET operations. All 87 are already tracked in `BACKLOG.md` under "New skills to build" or "Not recommended", so nothing below is new except where marked **NEW**.

## 1. AI-agent-related surface

**Headline: the spec has no AI-agent features.** Searches (path, operationId, tag, summary, description, schema names, scope names) for `agent`, `ai`, `mcp`, `workload`, `a2a`, `agentic`, `non-human`, `ID-JAG`, `registry`, `aiAgent` found no AI-agent endpoints, tags, schemas or scopes. There is no agent registry, agent identity, MCP server, workload principal or agent-governance endpoint in 2026.09.2. If those APIs exist, they are not in `management-minimal.yaml`, so check the full `management.yaml` or a different spec before assuming a gap.

Every "agent" hit is unrelated to AI:

| Hit | Meaning | Covered? |
|---|---|---|
| Tag `AgentPools`, schemas `Agent`, `AgentPool`, `AgentPoolUpdate`, `AgentType`, `AgentUpdateInstanceStatus` | On-prem connector agents (AD/LDAP/RADIUS/IWA), not AI | No (see 2) |
| `POST /api/v1/directories/{appInstanceId}/groups/{groupId}/query` (`submitGroupAttributeQuery`) | AD agent group attribute query; write | No, write-only |
| `LogUserAgent` | HTTP user-agent in System Log | n/a |

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

## 2. Other uncovered GET operations (87 total, all in BACKLOG.md)

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

- The spec defines two security schemes, `apiToken` (SSWS) and `oauth2`, and 107 distinct OAuth scopes. No scope contains `agent` other than `okta.agentPools.{read,manage}`.
- Scopes needed for the adjacent non-human-identity GETs above that users should add to `OKTA_CLIENT_SCOPES` when these features are built:
  `okta.serviceAccounts.read`, `okta.serviceAccounts.okta.read`, `okta.principalRateLimits.read`, `okta.oauthIntegrations.read`, `okta.agentPools.read`.
- Already-used scopes relevant to non-human clients: `okta.apps.read` (CWO connections, federated claims), `okta.apps.interclientTrust.read`, `okta.appGrants.read`, `okta.roles.read` (OAuth client roles), `okta.users.read` (user client grants/tokens).
- Privileged Access service-account endpoints are under `/privileged-access/api/v1/...` (not `/api/v1`), so the skill inventory prefix in AGENTS.md must use that path for `diff-spec-coverage.py` to map them.
- Lifecycle: CWO connections are EA, interclient trust and privileged-access service accounts are Limited GA (`isGenerallyAvailable: false`); calls may 403/404 on orgs without the feature.

## Suggested next steps

1. Re-run the spec refresh (`curl` command in AGENTS.md) in an environment where it is permitted, then re-run `diff-spec-coverage.py` to confirm this report.
2. If AI-agent coverage is a priority, check the full `management.yaml` or Okta's AI-agent docs/spec separately: the minimal spec shows nothing.
3. Build `okta-service-accounts` and `okta-rate-limits` (principal-level) first; both are non-human-identity visibility.
