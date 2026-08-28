# okta-skills

AI agent skills for reading data from the Okta API. These skills provide read-only access to Okta resources and are intended as a functional replacement for the Okta MCP server.

## Important: API Spec

Do not guess or assume how the Okta API works. Always verify endpoint paths, HTTP methods, query parameters, and response schemas against the official OpenAPI spec before writing or modifying any code:

**Spec URL:** https://raw.githubusercontent.com/okta/okta-management-openapi-spec/refs/heads/master/dist/current/management-minimal.yaml

A local copy (`management-minimal.yaml`) may exist in the repo root for quick reference, but it is gitignored and may be stale. Before starting any work, fetch a fresh copy from the URL above and save it to `management-minimal.yaml`:

```bash
curl -sSL https://raw.githubusercontent.com/okta/okta-management-openapi-spec/refs/heads/master/dist/current/management-minimal.yaml -o management-minimal.yaml
```

## Repository Structure

```
okta-skills/
├── skills/                        # Agent skill definitions (agentskills.io format)
│   ├── okta-api-tokens/
│   ├── okta-apps/
│   ├── okta-attack-protection/
│   ├── okta-authenticators/
│   ├── okta-authorization-servers/
│   ├── okta-behaviors/
│   ├── okta-device-assurance/
│   ├── okta-device-integrations/
│   ├── okta-device-posture/
│   ├── okta-devices/
│   ├── okta-expression-language/  # Okta Expression Language syntax reference (no script)
│   ├── okta-filters/              # SCIM filter/search syntax reference (no script)
│   ├── okta-groups/
│   ├── okta-iam/
│   ├── okta-identity-providers/
│   ├── okta-logs/
│   ├── okta-network-zones/
│   ├── okta-org-settings/
│   ├── okta-policies/
│   ├── okta-realms/
│   ├── okta-schemas/
│   ├── okta-security/
│   ├── okta-sessions/
│   └── okta-users/
│       ├── SKILL.md               # Skill metadata and instructions
│       └── scripts/users.py       # Executable script
├── shared/
│   └── okta_client.py             # Shared HTTP session and pagination logic
├── tests/
├── requirements.txt
└── AGENTS.md
```

## Invoking Scripts

Prefer `uv run` when uv is available — it manages dependencies automatically with no venv activation required. Fall back to plain `python` otherwise (requires dependencies installed in the active environment or repo `.venv`).

```bash
# Preferred
uv run skills/okta-users/scripts/users.py get user@example.com
uv run skills/okta-logs/scripts/logs.py login-failures --user user@example.com

# Fallback
python skills/okta-users/scripts/users.py get user@example.com
python skills/okta-logs/scripts/logs.py login-failures --user user@example.com
```

Do not source credential files or attempt to inject environment variables at invocation time — credentials must already be present in the shell environment before the agent session starts. This is the user's responsibility, not the agent's.

If a script exits with an auth error (`OKTA_CLIENT_ORGURL is not set`, `OKTA_CLIENT_TOKEN is required`, etc.), do not attempt to fix it by sourcing files or constructing credential strings. Instead, tell the user which environment variables are missing and ask them to set them — they can use `! export VAR=value` in Claude Code to set variables in their shell without leaving the session.

## Environment Variables

`OKTA_CLIENT_ORGURL` is always required. Auth method is determined by `OKTA_CLIENT_AUTHORIZATIONMODE` if set; otherwise auto-detected (PrivateKey preferred if both sets of credentials are present).

### Common

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_ORGURL` | Yes | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_AUTHORIZATIONMODE` | No | `PrivateKey` or `SSWS`. If unset, PrivateKey is used when client ID + key are present, otherwise SSWS. |
| `OKTA_CLIENT_USERAGENT` | No | Replaces the default `User-Agent` header |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | No | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | No | Request/read timeout in seconds (default: 30) |
| `OKTA_CLIENT_CABUNDLE` | No | Path to a CA bundle file or directory; use when behind a corporate proxy with a custom root CA. Takes precedence over `REQUESTS_CA_BUNDLE`. |
| `REQUESTS_CA_BUNDLE` | No | Standard `requests` library CA bundle variable; used as a fallback if `OKTA_CLIENT_CABUNDLE` is not set |

### SSWS (API Token) Auth

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_TOKEN` | Yes | Okta API token (SSWS token) |

### PrivateKey (OAuth 2.0) Auth

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_CLIENTID` | Yes | OAuth 2.0 service app client ID |
| `OKTA_CLIENT_PRIVATEKEY` | Yes | Private key as a PEM string, JWK JSON string, or path to a PEM/JWK file |
| `OKTA_CLIENT_SCOPES` | Yes | Space-separated OAuth scopes, e.g. `okta.users.read okta.groups.read` |
| `OKTA_CLIENT_TOKEN_CACHE_PATH` | No | File path for caching the access token between invocations. If unset, a fresh token is fetched on every run. |

PrivateKey auth requires `PyJWT>=2.0` and `cryptography>=41.0` to be installed. Supported key types: RSA (RS256) and EC (ES256).

## Skill Inventory

| Skill | Directory | API Endpoint | Description |
|---|---|---|---|
| okta-users | `skills/okta-users/` | `/api/v1/users` | User profiles, status, attributes |
| okta-groups | `skills/okta-groups/` | `/api/v1/groups` | Groups and group memberships |
| okta-apps | `skills/okta-apps/` | `/api/v1/apps` | Application integrations and assignments |
| okta-policies | `skills/okta-policies/` | `/api/v1/policies` | Sign-on, MFA, password, and access policies |
| okta-devices | `skills/okta-devices/` | `/api/v1/devices` | Enrolled device records |
| okta-network-zones | `skills/okta-network-zones/` | `/api/v1/zones` | IP and dynamic network zones |
| okta-device-assurance | `skills/okta-device-assurance/` | `/api/v1/device-assurances` | Device compliance requirement policies |
| okta-device-posture | `skills/okta-device-posture/` | `/api/v1/device-posture-checks` | Real-time device health posture checks |
| okta-logs | `skills/okta-logs/` | `/api/v1/logs` | System log events and audit history |
| okta-api-tokens | `skills/okta-api-tokens/` | `/api/v1/api-tokens` | API token metadata |
| okta-sessions | `skills/okta-sessions/` | `/api/v1/sessions` | Session lookup by ID |
| okta-iam | `skills/okta-iam/` | `/api/v1/iam`, `/api/v1/roles` | Custom admin roles, resource sets, role bindings, governance bundles |
| okta-authenticators | `skills/okta-authenticators/` | `/api/v1/authenticators` | Authenticator types, their methods, and custom Passkey/WebAuthn AAGUIDs |
| okta-behaviors | `skills/okta-behaviors/` | `/api/v1/behaviors` | Behavior detection rules (anomalous location/IP/device/ASN, velocity) |
| okta-authorization-servers | `skills/okta-authorization-servers/` | `/api/v1/authorizationServers` | OAuth/OIDC authorization servers, custom scopes, claims, policies, and signing keys |
| okta-identity-providers | `skills/okta-identity-providers/` | `/api/v1/idps` | Federation/social IdP integrations, key credentials, CSRs, signing keys, linked users |
| okta-schemas | `skills/okta-schemas/` | `/api/v1/mappings`, `/api/v1/meta/schemas`, `/api/v1/meta/types` | Profile mappings, user/group/app schemas, user types, log stream schemas, linked object definitions, UI schemas |
| okta-security | `skills/okta-security/` | `/api/v1/threats`, `/api/v1/security-events-providers`, `/api/v1/ssf`, `/api/v1/bot-protection` | ThreatInsight configuration, SSF security events providers/streams, bot protection settings |
| okta-attack-protection | `skills/okta-attack-protection/` | `/attack-protection/api/v1` | Authenticator lockout/enforcement settings and user lockout policy |
| okta-device-integrations | `skills/okta-device-integrations/` | `/api/v1/device-integrations` | Device trust/posture connector configurations (CrowdStrike, Chrome Device Trust, OSQuery, etc.) |
| okta-org-settings | `skills/okta-org-settings/` | `/api/v1/org` | Org general settings, contacts, CAPTCHA, third-party admin, preferences, Aerial consent, communication/support settings, YubiKey OTP tokens |
| okta-realms | `skills/okta-realms/` | `/api/v1/realms`, `/api/v1/realm-assignments` | Multi-tenant realm segmentation, realm assignment rules, and assignment operations |
| okta-filters | `skills/okta-filters/` | — | SCIM filter/search syntax reference and skill-selection guide |
| okta-expression-language | `skills/okta-expression-language/` | — | Okta Expression Language (EL) syntax/function reference for `elCondition.condition` on Authentication Policy and Account Management Policy rules, and `conditions.expression.value` on group rules |

## Command Reference

Each script accepts a subcommand and options. All output is JSON on stdout. Errors are JSON with an `error` key on stderr with exit code 1.

```bash
# Users
uv run skills/okta-users/scripts/users.py list
uv run skills/okta-users/scripts/users.py list --filter 'status eq "ACTIVE"'
uv run skills/okta-users/scripts/users.py get user@example.com
uv run skills/okta-users/scripts/users.py search "Jane Smith"
uv run skills/okta-users/scripts/users.py get-apps user@example.com
uv run skills/okta-users/scripts/users.py get-blocks user@example.com
uv run skills/okta-users/scripts/users.py get-groups user@example.com
uv run skills/okta-users/scripts/users.py get-idps user@example.com
uv run skills/okta-users/scripts/users.py get-linked-objects user@example.com manager
uv run skills/okta-users/scripts/users.py get-enrollments <userId>
uv run skills/okta-users/scripts/users.py get-classification <userId>
uv run skills/okta-users/scripts/users.py get-clients user@example.com
uv run skills/okta-users/scripts/users.py get-client-grants user@example.com <clientId>
uv run skills/okta-users/scripts/users.py get-client-tokens user@example.com <clientId>
uv run skills/okta-users/scripts/users.py get-client-token user@example.com <clientId> <tokenId>
uv run skills/okta-users/scripts/users.py get-devices <userId>
uv run skills/okta-users/scripts/users.py get-factors user@example.com
uv run skills/okta-users/scripts/users.py get-grants user@example.com
uv run skills/okta-users/scripts/users.py get-grant user@example.com <grantId>
uv run skills/okta-users/scripts/users.py get-risk <userId>
uv run skills/okta-users/scripts/users.py get-roles user@example.com
uv run skills/okta-users/scripts/users.py get-role user@example.com <roleAssignmentId>
uv run skills/okta-users/scripts/users.py get-subscriptions <userId>
uv run skills/okta-users/scripts/users.py get-subscription <userId> <notificationType>
uv run skills/okta-users/scripts/users.py get-factors-catalog user@example.com
uv run skills/okta-users/scripts/users.py get-factors-questions user@example.com
uv run skills/okta-users/scripts/users.py get-factor user@example.com <factorId>
uv run skills/okta-users/scripts/users.py get-factor-transaction user@example.com <factorId> <transactionId>
uv run skills/okta-users/scripts/users.py get-enrollment <userId> <enrollmentId>
uv run skills/okta-users/scripts/users.py get-role-governance user@example.com <roleAssignmentId>
uv run skills/okta-users/scripts/users.py get-role-governance-grant user@example.com <roleAssignmentId> <grantId>
uv run skills/okta-users/scripts/users.py get-role-governance-grant-resources user@example.com <roleAssignmentId> <grantId>
uv run skills/okta-users/scripts/users.py get-role-app-targets user@example.com <roleAssignmentId>
uv run skills/okta-users/scripts/users.py get-role-group-targets user@example.com <roleAssignmentId>
uv run skills/okta-users/scripts/users.py get-role-targets user@example.com <roleAssignmentId>

# Groups
uv run skills/okta-groups/scripts/groups.py list
uv run skills/okta-groups/scripts/groups.py get <group_id>
uv run skills/okta-groups/scripts/groups.py get-members <group_id>
uv run skills/okta-groups/scripts/groups.py get-apps <group_id>
uv run skills/okta-groups/scripts/groups.py get-owners <group_id>
uv run skills/okta-groups/scripts/groups.py search "Admins"
uv run skills/okta-groups/scripts/groups.py list-rules
uv run skills/okta-groups/scripts/groups.py list-rules --search "Engineering"
uv run skills/okta-groups/scripts/groups.py get-rule <rule_id>
uv run skills/okta-groups/scripts/groups.py list-roles <group_id>
uv run skills/okta-groups/scripts/groups.py get-role <group_id> <role_assignment_id>
uv run skills/okta-groups/scripts/groups.py list-role-app-targets <group_id> <role_assignment_id>
uv run skills/okta-groups/scripts/groups.py list-role-group-targets <group_id> <role_assignment_id>

# Apps
uv run skills/okta-apps/scripts/apps.py list
uv run skills/okta-apps/scripts/apps.py get <app_id>
uv run skills/okta-apps/scripts/apps.py get-users <app_id>
uv run skills/okta-apps/scripts/apps.py get-user <app_id> <user_id>
uv run skills/okta-apps/scripts/apps.py get-groups <app_id>
uv run skills/okta-apps/scripts/apps.py get-group <app_id> <group_id>
uv run skills/okta-apps/scripts/apps.py get-connection <app_id>
uv run skills/okta-apps/scripts/apps.py get-connection-jwks <app_id>
uv run skills/okta-apps/scripts/apps.py list-csrs <app_id>
uv run skills/okta-apps/scripts/apps.py get-csr <app_id> <csr_id>
uv run skills/okta-apps/scripts/apps.py list-jwks <app_id>
uv run skills/okta-apps/scripts/apps.py get-jwk <app_id> <key_id>
uv run skills/okta-apps/scripts/apps.py list-keys <app_id>
uv run skills/okta-apps/scripts/apps.py get-key <app_id> <key_id>
uv run skills/okta-apps/scripts/apps.py list-secrets <app_id>
uv run skills/okta-apps/scripts/apps.py get-secret <app_id> <secret_id>
uv run skills/okta-apps/scripts/apps.py list-cwo-connections <app_id>
uv run skills/okta-apps/scripts/apps.py get-cwo-connection <app_id> <connection_id>
uv run skills/okta-apps/scripts/apps.py list-features <app_id>
uv run skills/okta-apps/scripts/apps.py get-feature <app_id> <feature_name>
uv run skills/okta-apps/scripts/apps.py list-federated-claims <app_id>
uv run skills/okta-apps/scripts/apps.py get-federated-claim <app_id> <claim_id>
uv run skills/okta-apps/scripts/apps.py list-grants <app_id>
uv run skills/okta-apps/scripts/apps.py get-grant <app_id> <grant_id>
uv run skills/okta-apps/scripts/apps.py list-group-push-mappings <app_id>
uv run skills/okta-apps/scripts/apps.py get-group-push-mapping <app_id> <mapping_id>
uv run skills/okta-apps/scripts/apps.py list-interclient-allowed-apps <app_id>
uv run skills/okta-apps/scripts/apps.py list-interclient-target-apps <app_id>
uv run skills/okta-apps/scripts/apps.py get-saml-metadata <app_id> --kid <key_id>
uv run skills/okta-apps/scripts/apps.py list-tokens <app_id>
uv run skills/okta-apps/scripts/apps.py get-token <app_id> <token_id>

# Policies
uv run skills/okta-policies/scripts/policies.py list
uv run skills/okta-policies/scripts/policies.py list --type OKTA_SIGN_ON
uv run skills/okta-policies/scripts/policies.py get <policy_id>
uv run skills/okta-policies/scripts/policies.py get-rules <policy_id>
uv run skills/okta-policies/scripts/policies.py get-rule <policy_id> <rule_id>
uv run skills/okta-policies/scripts/policies.py list-mappings <policy_id>
uv run skills/okta-policies/scripts/policies.py get-mapping <policy_id> <mapping_id>

# Devices
uv run skills/okta-devices/scripts/devices.py list
uv run skills/okta-devices/scripts/devices.py get <device_id>
uv run skills/okta-devices/scripts/devices.py get-users <device_id>
uv run skills/okta-devices/scripts/devices.py get-os-accounts <device_id>
uv run skills/okta-devices/scripts/devices.py get-os-account <device_id> <os_account_id>

# Network Zones
uv run skills/okta-network-zones/scripts/network_zones.py list
uv run skills/okta-network-zones/scripts/network_zones.py get <zone_id>

# Device Assurance
uv run skills/okta-device-assurance/scripts/device_assurance.py list
uv run skills/okta-device-assurance/scripts/device_assurance.py get <policy_id>

# Device Posture
uv run skills/okta-device-posture/scripts/device_posture.py list
uv run skills/okta-device-posture/scripts/device_posture.py get <check_id>
uv run skills/okta-device-posture/scripts/device_posture.py list-defaults

# Logs
uv run skills/okta-logs/scripts/logs.py list
uv run skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z
uv run skills/okta-logs/scripts/logs.py list --filter 'eventType eq "user.session.start"' --limit 100
uv run skills/okta-logs/scripts/logs.py login-failures
uv run skills/okta-logs/scripts/logs.py login-failures --user user@example.com
uv run skills/okta-logs/scripts/logs.py list --filter 'outcome.result eq "FAILURE"'

# API Tokens
uv run skills/okta-api-tokens/scripts/api_tokens.py list
uv run skills/okta-api-tokens/scripts/api_tokens.py get <token_id>

# Sessions
uv run skills/okta-sessions/scripts/sessions.py get <session_id>

# IAM
uv run skills/okta-iam/scripts/iam.py list
uv run skills/okta-iam/scripts/iam.py get <role_id>
uv run skills/okta-iam/scripts/iam.py list-permissions <role_id>
uv run skills/okta-iam/scripts/iam.py get-permission <role_id> <permission_type>
uv run skills/okta-iam/scripts/iam.py list-assignees
uv run skills/okta-iam/scripts/iam.py list-resource-sets
uv run skills/okta-iam/scripts/iam.py get-resource-set <resource_set_id>
uv run skills/okta-iam/scripts/iam.py list-bindings <resource_set_id>
uv run skills/okta-iam/scripts/iam.py get-binding <resource_set_id> <role_id>
uv run skills/okta-iam/scripts/iam.py list-binding-members <resource_set_id> <role_id>
uv run skills/okta-iam/scripts/iam.py get-binding-member <resource_set_id> <role_id> <member_id>
uv run skills/okta-iam/scripts/iam.py list-resources <resource_set_id>
uv run skills/okta-iam/scripts/iam.py get-resource <resource_set_id> <resource_id>
uv run skills/okta-iam/scripts/iam.py list-bundles
uv run skills/okta-iam/scripts/iam.py get-bundle <bundle_id>
uv run skills/okta-iam/scripts/iam.py list-bundle-entitlements <bundle_id>
uv run skills/okta-iam/scripts/iam.py list-bundle-entitlement-values <bundle_id> <entitlement_id>
uv run skills/okta-iam/scripts/iam.py get-opt-in-status
uv run skills/okta-iam/scripts/iam.py list-role-subscriptions <role_ref>
uv run skills/okta-iam/scripts/iam.py get-role-subscription <role_ref> <notification_type>

# Authenticators
uv run skills/okta-authenticators/scripts/authenticators.py list
uv run skills/okta-authenticators/scripts/authenticators.py get <authenticator_id>
uv run skills/okta-authenticators/scripts/authenticators.py list-methods <authenticator_id>
uv run skills/okta-authenticators/scripts/authenticators.py get-method <authenticator_id> <method_type>
uv run skills/okta-authenticators/scripts/authenticators.py list-aaguids <authenticator_id>
uv run skills/okta-authenticators/scripts/authenticators.py get-aaguid <authenticator_id> <aaguid>

# Behaviors
uv run skills/okta-behaviors/scripts/behaviors.py list
uv run skills/okta-behaviors/scripts/behaviors.py get <behavior_id>

# Authorization Servers
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get <auth_server_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-associated-servers <auth_server_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-claims <auth_server_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-claim <auth_server_id> <claim_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-clients <auth_server_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-tokens <auth_server_id> <client_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-token <auth_server_id> <client_id> <token_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-keys <auth_server_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-key <auth_server_id> <key_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-policies <auth_server_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-policy <auth_server_id> <policy_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-policy-rules <auth_server_id> <policy_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-policy-rule <auth_server_id> <policy_id> <rule_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-resource-server-keys <auth_server_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-resource-server-key <auth_server_id> <key_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-scopes <auth_server_id>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-scope <auth_server_id> <scope_id>

# Identity Providers
uv run skills/okta-identity-providers/scripts/identity_providers.py list
uv run skills/okta-identity-providers/scripts/identity_providers.py get <idp_id>
uv run skills/okta-identity-providers/scripts/identity_providers.py list-keys
uv run skills/okta-identity-providers/scripts/identity_providers.py get-key <kid>
uv run skills/okta-identity-providers/scripts/identity_providers.py list-csrs <idp_id>
uv run skills/okta-identity-providers/scripts/identity_providers.py get-csr <idp_id> <idp_csr_id>
uv run skills/okta-identity-providers/scripts/identity_providers.py list-signing-keys <idp_id>
uv run skills/okta-identity-providers/scripts/identity_providers.py get-active-signing-key <idp_id>
uv run skills/okta-identity-providers/scripts/identity_providers.py get-signing-key <idp_id> <kid>
uv run skills/okta-identity-providers/scripts/identity_providers.py list-users <idp_id>
uv run skills/okta-identity-providers/scripts/identity_providers.py get-user <idp_id> <user_id>
uv run skills/okta-identity-providers/scripts/identity_providers.py list-tokens <idp_id> <user_id>

# Profile Mappings & Schemas
uv run skills/okta-schemas/scripts/schemas.py list
uv run skills/okta-schemas/scripts/schemas.py list --source-id <user_type_or_app_id> --target-id <user_type_or_app_id>
uv run skills/okta-schemas/scripts/schemas.py get <mapping_id>
uv run skills/okta-schemas/scripts/schemas.py get-app-user-schema <app_id>
uv run skills/okta-schemas/scripts/schemas.py get-group-schema
uv run skills/okta-schemas/scripts/schemas.py list-log-stream-schemas
uv run skills/okta-schemas/scripts/schemas.py get-log-stream-schema <log_stream_type>
uv run skills/okta-schemas/scripts/schemas.py list-linked-objects
uv run skills/okta-schemas/scripts/schemas.py get-linked-object <name>
uv run skills/okta-schemas/scripts/schemas.py get-user-schema <schema_id>
uv run skills/okta-schemas/scripts/schemas.py list-user-types
uv run skills/okta-schemas/scripts/schemas.py get-user-type <type_id>
uv run skills/okta-schemas/scripts/schemas.py list-ui-schemas
uv run skills/okta-schemas/scripts/schemas.py get-ui-schema <id>

# ThreatInsight & Security
uv run skills/okta-security/scripts/security.py get-threat-insight-config
uv run skills/okta-security/scripts/security.py list-security-events-providers
uv run skills/okta-security/scripts/security.py get-security-events-provider <id>
uv run skills/okta-security/scripts/security.py get-ssf-streams
uv run skills/okta-security/scripts/security.py get-ssf-streams --stream-id <stream_id>
uv run skills/okta-security/scripts/security.py get-ssf-stream-status <stream_id>
uv run skills/okta-security/scripts/security.py get-bot-protection-config

# Attack Protection
uv run skills/okta-attack-protection/scripts/attack_protection.py get-authenticator-settings
uv run skills/okta-attack-protection/scripts/attack_protection.py get-user-lockout-settings

# Device Integrations
uv run skills/okta-device-integrations/scripts/device_integrations.py list
uv run skills/okta-device-integrations/scripts/device_integrations.py get <device_integration_id>

# Org Settings
uv run skills/okta-org-settings/scripts/org_settings.py get
uv run skills/okta-org-settings/scripts/org_settings.py list-contact-types
uv run skills/okta-org-settings/scripts/org_settings.py get-contact <BILLING|TECHNICAL>
uv run skills/okta-org-settings/scripts/org_settings.py get-captcha-settings
uv run skills/okta-org-settings/scripts/org_settings.py get-third-party-admin-setting
uv run skills/okta-org-settings/scripts/org_settings.py get-preferences
uv run skills/okta-org-settings/scripts/org_settings.py get-aerial-consent
uv run skills/okta-org-settings/scripts/org_settings.py get-communication-settings
uv run skills/okta-org-settings/scripts/org_settings.py get-support-settings
uv run skills/okta-org-settings/scripts/org_settings.py list-support-cases
uv run skills/okta-org-settings/scripts/org_settings.py get-auto-assign-admin-app-setting
uv run skills/okta-org-settings/scripts/org_settings.py get-client-privileges-setting
uv run skills/okta-org-settings/scripts/org_settings.py list-yubikey-tokens
uv run skills/okta-org-settings/scripts/org_settings.py get-yubikey-token <token_id>

# Realms
uv run skills/okta-realms/scripts/realms.py list-realms
uv run skills/okta-realms/scripts/realms.py list-realms --search 'profile.name co "Partner"' --sort-by profile.name --sort-order asc
uv run skills/okta-realms/scripts/realms.py get-realm <realm_id>
uv run skills/okta-realms/scripts/realms.py list-realm-assignments
uv run skills/okta-realms/scripts/realms.py get-realm-assignment <assignment_id>
uv run skills/okta-realms/scripts/realms.py list-realm-assignment-operations
```

## Shared Library

`shared/okta_client.py` provides functions used by all scripts:

- `get_session()` — returns a configured `(session, base_url)` tuple using environment variables
- `paginated_get(session, url, params, limit)` — follows Okta's `Link` header pagination and returns a complete list
- `paginated_get_wrapped(session, url, key, params, limit)` — for IAM/governance endpoints (`/api/v1/iam/...`) that wrap results in a named field (e.g. `roles`, `resource-sets`) and paginate via a `_links.next.href` cursor in the response body instead of a `Link` header

Do not invoke `okta_client.py` directly. It is imported by each script via a `sys.path` insert pointing to the `shared/` directory.

## Conventions

- All operations are read-only. No write, update, or delete operations exist.
- Scripts follow the `list`, `get`, `search`, `get-<relation>`, `list-<relation>` subcommand pattern.
- Pagination is handled automatically; results are always returned as a complete JSON array.
- Date/time parameters use ISO 8601 format: `2024-01-01T00:00:00Z`.
- Filter expressions use Okta's SCIM filter syntax where supported.

## Knowledge Base

Each skill's `SKILL.md` is the authoritative source for interpreting the data that skill returns. Because skills can be installed and invoked from any project, all interpretation guidance must live inside the skill itself — do not rely on any external file being present.

When adding or updating a skill, include the following in its `SKILL.md`:

- **Output Schema** — key fields an agent needs to understand the response, including nested fields, enum values, and what each means in plain terms
- **Interpretation** — how to read the data: what field combinations indicate a particular state, what values are actionable, what is normal vs. noteworthy
- **Cross-skill references** — when a field in this skill's output (e.g. `actor.id` in a log event) can be used as input to another skill (e.g. `okta-users get`), say so explicitly

Keep this guidance agent-facing: write it so an agent that has just received a JSON response can understand what it's looking at and what to do next.
