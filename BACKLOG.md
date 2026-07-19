# Okta Skills Backlog

> Audited against `management-minimal.yaml` on 2026-06-18.
> Only HTTP GET operations are listed. Lifecycle notes: **⚠️ Limited GA** = `isGenerallyAvailable: false` or `lifecycle: LIMITED_GA`; **⚠️ EA** = `lifecycle: EA`.

---

## Gaps in existing skills

### okta-apps

Currently implements: all GET endpoints in spec for this path. No gaps.

### okta-groups

Currently implements: all GET endpoints in spec for this path. No gaps.

### okta-policies

Currently implements: all non-deprecated GET endpoints in spec for this path. `GET /api/v1/policies/{policyId}/app` (`listPolicyApps`) is intentionally not implemented — it's marked `deprecated: true` in the spec in favor of `listPolicyMappings` (`list-mappings`), which is implemented.

### okta-device-posture

Currently implements: all GET endpoints in spec for this path. No gaps. Note: `list` (`listDevicePostureChecks`) is EA and `list-defaults` (`listDefaultDevicePostureChecks`) is ⚠️ Limited GA (`isGenerallyAvailable: false`); `get` has no lifecycle restriction.

---

### okta-network-zones

Currently implements: `GET /api/v1/zones`, `GET /api/v1/zones/{id}`. Fully covers all GET endpoints in spec for this path. No gaps.

---

### okta-device-assurance

Currently implements: `GET /api/v1/device-assurances`, `GET /api/v1/device-assurances/{id}`. Fully covers all GET endpoints in spec for this path. No gaps.

---

### okta-logs

Currently implements: `GET /api/v1/logs`. Fully covers all GET endpoints in spec for this path. No gaps.

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

Currently implements: `list`, `get`, `get-users`. Fully covers all GET endpoints in spec for this path. No gaps. Note: `/api/v1/devices/{deviceId}/os-accounts` and `.../os-accounts/{osAccountId}` have no `get` operation defined in the spec at all (only lifecycle actions and path parameters), so there is nothing to implement there.

---

### okta-users

Currently implements: all GET endpoints in spec for this path. No gaps.

---

### okta-authorization-servers

Currently implements: all GET endpoints in spec for this path. No gaps.

---

### okta-identity-providers

Currently implements: all GET endpoints in spec for this path. No gaps.

---

### okta-attack-protection

Currently implements: `GET /attack-protection/api/v1/authenticator-settings`, `GET /attack-protection/api/v1/user-lockout-settings`. Fully covers all GET endpoints in spec for this path. No gaps. Note: `get-authenticator-settings` is ⚠️ Limited GA (`isGenerallyAvailable: false`); `get-user-lockout-settings` has no lifecycle restriction.

---

### okta-device-integrations

Currently implements: `GET /api/v1/device-integrations`, `GET /api/v1/device-integrations/{deviceIntegrationId}`. Fully covers all GET endpoints in spec for this path. No gaps. Note: both endpoints are ⚠️ Limited GA (`isGenerallyAvailable: false`).

---

### okta-org-settings

Currently implements: `GET /api/v1/org`, `GET /api/v1/org/contacts`, `GET /api/v1/org/contacts/{contactType}`, `GET /api/v1/org/captcha`, `GET /api/v1/org/orgSettings/thirdPartyAdminSetting`, `GET /api/v1/org/preferences`, `GET /api/v1/org/privacy/aerial`, `GET /api/v1/org/privacy/oktaCommunication`, `GET /api/v1/org/privacy/oktaSupport`, `GET /api/v1/org/privacy/oktaSupport/cases`, `GET /api/v1/org/settings/autoAssignAdminAppSetting`, `GET /api/v1/org/settings/clientPrivilegesSetting`, `GET /api/v1/org/factors/yubikey_token/tokens`, `GET /api/v1/org/factors/yubikey_token/tokens/{tokenId}`. Fully covers all GET endpoints in spec for this path. No gaps. Note: `get-captcha-settings` is ⚠️ Limited GA (`isGenerallyAvailable: false`); all others have no lifecycle restriction.

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
| `GET /api/v1/brands/{brandId}/pages/error/customized` | `getCustomizedErrorPage` | Retrieve the customized error page |
| `GET /api/v1/brands/{brandId}/pages/error/default` | `getDefaultErrorPage` | Retrieve the default error page |
| `GET /api/v1/brands/{brandId}/pages/sign-out/customized` | `getSignOutPageSettings` | Retrieve the sign-out page settings |
| `GET /api/v1/brands/{brandId}/templates/email` | `listEmailTemplates` | List all email templates for a brand |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}` | `getEmailTemplate` | Retrieve a specific email template |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/customizations` | `listEmailCustomizations` | List all email customizations for a template |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/customizations/{customizationId}` | `getEmailCustomization` | Retrieve a specific email customization |
| `GET /api/v1/brands/{brandId}/templates/email/{templateName}/default-content` | `getEmailDefaultContent` | Retrieve the default content of an email template |
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

### Realms (`/api/v1/realms`, `/api/v1/realm-assignments`)

Useful for orgs using Okta's Realm feature for multi-tenant segmentation.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/realms` | `listRealms` | List all realms |
| `GET /api/v1/realms/{realmId}` | `getRealm` | Retrieve a specific realm |
| `GET /api/v1/realm-assignments` | `listRealmAssignments` | List all realm assignments |
| `GET /api/v1/realm-assignments/{assignmentId}` | `getRealmAssignment` | Retrieve a specific realm assignment |
| `GET /api/v1/realm-assignments/operations` | `listRealmAssignmentOperations` | List all realm assignment operations |

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


