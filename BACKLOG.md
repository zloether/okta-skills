# Okta Skills Backlog

> Audited against `management-minimal.yaml` on 2026-07-19; re-audited 2026-08-15 for new/missing GET operations and for full query-parameter and lifecycle-label parity across all 22 skills. All parameter/coverage gaps identified in the 2026-08-15 audit (apps, groups, policies, network-zones, devices, users, schemas, org-settings, logs) have since been implemented and verified.
> Only HTTP GET operations are listed. Lifecycle notes: **⚠️ Limited GA** = `isGenerallyAvailable: false` or `lifecycle: LIMITED_GA`; **⚠️ EA** = `lifecycle: EA`.

---

## Gaps in existing skills

### okta-apps

**Parameter gaps fixed 2026-08-15:** `list` now sends `q`, `expand`, `useOptimization`, `alwaysIncludeVpnSettings`, `includeNonDeleted` in addition to `filter`/`limit`. `get`, `get-group`, `get-user` now send `expand`. `get-users`/`get-groups` now send `q`, `expand`, and respect `--limit`. `list-cwo-connections` now sends `status`, `requestingAppId`, `resourceAppId`, `activeAppsOnly`, `requestingAppName`, `resourceAppName`. `list-group-push-mappings` now sends `lastUpdated`, `sourceGroupId`, `status`. `list-grants`/`get-grant`/`list-tokens`/`get-token` now send `expand`. Full parameter parity with spec achieved; no remaining gaps.

Lifecycle drift (fixed 2026-08-15): `list-interclient-allowed-apps`/`list-interclient-target-apps` were labeled "(EA)"/"Early Access" in both `apps.py`'s argparse help text and `SKILL.md`; the spec marks both `listInterclientAllowedApplications` and `listInterclientTargetApplications` as ⚠️ Limited GA (`lifecycle: LIMITED_GA, isGenerallyAvailable: false`). Both files corrected.

### okta-groups

**Parameter gaps fixed 2026-08-15:** `list` now sends `q` (added to the existing `--filter`/`--search` mutually exclusive group), `expand`, `sortBy`, `sortOrder`. `get-members`, `get-apps` now respect `--limit`. `get-owners` now sends `search` and respects `--limit`. `list-rules` now sends `expand`. `list-roles` now sends `expand`. `list-role-app-targets`/`list-role-group-targets` now respect `--limit`. Full parameter parity with spec achieved; no remaining gaps. `--q`'s help text notes it disables pagination and caps at 300 results per spec.

No lifecycle drift found — every implemented operation is `lifecycle: GA, isGenerallyAvailable: true` and SKILL.md makes no contradicting claims.

### okta-policies

Currently implements: all non-deprecated GET endpoints in spec for this path. `GET /api/v1/policies/{policyId}/app` (`listPolicyApps`) is intentionally not implemented — confirmed still `deprecated: true` in the spec in favor of `listPolicyMappings` (`list-mappings`), which is implemented. **Parameter gap fixed 2026-08-15:** `list` now sends `status`, `q`, `expand`, `sortBy`, `resourceId` in addition to `type`. `get` now sends `expand`. Full parameter parity with spec achieved; no remaining gaps. No lifecycle drift found.

### okta-device-posture

Currently implements: all GET endpoints in spec for this path. No gaps. Lifecycle labels corrected 2026-08-15 in `SKILL.md`: `list`, `list-defaults`, and `get` (`listDevicePostureChecks`, `listDefaultDevicePostureChecks`, `getDevicePostureCheck`) are all now labeled ⚠️ Limited GA (`isGenerallyAvailable: false`) — `get` previously and incorrectly claimed no lifecycle restriction.

---

### okta-network-zones

Currently implements: `GET /api/v1/zones`, `GET /api/v1/zones/{id}`. Fully covers all GET endpoints in spec for this path. **Parameter gap fixed 2026-08-15:** `list` now exposes `--limit`, plus `--usage` and `--system` as mutually-exclusive alternatives to `--type` (all three build the same `filter` param). `--type`'s help text retains a caveat that the spec's filtering description lists `id`/`usage`/`system`, not `type` — worth a live check before trusting `--type` filtering, but the CLI option itself is no longer missing. `--system` uses a validating argparse type that rejects any value other than `true`/`false` (case-insensitive) instead of silently treating typos as `false`.

---

### okta-device-assurance

Currently implements: `GET /api/v1/device-assurances`, `GET /api/v1/device-assurances/{id}`. Fully covers all GET endpoints in spec for this path. No gaps.

---

### okta-logs

Currently implements: `GET /api/v1/logs`. Fully covers all GET endpoints in spec for this path. `list` exposes the full `listLogEvents` parameter surface (`since`, `until`, `filter`, `q`, `sortOrder`, `limit`) — no gaps there. **Parameter gap fixed 2026-08-15:** `login-failures` now also sends `q` and `sortOrder` alongside its hardcoded filter. Full parameter parity with spec achieved; no remaining gaps. No lifecycle drift (GA).

---

### okta-api-tokens

Currently implements: `GET /api/v1/api-tokens`, `GET /api/v1/api-tokens/{apiTokenId}`. Fully covers all GET endpoints in spec for this path. No gaps.

---

### okta-sessions

Currently implements: `GET /api/v1/sessions/{sessionId}`. Fully covers all GET endpoints in spec for this path (session IDs are not enumerable; there is no `list`). No gaps.

---

### okta-iam

Currently implements: all GET endpoints in spec for `/api/v1/iam` and `/api/v1/roles/{roleRef}/subscriptions`. No gaps. Note: `list-bundles`, `get-bundle`, `list-bundle-entitlements`, `list-bundle-entitlement-values`, and `get-opt-in-status` (governance bundle endpoints) are ⚠️ Limited GA.

---

### okta-authenticators

Currently implements: all GET endpoints in spec for this path. No gaps. Note: all six endpoints are ⚠️ Limited GA (`isGenerallyAvailable: false`) per the spec, including `listAllCustomAAGUIDs`/`getCustomAAGUID` which weren't marked with the ⚠️ symbol above when this backlog was first audited.

---

### okta-behaviors

Currently implements: `GET /api/v1/behaviors`, `GET /api/v1/behaviors/{behaviorId}`. Fully covers all GET endpoints in spec for this path. No gaps.

---

### okta-devices

Currently implements: `list`, `get`, `get-users`, `get-os-accounts`, `get-os-account`. **Gap fixed 2026-08-15:** added `get-os-accounts <device_id>` / `get-os-account <device_id> <os_account_id>` subcommands for `GET /api/v1/devices/{deviceId}/os-accounts` (`listDeviceOSAccounts`) and `GET /api/v1/devices/{deviceId}/os-accounts/{osAccountId}` (`getDeviceOSAccount`) — both ⚠️ Limited GA (`lifecycle: EA`, `isGenerallyAvailable: false`), each accepting an `expand` query param. **Parameter gap fixed 2026-08-15:** `list` now exposes `listDevices`'s `expand` param (`user`/`userSummary`). Full parameter/coverage parity with spec achieved; no remaining gaps. No lifecycle drift found on the implemented subcommands (`list`/`get`/`get-users` are all ⚠️ Limited GA per spec; SKILL.md makes no lifecycle claim to contradict this).

---

### okta-users

Currently implements: all GET endpoints in spec for this path. **Parameter gaps fixed 2026-08-15:** `list` now sends `search`, `q`, `sortBy`, `sortOrder`, `fields`, `expand` in addition to `filter`/`limit`. `get` now sends `expand`. `get-enrollments`/`get-enrollment` now send `discloseIdentifiers`. `get-grants`/`get-grant` and `get-roles` now send `expand`. Full parameter parity with spec achieved; no remaining gaps. `--filter`/`--search`/`--q` on `list` are mutually exclusive (matching `okta-groups`); `--q`'s help text notes it disables pagination and caps at 10 results per spec.

No genuine lifecycle drift found. `get-role-governance`/`get-role-governance-grant`/`get-role-governance-grant-resources` are labeled "Limited GA" in both `SKILL.md` and argparse help; the spec's literal `x-okta-lifecycle.lifecycle` enum on all three is actually `GA` (not `LIMITED_GA`), but `isGenerallyAvailable: false` holds, so the label is correct per this backlog's own convention (⚠️ Limited GA = `isGenerallyAvailable: false` OR `lifecycle: LIMITED_GA`) — noted here for awareness, not as an action item.

---

### okta-authorization-servers

Currently implements: all GET endpoints in spec for this path. No gaps.

---

### okta-identity-providers

Currently implements: all GET endpoints in spec for this path. No gaps.

---

### okta-schemas

Currently implements: all GET endpoints in spec for `/api/v1/mappings` and `/api/v1/meta` (schemas, types, uischemas, linkedObjects, logStream). No coverage gaps. **Parameter gap fixed 2026-08-15:** `list` (`listProfileMappings`, `/api/v1/mappings`) now exposes `--limit`. Full parameter parity with spec achieved; no remaining gaps. Note: `/api/v1/meta/layouts/apps/{appName}` and its `sections/{section}/{operation}` sub-path have no HTTP methods defined in the spec at all (path parameters only), so there is nothing to implement there. Newly-noted lifecycle: `list-ui-schemas`/`get-ui-schema` (`/api/v1/meta/uischemas`) are ⚠️ Limited GA (`lifecycle: LIMITED_GA`, SKU: Okta Identity Engine) — this backlog didn't call it out, but the skill's own `SKILL.md` already labels both correctly, so no drift/fix needed there.

---

### okta-security

Currently implements: all GET endpoints in spec for `/api/v1/threats`, `/api/v1/security-events-providers`, `/api/v1/ssf`, `/api/v1/bot-protection`. No gaps. Note: `/api/v1/ssf/stream/verification` is POST-only (no GET), so there is nothing to implement there. Newly-noted lifecycle: most of this skill's surface is ⚠️ Limited GA — `list-security-events-providers`/`get-security-events-provider`, `get-ssf-streams`, `get-ssf-stream-status`, and `get-bot-protection-config` are all `lifecycle: LIMITED_GA`; only `get-threat-insight-config` is full GA. This backlog didn't call it out, but the skill's own `SKILL.md` already labels all four correctly, so no drift/fix needed there.

---

### okta-attack-protection

Currently implements: `GET /attack-protection/api/v1/authenticator-settings`, `GET /attack-protection/api/v1/user-lockout-settings`. Fully covers all GET endpoints in spec for this path. No gaps. Note: `get-authenticator-settings` is ⚠️ Limited GA (`isGenerallyAvailable: false`); `get-user-lockout-settings` has no lifecycle restriction.

---

### okta-device-integrations

Currently implements: `GET /api/v1/device-integrations`, `GET /api/v1/device-integrations/{deviceIntegrationId}`. Fully covers all GET endpoints in spec for this path. No gaps. Note: both endpoints are ⚠️ Limited GA (`isGenerallyAvailable: false`).

---

### okta-org-settings

Currently implements: `GET /api/v1/org`, `GET /api/v1/org/contacts`, `GET /api/v1/org/contacts/{contactType}`, `GET /api/v1/org/captcha`, `GET /api/v1/org/orgSettings/thirdPartyAdminSetting`, `GET /api/v1/org/preferences`, `GET /api/v1/org/privacy/aerial`, `GET /api/v1/org/privacy/oktaCommunication`, `GET /api/v1/org/privacy/oktaSupport`, `GET /api/v1/org/privacy/oktaSupport/cases`, `GET /api/v1/org/settings/autoAssignAdminAppSetting`, `GET /api/v1/org/settings/clientPrivilegesSetting`, `GET /api/v1/org/factors/yubikey_token/tokens`, `GET /api/v1/org/factors/yubikey_token/tokens/{tokenId}`. Fully covers all GET endpoints in spec for this path. No coverage gaps. Note: `get-captcha-settings` is ⚠️ Limited GA (`isGenerallyAvailable: false`); all others have no lifecycle restriction. **Parameter gap fixed 2026-08-15:** `list-yubikey-tokens` now also sends `sortBy`/`sortOrder` (via `--sort-by`/`--sort-order`) in addition to `--filter`/`--limit`/`--expand-user`. `forDownload` is intentionally not exposed: the spec documents it as switching the response to CSV, but every fetch helper in `shared/okta_client.py` unconditionally calls `resp.json()`, so `--for-download` would crash on every use — not implementable without adding non-JSON response handling that no other command needs. Full parameter parity with spec achieved (within the tool's all-JSON-output contract); no remaining gaps.

---

### okta-realms

Currently implements: `GET /api/v1/realms`, `GET /api/v1/realms/{realmId}`, `GET /api/v1/realm-assignments`, `GET /api/v1/realm-assignments/{assignmentId}`, `GET /api/v1/realm-assignments/operations`. Fully covers all GET endpoints in spec for this path. All operations are GA, no lifecycle drift. `list-realms`/`list-realm-assignments`/`list-realm-assignment-operations` don't expose `after` (low impact — `paginated_get`'s Link-header following handles pagination automatically). **Bug fixed 2026-08-15:** all three `list-*` subcommands accepted `--limit` but never forwarded it to the API as a query parameter (`paginated_get` was called without a `params` dict containing `limit`), so it only truncated client-side after the full result set was already fetched. Fixed in `realms.py` to set `params['limit']` matching the pattern used elsewhere in the codebase (e.g. `okta-users`).

---

## New skills to build

### Hooks (`/api/v1/eventHooks`, `/api/v1/inlineHooks`, `/api/v1/hook-keys`)

Useful for auditing what automation and integrations are active.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/eventHooks` | `listEventHooks` | List all event hooks |
| `GET /api/v1/eventHooks/{eventHookId}` | `getEventHook` | Retrieve a specific event hook |
| `GET /api/v1/inlineHooks` | `listInlineHooks` | List all inline hooks |
| `GET /api/v1/inlineHooks/{inlineHookId}` | `getInlineHook` | Retrieve a specific inline hook |
| `GET /api/v1/hook-keys` | `listHookKeys` | List all hook signing keys |
| `GET /api/v1/hook-keys/{id}` | `getHookKey` | Retrieve a specific hook key by ID |
| `GET /api/v1/hook-keys/public/{keyId}` | `getPublicKey` | Retrieve a hook key's public component |

---

### Branding & Customization (`/api/v1/brands`)

Useful for reporting on the org's UI customization state.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/brands` | `listBrands` | List all brands |
| `GET /api/v1/brands/{brandId}` | `getBrand` | Retrieve a specific brand |
| `GET /api/v1/brands/{brandId}/domains` | `listBrandDomains` | List all domains associated with a brand |
| `GET /api/v1/brands/{brandId}/themes` | `listBrandThemes` | List all themes for a brand |
| `GET /api/v1/brands/{brandId}/themes/{themeId}` | `getBrandTheme` | Retrieve a specific brand theme |
| `GET /api/v1/brands/{brandId}/pages/sign-in` | `getSignInPage` | Retrieve the sign-in page sub-resources |
| `GET /api/v1/brands/{brandId}/pages/sign-in/customized` | `getCustomizedSignInPage` | Retrieve the customized sign-in page |
| `GET /api/v1/brands/{brandId}/pages/sign-in/default` | `getDefaultSignInPage` | Retrieve the default sign-in page |
| `GET /api/v1/brands/{brandId}/pages/sign-in/preview` | `getPreviewSignInPage` | Retrieve a preview of the sign-in page (new since last audit) |
| `GET /api/v1/brands/{brandId}/pages/sign-in/widget-versions` | `listAllSignInWidgetVersions` | List all sign-in widget versions available to a brand (new since last audit) |
| `GET /api/v1/brands/{brandId}/pages/error` | `getErrorPage` | Retrieve the error page sub-resources (new since last audit) |
| `GET /api/v1/brands/{brandId}/pages/error/customized` | `getCustomizedErrorPage` | Retrieve the customized error page |
| `GET /api/v1/brands/{brandId}/pages/error/default` | `getDefaultErrorPage` | Retrieve the default error page |
| `GET /api/v1/brands/{brandId}/pages/error/preview` | `getPreviewErrorPage` | Retrieve a preview of the error page (new since last audit) |
| `GET /api/v1/brands/{brandId}/pages/sign-out/customized` | `getSignOutPageSettings` | Retrieve the sign-out page settings |
| `GET /api/v1/brands/{brandId}/templates/email` | `listEmailTemplates` | List all email templates for a brand |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}` | `getEmailTemplate` | Retrieve a specific email template |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/customizations` | `listEmailCustomizations` | List all email customizations for a template |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/customizations/{customizationId}` | `getEmailCustomization` | Retrieve a specific email customization |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/customizations/{customizationId}/preview` | `getCustomizationPreview` | Retrieve a preview of an email customization (new since last audit) |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/default-content` | `getEmailDefaultContent` | Retrieve the default content of an email template |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/default-content/preview` | `getEmailDefaultPreview` | Retrieve a preview of the default email content (new since last audit) |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/settings` | `getEmailSettings` | Retrieve the settings for an email template |
| `GET /api/v1/brands/{brandId}/well-known-uris` | `getAllWellKnownURIs` | Retrieve all well-known URIs for a brand ⚠️ Limited GA |
| `GET /api/v1/brands/{brandId}/well-known-uris/{path}` | `getRootBrandWellKnownURI` | Retrieve a specific brand well-known URI ⚠️ Limited GA |
| `GET /api/v1/brands/{brandId}/well-known-uris/{path}/customized` | `getBrandWellKnownURI` | Retrieve the customized content of a well-known URI ⚠️ Limited GA |

---

### Custom Domains & Email Infrastructure (`/api/v1/domains`, `/api/v1/email-domains`, `/api/v1/email-servers`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/domains` | `listCustomDomains` | List all custom domains configured in the org |
| `GET /api/v1/domains/{domainId}` | `getCustomDomain` | Retrieve a specific custom domain |
| `GET /api/v1/email-domains` | `listEmailDomains` | List all email domains |
| `GET /api/v1/email-domains/{emailDomainId}` | `getEmailDomain` | Retrieve a specific email domain |
| `GET /api/v1/email-servers` | `listEmailServers` | List all enrolled SMTP servers |
| `GET /api/v1/email-servers/{emailServerId}` | `getEmailServer` | Retrieve a specific SMTP server configuration |

---

### Features (`/api/v1/features`)

Useful for reporting which self-service features are enabled in the org.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/features` | `listFeatures` | List all self-service features for the org |
| `GET /api/v1/features/{featureId}` | `getFeature` | Retrieve a specific feature by ID |
| `GET /api/v1/features/{featureId}/dependencies` | `listFeatureDependencies` | List all features that must be enabled before this one |
| `GET /api/v1/features/{featureId}/dependents` | `listFeatureDependents` | List all features that depend on this one |

---

### Log Streams (`/api/v1/logStreams`)

Useful for auditing where system log data is being forwarded.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/logStreams` | `listLogStreams` | List all log streams |
| `GET /api/v1/logStreams/{logStreamId}` | `getLogStream` | Retrieve a specific log stream |

---

### Trusted Origins (`/api/v1/trustedOrigins`)

Useful for auditing CORS and redirect allow-listing.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/trustedOrigins` | `listTrustedOrigins` | List all trusted origins |
| `GET /api/v1/trustedOrigins/{trustedOriginId}` | `getTrustedOrigin` | Retrieve a specific trusted origin |

---

### Agent Pools (`/api/v1/agentPools`)

Useful for orgs using on-premises connectors (AD, LDAP, RADIUS).

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/agentPools` | `listAgentPools` | List all agent pools |
| `GET /api/v1/agentPools/{poolId}/updates` | `listAgentPoolsUpdates` | List all updates for an agent pool |
| `GET /api/v1/agentPools/{poolId}/updates/settings` | `getAgentPoolsUpdateSettings` | Retrieve the update settings for an agent pool |
| `GET /api/v1/agentPools/{poolId}/updates/{updateId}` | `getAgentPoolsUpdateInstance` | Retrieve a specific agent pool update by ID |

---

### Rate Limit Settings (`/api/v1/rate-limit-settings`, `/api/v1/principal-rate-limits`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/rate-limit-settings/admin-notifications` | `getRateLimitSettingsAdminNotifications` | Retrieve the rate limit admin notification settings |
| `GET /api/v1/rate-limit-settings/per-client` | `getRateLimitSettingsPerClient` | Retrieve the per-client rate limit settings |
| `GET /api/v1/rate-limit-settings/warning-threshold` | `getRateLimitSettingsWarningThreshold` | Retrieve the rate limit warning threshold percentage |
| `GET /api/v1/principal-rate-limits` | `listPrincipalRateLimitEntities` | List all principal-level rate limit overrides |
| `GET /api/v1/principal-rate-limits/{principalRateLimitId}` | `getPrincipalRateLimitEntity` | Retrieve a specific principal rate limit |

---

### Push Providers & Telephony (`/api/v1/push-providers`, `/api/v1/telephony-providers`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/push-providers` | `listPushProviders` | List all custom push notification providers |
| `GET /api/v1/push-providers/{pushProviderId}` | `getPushProvider` | Retrieve a specific push provider |
| `GET /api/v1/telephony-providers` | `listAllCustomTelephonyProviderCredentials` | List all custom telephony providers ⚠️ EA |
| `GET /api/v1/telephony-providers/{customTelephonyProviderId}` | `getCustomTelephonyProviderCredential` | Retrieve a specific custom telephony provider ⚠️ EA |

---

### CAPTCHA (`/api/v1/captchas`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/captchas` | `listCaptchaInstances` | List all CAPTCHA instances configured in the org ⚠️ Limited GA |
| `GET /api/v1/captchas/{captchaId}` | `getCaptchaInstance` | Retrieve a specific CAPTCHA instance ⚠️ Limited GA |

---

### SMS Templates (`/api/v1/templates/sms`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/templates/sms` | `listSmsTemplates` | List all SMS templates |
| `GET /api/v1/templates/sms/{templateId}` | `getSmsTemplate` | Retrieve a specific SMS template |

---

### First-Party App Settings (`/api/v1/first-party-app-settings`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/first-party-app-settings/{appName}` | `getFirstPartyAppSettings` | Retrieve settings for a named Okta first-party app (e.g., the Admin Console) |

---

### Disaster Recovery Status (`/api/v1/dr/status`)

Useful for orgs enrolled in Okta's Disaster Recovery program to check current failover/failback state. ⚠️ EA. `failback`/`failover` are POST-only (state-changing) and out of scope for a read-only skill.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/dr/status` | `getDRStatus` | Retrieve the disaster recovery status for all domains |
| `GET /api/v1/dr/status/{domain}` | `getDRStatusForDomain` | Retrieve the disaster recovery status for a specific domain |

---

### OAuth Client Role Assignments (`/oauth2/v1/clients/{clientId}/roles`)

Admin role assignments to OAuth 2.0 client apps (service apps) — the client-app equivalent of the user/group role assignments already covered by okta-iam.

| Path | operationId | Description |
|---|---|---|
| `GET /oauth2/v1/clients/{clientId}/roles` | `listRolesForClient` | List all role assignments for a client app |
| `GET /oauth2/v1/clients/{clientId}/roles/{roleAssignmentId}` | `retrieveClientRole` | Retrieve a specific client role assignment |
| `GET /oauth2/v1/clients/{clientId}/roles/{roleAssignmentId}/targets/catalog/apps` | `listAppTargetRoleToClient` | List all app targets for a client's app-scoped role assignment |
| `GET /oauth2/v1/clients/{clientId}/roles/{roleAssignmentId}/targets/groups` | `listGroupTargetRoleForClient` | List all group targets for a client's group-scoped role assignment |

---

### Privileged Access Service Accounts (`/privileged-access/api/v1/okta-service-accounts`, `/privileged-access/api/v1/service-accounts`)

Okta Privileged Access (OPA) service account inventory. ⚠️ Limited GA (`isGenerallyAvailable: false`). Note: `/privileged-access/api/v1/containers/*` and `/privileged-access/api/v1/resources*` paths exist in the spec but have no HTTP methods defined (path parameters only) — nothing to implement there.

| Path | operationId | Description |
|---|---|---|
| `GET /privileged-access/api/v1/okta-service-accounts` | `listOktaManagedUserAccounts` | List all Okta-managed user accounts used as service accounts |
| `GET /privileged-access/api/v1/okta-service-accounts/{id}` | `getOktaManagedUserAccount` | Retrieve a specific Okta-managed user account |
| `GET /privileged-access/api/v1/service-accounts` | `listAppServiceAccounts` | List all app service accounts |
| `GET /privileged-access/api/v1/service-accounts/{id}` | `getAppServiceAccount` | Retrieve a specific app service account |

---

### Not recommended (reviewed, low value or out of scope)

- **`GET /api/v1/directories/{appInstanceId}/groups/{groupId}/query/{resultId}`** — polls the result of an async AD group attribute query started by a `POST .../query` call this toolset doesn't make; a `resultId` from a prior write isn't obtainable in a read-only workflow.
- **`/api/v1/identity-sources/{identitySourceId}/...`** — HR-driven bulk import staging (groups/sessions/users). The few GET endpoints (get group, get membership, list/get session, get user) exist to check the status of bulk write operations, and there's no endpoint to list identity sources themselves — the ID must already be known from elsewhere (e.g. an app's provisioning config). Mostly a write-oriented feature.
- **`GET /webauthn-registration/api/v1/users/{userId}/enrollments`** — lists WebAuthn preregistration factors (kiosk/shared-device fulfillment flow) for one user. ⚠️ Limited GA, single endpoint, narrow use case — could be added as an extra command on okta-authenticators or okta-users if ever needed, doesn't warrant its own skill.
- **`/integrations/api/v1/api-services`** — OIN partner integration-submission workflow; relevant only to ISV partners building Okta integrations, not org admins. Now has three GET endpoints (`listApiServiceIntegrationInstances`, `getApiServiceIntegrationInstance`, and a new `listApiServiceIntegrationInstanceSecrets` sub-resource since last audit) — still out of scope for the same reason.
- **`GET /okta-personal-settings/api/v1/export-blocklists`** — blocked email domains for Okta Personal (consumer product) app-migration exclusion; niche, not core org administration.
- **`/.well-known/okta-organization`, `/.well-known/ssf-configuration`, etc.** — unauthenticated public discovery documents. Org metadata and SSF transmitter metadata are somewhat redundant with `okta-org-settings get` and `okta-security get-ssf-streams`.


