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

## New skills to build

### Authorization Servers (`/api/v1/authorizationServers`)

Core OAuth/OIDC infrastructure — highly useful for understanding what token policies and scopes exist.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/authorizationServers` | `listAuthorizationServers` | List all authorization servers |
| `GET /api/v1/authorizationServers/{authServerId}` | `getAuthorizationServer` | Retrieve an authorization server |
| `GET /api/v1/authorizationServers/{authServerId}/associatedServers` | `listAssociatedServersByTrustedType` | List all servers trusted by an auth server |
| `GET /api/v1/authorizationServers/{authServerId}/claims` | `listOAuth2Claims` | List all custom token claims for an auth server |
| `GET /api/v1/authorizationServers/{authServerId}/claims/{claimId}` | `getOAuth2Claim` | Retrieve a specific custom claim |
| `GET /api/v1/authorizationServers/{authServerId}/clients` | `listOAuth2ClientsForAuthorizationServer` | List all clients registered with an auth server |
| `GET /api/v1/authorizationServers/{authServerId}/clients/{clientId}/tokens` | `listRefreshTokensForAuthorizationServerAndClient` | List all refresh tokens for a client on an auth server |
| `GET /api/v1/authorizationServers/{authServerId}/clients/{clientId}/tokens/{tokenId}` | `getRefreshTokenForAuthorizationServerAndClient` | Retrieve a specific refresh token |
| `GET /api/v1/authorizationServers/{authServerId}/credentials/keys` | `listAuthorizationServerKeys` | List all signing keys for an auth server |
| `GET /api/v1/authorizationServers/{authServerId}/credentials/keys/{keyId}` | `getAuthorizationServerKey` | Retrieve a specific signing key |
| `GET /api/v1/authorizationServers/{authServerId}/policies` | `listAuthorizationServerPolicies` | List all policies for an auth server |
| `GET /api/v1/authorizationServers/{authServerId}/policies/{policyId}` | `getAuthorizationServerPolicy` | Retrieve a specific auth server policy |
| `GET /api/v1/authorizationServers/{authServerId}/policies/{policyId}/rules` | `listAuthorizationServerPolicyRules` | List all rules for an auth server policy |
| `GET /api/v1/authorizationServers/{authServerId}/policies/{policyId}/rules/{ruleId}` | `getAuthorizationServerPolicyRule` | Retrieve a specific auth server policy rule |
| `GET /api/v1/authorizationServers/{authServerId}/resourceservercredentials/keys` | `listOAuth2ResourceServerJsonWebKeys` | List all resource server public JWKs |
| `GET /api/v1/authorizationServers/{authServerId}/resourceservercredentials/keys/{keyId}` | `getOAuth2ResourceServerJsonWebKey` | Retrieve a specific resource server JWK |
| `GET /api/v1/authorizationServers/{authServerId}/scopes` | `listOAuth2Scopes` | List all custom scopes for an auth server |
| `GET /api/v1/authorizationServers/{authServerId}/scopes/{scopeId}` | `getOAuth2Scope` | Retrieve a specific custom scope |

---

### Identity Providers (`/api/v1/idps`)

Useful for understanding federation configuration and which external IdPs are configured.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/idps` | `listIdentityProviders` | List all identity providers |
| `GET /api/v1/idps/{idpId}` | `getIdentityProvider` | Retrieve a specific IdP |
| `GET /api/v1/idps/credentials/keys` | `listIdentityProviderKeys` | List all IdP key credentials |
| `GET /api/v1/idps/credentials/keys/{kid}` | `getIdentityProviderKey` | Retrieve a specific IdP key credential |
| `GET /api/v1/idps/{idpId}/credentials/csrs` | `listCsrsForIdentityProvider` | List all CSRs for an IdP |
| `GET /api/v1/idps/{idpId}/credentials/csrs/{idpCsrId}` | `getCsrForIdentityProvider` | Retrieve a specific IdP CSR |
| `GET /api/v1/idps/{idpId}/credentials/keys` | `listIdentityProviderSigningKeys` | List all signing keys for an IdP |
| `GET /api/v1/idps/{idpId}/credentials/keys/active` | `listActiveIdentityProviderSigningKey` | List the active signing key for an IdP |
| `GET /api/v1/idps/{idpId}/credentials/keys/{kid}` | `getIdentityProviderSigningKey` | Retrieve a specific IdP signing key |
| `GET /api/v1/idps/{idpId}/users` | `listIdentityProviderApplicationUsers` | List all users linked to an IdP |
| `GET /api/v1/idps/{idpId}/users/{userId}` | `getIdentityProviderApplicationUser` | Retrieve a specific user linked to an IdP |
| `GET /api/v1/idps/{idpId}/users/{userId}/credentials/tokens` | `listSocialAuthTokens` | List all social auth tokens for an OIDC IdP user |

---

### Org Settings (`/api/v1/org`)

Useful for answering questions about how the org is configured.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/org` | `getOrgSettings` | Retrieve the org's general settings (name, website, etc.) |
| `GET /api/v1/org/contacts` | `listOrgContactTypes` | List all org contact types |
| `GET /api/v1/org/contacts/{contactType}` | `getOrgContactUser` | Retrieve the user for a specific contact type |
| `GET /api/v1/org/captcha` | `getOrgCaptchaSettings` | Retrieve org-wide CAPTCHA settings ⚠️ Limited GA |
| `GET /api/v1/org/orgSettings/thirdPartyAdminSetting` | `getThirdPartyAdminSetting` | Retrieve the org third-party admin setting |
| `GET /api/v1/org/preferences` | `getOrgPreferences` | Retrieve the org's end-user UI preferences |
| `GET /api/v1/org/privacy/aerial` | `getAerialConsent` | Retrieve Okta Aerial consent status for the org |
| `GET /api/v1/org/privacy/oktaCommunication` | `getOktaCommunicationSettings` | Retrieve the Okta communication opt-in settings |
| `GET /api/v1/org/privacy/oktaSupport` | `getOrgOktaSupportSettings` | Retrieve the Okta Support access settings |
| `GET /api/v1/org/privacy/oktaSupport/cases` | `listOktaSupportCases` | List all open Okta Support cases |
| `GET /api/v1/org/settings/autoAssignAdminAppSetting` | `getAutoAssignAdminAppSetting` | Retrieve the auto-assign Admin Console app setting |
| `GET /api/v1/org/settings/clientPrivilegesSetting` | `getClientPrivilegesSetting` | Retrieve the default public client app role setting |
| `GET /api/v1/org/factors/yubikey_token/tokens` | `listYubikeyOtpTokens` | List all YubiKey OTP tokens provisioned in the org |
| `GET /api/v1/org/factors/yubikey_token/tokens/{tokenId}` | `getYubikeyOtpTokenById` | Retrieve a specific YubiKey OTP token |

---

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

### Profile Mappings & Schemas (`/api/v1/mappings`, `/api/v1/meta/schemas`, `/api/v1/meta/types`)

Useful for understanding how user attributes flow between Okta and applications.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/mappings` | `listProfileMappings` | List all profile mappings in the org |
| `GET /api/v1/mappings/{mappingId}` | `getProfileMapping` | Retrieve a specific profile mapping |
| `GET /api/v1/meta/schemas/apps/{appId}/default` | `getApplicationUserSchema` | Retrieve the default app user schema for an app |
| `GET /api/v1/meta/schemas/group/default` | `getGroupSchema` | Retrieve the default group schema |
| `GET /api/v1/meta/schemas/logStream` | `listLogStreamSchemas` | List all log stream schemas |
| `GET /api/v1/meta/schemas/logStream/{logStreamType}` | `getLogStreamSchema` | Retrieve the log stream schema for a specific type |
| `GET /api/v1/meta/schemas/user/linkedObjects` | `listLinkedObjectDefinitions` | List all linked object definitions |
| `GET /api/v1/meta/schemas/user/linkedObjects/{linkedObjectName}` | `getLinkedObjectDefinition` | Retrieve a specific linked object definition |
| `GET /api/v1/meta/schemas/user/{schemaId}` | `getUserSchema` | Retrieve a user schema |
| `GET /api/v1/meta/types/user` | `listUserTypes` | List all user types in the org |
| `GET /api/v1/meta/types/user/{typeId}` | `getUserType` | Retrieve a specific user type |
| `GET /api/v1/meta/uischemas` | `listUISchemas` | List all UI schemas ⚠️ Limited GA |
| `GET /api/v1/meta/uischemas/{id}` | `getUISchema` | Retrieve a specific UI schema ⚠️ Limited GA |

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

### ThreatInsight & Security (`/api/v1/threats`, `/api/v1/security-events-providers`, `/api/v1/bot-protection`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/threats/configuration` | `getCurrentConfiguration` | Retrieve the ThreatInsight configuration |
| `GET /api/v1/security-events-providers` | `listSecurityEventsProviderInstances` | List all security events providers (SSF receivers) ⚠️ Limited GA |
| `GET /api/v1/security-events-providers/{securityEventProviderId}` | `getSecurityEventsProviderInstance` | Retrieve a specific security events provider ⚠️ Limited GA |
| `GET /api/v1/ssf/stream` | `getSsfStreams` | Retrieve the SSF stream configuration(s) ⚠️ Limited GA |
| `GET /api/v1/ssf/stream/status` | `getSsfStreamStatus` | Retrieve the SSF stream status ⚠️ Limited GA |
| `GET /api/v1/bot-protection/configuration` | `getBotProtectionConfiguration` | Retrieve the bot protection configuration ⚠️ EA |

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

### Device Integrations (`/api/v1/device-integrations`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/device-integrations` | `listDeviceIntegrations` | List all device integrations ⚠️ Limited GA |
| `GET /api/v1/device-integrations/{deviceIntegrationId}` | `getDeviceIntegration` | Retrieve a specific device integration ⚠️ Limited GA |

---

### Attack Protection (`/attack-protection/api/v1`)

Note: these endpoints are under a different base path (`/attack-protection/api/v1/`), not `/api/v1/`.

| Path | operationId | Description |
|---|---|---|
| `GET /attack-protection/api/v1/authenticator-settings` | `getAuthenticatorSettings` | Retrieve the org's authenticator lockout/enforcement settings ⚠️ Limited GA |
| `GET /attack-protection/api/v1/user-lockout-settings` | `getUserLockoutSettings` | Retrieve the org's user lockout policy settings |
