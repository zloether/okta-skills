# Okta Skills Backlog

> Audited against `management-minimal.yaml` on 2026-06-18.
> Only HTTP GET operations are listed. Lifecycle notes: **⚠️ Limited GA** = `isGenerallyAvailable: false` or `lifecycle: LIMITED_GA`; **⚠️ EA** = `lifecycle: EA`.

---

## Gaps in existing skills

### okta-apps

Currently implements: `GET /api/v1/apps`, `GET /api/v1/apps/{appId}`, `GET /api/v1/apps/{appId}/users`, `GET /api/v1/apps/{appId}/groups`.

Missing:

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/apps/{appId}/connections/default` | `getDefaultProvisioningConnectionForApplication` | Retrieve the default provisioning connection for an app |
| `GET /api/v1/apps/{appId}/connections/default/jwks` | `getUserProvisioningConnectionJWKS` | Retrieve the JWKS for the default provisioning connection |
| `GET /api/v1/apps/{appId}/credentials/csrs` | `listCsrsForApplication` | List all certificate signing requests for an app |
| `GET /api/v1/apps/{appId}/credentials/csrs/{csrId}` | `getCsrForApplication` | Retrieve a specific CSR for an app |
| `GET /api/v1/apps/{appId}/credentials/jwks` | `listJwk` | List all OAuth 2.0 client JSON Web Keys for an app |
| `GET /api/v1/apps/{appId}/credentials/jwks/{keyId}` | `getJwk` | Retrieve a specific OAuth 2.0 client JWK |
| `GET /api/v1/apps/{appId}/credentials/keys` | `listApplicationKeys` | List all key credentials for an app |
| `GET /api/v1/apps/{appId}/credentials/keys/{keyId}` | `getApplicationKey` | Retrieve a specific key credential |
| `GET /api/v1/apps/{appId}/credentials/secrets` | `listOAuth2ClientSecrets` | List all OAuth 2.0 client secrets |
| `GET /api/v1/apps/{appId}/credentials/secrets/{secretId}` | `getOAuth2ClientSecret` | Retrieve a specific OAuth 2.0 client secret |
| `GET /api/v1/apps/{appId}/cwo/connections` | `getAllCrossAppAccessConnections` | List all Cross App Access connections ⚠️ EA |
| `GET /api/v1/apps/{appId}/cwo/connections/{connectionId}` | `getCrossAppAccessConnection` | Retrieve a specific Cross App Access connection ⚠️ EA |
| `GET /api/v1/apps/{appId}/features` | `listFeaturesForApplication` | List all features enabled for an app |
| `GET /api/v1/apps/{appId}/features/{featureName}` | `getFeatureForApplication` | Retrieve a specific app feature |
| `GET /api/v1/apps/{appId}/federated-claims` | `listFederatedClaims` | List all configured federated claims for an app |
| `GET /api/v1/apps/{appId}/federated-claims/{claimId}` | `getFederatedClaim` | Retrieve a specific federated claim |
| `GET /api/v1/apps/{appId}/grants` | `listScopeConsentGrants` | List all scope consent grants for an app |
| `GET /api/v1/apps/{appId}/grants/{grantId}` | `getScopeConsentGrant` | Retrieve a specific app grant |
| `GET /api/v1/apps/{appId}/group-push/mappings` | `listGroupPushMappings` | List all group push mappings for an app |
| `GET /api/v1/apps/{appId}/group-push/mappings/{mappingId}` | `getGroupPushMapping` | Retrieve a specific group push mapping |
| `GET /api/v1/apps/{appId}/groups/{groupId}` | `getApplicationGroupAssignment` | Retrieve a specific group assignment for an app |
| `GET /api/v1/apps/{appId}/interclient-allowed-apps` | `listInterclientAllowedApplications` | List all apps allowed to call a target app ⚠️ EA |
| `GET /api/v1/apps/{appId}/interclient-target-apps` | `listInterclientTargetApplications` | List all target apps an allowed app can call ⚠️ EA |
| `GET /api/v1/apps/{appId}/sso/saml/metadata` | `previewSAMLmetadataForApplication` | Retrieve the SAML metadata for an app |
| `GET /api/v1/apps/{appId}/tokens` | `listOAuth2TokensForApplication` | List all refresh tokens for an app |
| `GET /api/v1/apps/{appId}/tokens/{tokenId}` | `getOAuth2TokenForApplication` | Retrieve a specific app refresh token |
| `GET /api/v1/apps/{appId}/users/{userId}` | `getApplicationUser` | Retrieve a specific user assignment for an app |

---

### okta-groups

Currently implements: `GET /api/v1/groups`, `GET /api/v1/groups/{id}`, `GET /api/v1/groups/{id}/users`, `GET /api/v1/groups/{id}/apps`, `GET /api/v1/groups/{id}/owners`, `GET /api/v1/groups/rules`, `GET /api/v1/groups/rules/{id}`.

Missing:

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/groups/{groupId}/roles` | `listGroupAssignedRoles` | List all role assignments for a group |
| `GET /api/v1/groups/{groupId}/roles/{roleAssignmentId}` | `getGroupAssignedRole` | Retrieve a specific role assignment for a group |
| `GET /api/v1/groups/{groupId}/roles/{roleAssignmentId}/targets/catalog/apps` | `listApplicationTargetsForApplicationAdministratorRoleForGroup` | List all app targets for a group's admin role |
| `GET /api/v1/groups/{groupId}/roles/{roleAssignmentId}/targets/groups` | `listGroupTargetsForGroupRole` | List all group targets for a group's role |

---

### okta-policies

Currently implements: `GET /api/v1/policies`, `GET /api/v1/policies/{id}`, `GET /api/v1/policies/{id}/rules`.

Missing:

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/policies/{policyId}/rules/{ruleId}` | `getPolicyRule` | Retrieve a specific policy rule by ID |
| `GET /api/v1/policies/{policyId}/app` | `listPolicyApps` | List all apps mapped to a policy |
| `GET /api/v1/policies/{policyId}/mappings` | `listPolicyMappings` | List all resources (apps/groups) mapped to a policy |
| `GET /api/v1/policies/{policyId}/mappings/{mappingId}` | `getPolicyMapping` | Retrieve a specific policy resource mapping |

---

### okta-device-posture

Currently implements: `GET /api/v1/device-posture-checks`, `GET /api/v1/device-posture-checks/{id}`.

Missing:

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/device-posture-checks/default` | `listDefaultDevicePostureChecks` | List all Okta-built-in (BUILTIN) default device posture checks ⚠️ Limited GA |

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

### Admin Roles & IAM (`/api/v1/iam`, `/api/v1/roles`)

Essential for understanding who has admin access and what custom roles exist.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/iam/assignees/users` | `listUsersWithRoleAssignments` | List all users who have any role assignment |
| `GET /api/v1/iam/roles` | `listRoles` | List all custom roles |
| `GET /api/v1/iam/roles/{roleIdOrLabel}` | `getRole` | Retrieve a specific custom role |
| `GET /api/v1/iam/roles/{roleIdOrLabel}/permissions` | `listRolePermissions` | List all permissions for a custom role |
| `GET /api/v1/iam/roles/{roleIdOrLabel}/permissions/{permissionType}` | `getRolePermission` | Retrieve a specific custom role permission |
| `GET /api/v1/iam/resource-sets` | `listResourceSets` | List all resource sets |
| `GET /api/v1/iam/resource-sets/{resourceSetIdOrLabel}` | `getResourceSet` | Retrieve a specific resource set |
| `GET /api/v1/iam/resource-sets/{resourceSetIdOrLabel}/bindings` | `listBindings` | List all role-to-resource-set bindings |
| `GET /api/v1/iam/resource-sets/{resourceSetIdOrLabel}/bindings/{roleIdOrLabel}` | `getBinding` | Retrieve a specific role-resource-set binding |
| `GET /api/v1/iam/resource-sets/{resourceSetIdOrLabel}/bindings/{roleIdOrLabel}/members` | `listMembersOfBinding` | List all members of a role-resource-set binding |
| `GET /api/v1/iam/resource-sets/{resourceSetIdOrLabel}/bindings/{roleIdOrLabel}/members/{memberId}` | `getMemberOfBinding` | Retrieve a specific binding member |
| `GET /api/v1/iam/resource-sets/{resourceSetIdOrLabel}/resources` | `listResourceSetResources` | List all resources in a resource set |
| `GET /api/v1/iam/resource-sets/{resourceSetIdOrLabel}/resources/{resourceId}` | `getResourceSetResource` | Retrieve a specific resource set resource |
| `GET /api/v1/iam/governance/bundles` | `listGovernanceBundles` | List all governance bundles ⚠️ Limited GA |
| `GET /api/v1/iam/governance/bundles/{bundleId}` | `getGovernanceBundle` | Retrieve a specific governance bundle ⚠️ Limited GA |
| `GET /api/v1/iam/governance/bundles/{bundleId}/entitlements` | `listBundleEntitlements` | List all entitlements for a governance bundle ⚠️ Limited GA |
| `GET /api/v1/iam/governance/bundles/{bundleId}/entitlements/{entitlementId}/values` | `listBundleEntitlementValues` | List all values for a governance bundle entitlement ⚠️ Limited GA |
| `GET /api/v1/iam/governance/optIn` | `getOptInStatus` | Retrieve the Admin Console governance opt-in status ⚠️ Limited GA |
| `GET /api/v1/roles/{roleRef}/subscriptions` | `listSubscriptionsRole` | List all notification subscriptions for a role |
| `GET /api/v1/roles/{roleRef}/subscriptions/{notificationType}` | `getSubscriptionsNotificationTypeRole` | Retrieve a specific notification subscription for a role |

---

### Authenticators (`/api/v1/authenticators`)

Useful for understanding what MFA methods are configured org-wide.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/authenticators` | `listAuthenticators` | List all authenticators configured in the org ⚠️ Limited GA |
| `GET /api/v1/authenticators/{authenticatorId}` | `getAuthenticator` | Retrieve a specific authenticator ⚠️ Limited GA |
| `GET /api/v1/authenticators/{authenticatorId}/methods` | `listAuthenticatorMethods` | List all methods for an authenticator ⚠️ Limited GA |
| `GET /api/v1/authenticators/{authenticatorId}/methods/{methodType}` | `getAuthenticatorMethod` | Retrieve a specific authenticator method ⚠️ Limited GA |
| `GET /api/v1/authenticators/{authenticatorId}/aaguids` | `listAllCustomAAGUIDs` | List all custom WebAuthn AAGUIDs for an authenticator |
| `GET /api/v1/authenticators/{authenticatorId}/aaguids/{aaguid}` | `getCustomAAGUID` | Retrieve a specific custom AAGUID |

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

### Behaviors (`/api/v1/behaviors`)

Useful for understanding what behavioral detection rules are active (e.g., new device, new country).

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/behaviors` | `listBehaviorDetectionRules` | List all behavior detection rules |
| `GET /api/v1/behaviors/{behaviorId}` | `getBehaviorDetectionRule` | Retrieve a specific behavior detection rule |

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

### API Tokens (`/api/v1/api-tokens`)

Useful for auditing which API tokens exist and who created them.

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/api-tokens` | `listApiTokens` | List metadata for all API tokens in the org |
| `GET /api/v1/api-tokens/{apiTokenId}` | `getApiToken` | Retrieve metadata for a specific API token |

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

### Sessions (`/api/v1/sessions`)

| Path | operationId | Description |
|---|---|---|
| `GET /api/v1/sessions/{sessionId}` | `getSession` | Retrieve session information for a specific session ID |

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
