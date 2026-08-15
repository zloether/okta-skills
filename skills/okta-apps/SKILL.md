---
name: okta-apps
description: Read Okta application integrations and app assignments. Use when asked about applications, app integrations, which apps a user or group can access, which users or groups are assigned to an app, or app configuration details.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-apps/scripts/apps.py <command> [options]
```

### list
List applications, optionally filtered.
```bash
uv run skills/okta-apps/scripts/apps.py list
uv run skills/okta-apps/scripts/apps.py list --filter 'status eq "ACTIVE"'
uv run skills/okta-apps/scripts/apps.py list --filter 'name eq "workday"'
uv run skills/okta-apps/scripts/apps.py list --q workday --limit 50
```
Options: `--q` (name-prefix search), `--expand` (must be paired with `--filter`), `--use-optimization`, `--always-include-vpn-settings`, `--include-non-deleted`, `--limit`.

### get
Get a single application by ID.
```bash
uv run skills/okta-apps/scripts/apps.py get 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get 0oa1ab2cd3EF4GH5IJ6K --expand user/00u1ab2cd3EF4GH5IJ6K
```

### get-users
List users assigned to an application.
```bash
uv run skills/okta-apps/scripts/apps.py get-users 0oa1ab2cd3EF4GH5IJ6K
```
Options: `--q` (search by user name/login), `--expand` (e.g. `user`), `--limit`.

### get-groups
List groups assigned to an application.
```bash
uv run skills/okta-apps/scripts/apps.py get-groups 0oa1ab2cd3EF4GH5IJ6K
```
Options: `--q` (search by group name), `--expand` (e.g. `group`), `--limit`.

### get-group
Get a specific group assignment for an application.
```bash
uv run skills/okta-apps/scripts/apps.py get-group 0oa1ab2cd3EF4GH5IJ6K 00g1ab2cd3EF4GH5IJ6K --expand group
```

### get-user
Get a specific user assignment for an application.
```bash
uv run skills/okta-apps/scripts/apps.py get-user 0oa1ab2cd3EF4GH5IJ6K 00u1ab2cd3EF4GH5IJ6K --expand user
```

### get-connection / get-connection-jwks
Get the default provisioning connection for an app, or its JWKS.
```bash
uv run skills/okta-apps/scripts/apps.py get-connection 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-connection-jwks 0oa1ab2cd3EF4GH5IJ6K
```

### list-csrs / get-csr
List or get certificate signing requests for an app's SSO credentials.
```bash
uv run skills/okta-apps/scripts/apps.py list-csrs 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-csr 0oa1ab2cd3EF4GH5IJ6K <csr_id>
```

### list-jwks / get-jwk
List or get an app's OAuth 2.0 client JSON Web Keys.
```bash
uv run skills/okta-apps/scripts/apps.py list-jwks 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-jwk 0oa1ab2cd3EF4GH5IJ6K <key_id>
```

### list-keys / get-key
List or get an app's key credentials (SSO signing certificates).
```bash
uv run skills/okta-apps/scripts/apps.py list-keys 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-key 0oa1ab2cd3EF4GH5IJ6K <key_id>
```

### list-secrets / get-secret
List or get an app's OAuth 2.0 client secrets.
```bash
uv run skills/okta-apps/scripts/apps.py list-secrets 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-secret 0oa1ab2cd3EF4GH5IJ6K <secret_id>
```

### list-cwo-connections / get-cwo-connection
List or get Cross App Access (CWO) connections for an app. ⚠️ Early Access.
```bash
uv run skills/okta-apps/scripts/apps.py list-cwo-connections 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-cwo-connection 0oa1ab2cd3EF4GH5IJ6K <connection_id>
```
`list-cwo-connections` options: `--status`, `--requesting-app-id`, `--resource-app-id`, `--active-apps-only`, `--requesting-app-name`, `--resource-app-name`.

### list-features / get-feature
List or get an app's enabled provisioning features.
```bash
uv run skills/okta-apps/scripts/apps.py list-features 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-feature 0oa1ab2cd3EF4GH5IJ6K USER_PROVISIONING
```

### list-federated-claims / get-federated-claim
List or get an app's federated (SAML/OIDC) claim configurations.
```bash
uv run skills/okta-apps/scripts/apps.py list-federated-claims 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-federated-claim 0oa1ab2cd3EF4GH5IJ6K <claim_id>
```

### list-grants / get-grant
List or get OAuth 2.0 scope consent grants for an app.
```bash
uv run skills/okta-apps/scripts/apps.py list-grants 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-grant 0oa1ab2cd3EF4GH5IJ6K <grant_id>
```
Both accept `--expand` (e.g. `scope`).

### list-group-push-mappings / get-group-push-mapping
List or get group push mappings (Okta groups pushed to a downstream app).
```bash
uv run skills/okta-apps/scripts/apps.py list-group-push-mappings 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-group-push-mapping 0oa1ab2cd3EF4GH5IJ6K <mapping_id>
```
`list-group-push-mappings` options: `--last-updated`, `--source-group-id`, `--status`.

### list-interclient-allowed-apps / list-interclient-target-apps
List apps allowed to call this app, or apps this app is allowed to call, via Okta Interclient Access. ⚠️ Limited GA.
```bash
uv run skills/okta-apps/scripts/apps.py list-interclient-allowed-apps 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py list-interclient-target-apps 0oa1ab2cd3EF4GH5IJ6K
```

### get-saml-metadata
Get the SAML metadata (raw XML, not JSON) for a SAML app. `--kid` is required — get it from `list-keys`.
```bash
uv run skills/okta-apps/scripts/apps.py get-saml-metadata 0oa1ab2cd3EF4GH5IJ6K --kid <key_id>
```

### list-tokens / get-token
List or get OAuth 2.0 refresh tokens issued to an app.
```bash
uv run skills/okta-apps/scripts/apps.py list-tokens 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-apps/scripts/apps.py get-token 0oa1ab2cd3EF4GH5IJ6K <token_id>
```
Both accept `--expand` (e.g. `scope`).

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

## Output

JSON to stdout for all commands except `get-saml-metadata`, which prints raw XML. List operations return arrays; `get` returns a single app object. `get-users` returns AppUser objects (include a `credentials` and `profile` field in addition to user info). Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### App object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta app ID (e.g. `0oa1ab2cd3EF4GH5IJ6K`); use this as the target in other lookups |
| `name` | string | Internal app name / integration key (e.g. `workday`, `salesforce`, `template_saml_2_0`) |
| `label` | string | Human-readable display name shown to users |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `signOnMode` | string | How the app authenticates — see Sign-on Modes below |
| `features` | array | Enabled features: `PUSH_NEW_USERS`, `PUSH_USER_DEACTIVATION`, `PUSH_GROUPS`, etc. |
| `credentials.scheme` | string | `SHARED_USERNAME_AND_PASSWORD`, `EXTERNAL_PASSWORD_SYNC`, `EDIT_USERNAME_AND_PASSWORD`, `ADMIN_SETS_CREDENTIALS` |
| `settings.app` | object | App-specific settings (varies by integration) |
| `created` | ISO 8601 string | When the app integration was created |
| `lastUpdated` | ISO 8601 string | When the app integration was last modified |
| `_links` | object | HAL links for related resources (users, groups, logo, metadata) |

### AppUser object (`get-users`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta user ID |
| `status` | string | User's assignment status: `ACTIVE`, `PROVISIONED`, `DEPROVISIONED` |
| `created` | ISO 8601 string | When the user was assigned to this app |
| `lastUpdated` | ISO 8601 string | When the assignment was last modified |
| `credentials.userName` | string | Username used for this specific app (may differ from Okta login) |
| `profile` | object | App-specific profile attributes pushed to the app (varies by integration) |
| `scope` | string | `USER` (direct assignment) or `GROUP` (assigned via a group) |

### Group assignment object (`get-groups` / `get-group`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta group ID |
| `priority` | integer | Assignment priority (lower = higher priority) |
| `lastUpdated` | ISO 8601 string | When the group assignment was last modified |

### Key credential / JWK object (`list-keys`, `get-key`, `list-jwks`, `get-jwk`)

| Field | Type | Description |
|---|---|---|
| `kid` | string | Key ID; pass to `get-key`/`get-jwk` or use as `--kid` for `get-saml-metadata` |
| `kty` | string | Key type, e.g. `RSA` |
| `use` | string | Key usage, typically `sig` |
| `expiresAt` | ISO 8601 string | When the certificate expires — check for near-term expirations |
| `x5c` | string[] | X.509 certificate chain |

### CSR object (`list-csrs` / `get-csr`)

| Field | Type | Description |
|---|---|---|
| `id` | string | CSR ID |
| `csr` | string | Base64-encoded certificate signing request |
| `kty` | string | Key type, e.g. `RSA` |

### OAuth 2.0 client secret object (`list-secrets` / `get-secret`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Secret ID |
| `client_secret` | string | The secret value itself — treat as sensitive |
| `secret_hash` | string | Hash of the secret |
| `status` | string | `ACTIVE` or `INACTIVE` |

### Feature object (`list-features` / `get-feature`)

| Field | Type | Description |
|---|---|---|
| `name` | string | `USER_PROVISIONING` (Okta → app) or `INBOUND_PROVISIONING` (app → Okta) |
| `status` | string | `ENABLED` or `DISABLED` |
| `description` | string | Human-readable description of the feature |

### Federated claim object (`list-federated-claims` / `get-federated-claim`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Claim ID |
| `name` | string | Claim name emitted in the token |
| `expression` | string | Okta Expression Language expression evaluated at runtime |

### Scope consent grant object (`list-grants` / `get-grant`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Grant ID |
| `clientId` | string | Client ID of the app that received consent |
| `scopeId` | string | Okta scope granted, e.g. `okta.users.read` |
| `status` | string | Grant/token status |
| `userId` | string | User who granted consent, if user-scoped |

### Group push mapping object (`list-group-push-mappings` / `get-group-push-mapping`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Mapping ID |
| `sourceGroupId` | string | Okta group being pushed — pass to `okta-groups get <id>` |
| `targetGroupId` | string | ID of the corresponding group in the downstream app |
| `status` | string | Push status |
| `errorSummary` | string | Error message if the latest push failed |

### OAuth 2.0 refresh token object (`list-tokens` / `get-token`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Token ID |
| `clientId` | string | Client the token was issued to |
| `expiresAt` | ISO 8601 string | Token expiration |

### SAML metadata (`get-saml-metadata`)

Raw XML `EntityDescriptor` document — not JSON. Contains the app's signing certificate and SSO endpoint URLs; use this when configuring the app as a SAML SP pointed at Okta.

## Interpretation

### Sign-on modes

| Mode | Description |
|---|---|
| `SAML_2_0` | SAML 2.0 federation; Okta is the IdP |
| `OIDC_CLIENT` | OpenID Connect / OAuth 2.0 |
| `BOOKMARK` | Simple bookmark; no SSO |
| `BASIC_AUTH` | Basic HTTP auth |
| `AUTO_LOGIN` | SWA (Secure Web Authentication) auto-login |
| `BROWSER_PLUGIN` | SWA browser plugin |
| `SECURE_PASSWORD_STORE` | SWA with stored credentials |

### What to look for

- **Inactive apps with active assignments**: `status eq "INACTIVE"` combined with users returned by `get-users` — users are still assigned but cannot access the app.
- **Direct vs. group assignment**: `scope eq "USER"` in AppUser objects means the user was directly assigned; `scope eq "GROUP"` means access comes through a group. Direct assignments are harder to audit at scale.
- **Apps with `PUSH_NEW_USERS` feature**: These are provisioning-enabled apps; users appear automatically when assigned and are deprovisioned when removed from Okta.
- **Credentials scheme**: `SHARED_USERNAME_AND_PASSWORD` means all users share one set of credentials — a security concern worth flagging.
- **Expiring signing keys**: `list-keys` / `list-jwks` entries with a near-term `expiresAt` indicate a certificate rotation is needed soon — SSO will break once expired.
- **Failed group pushes**: `list-group-push-mappings` entries with a non-empty `errorSummary` mean the downstream app is out of sync with the mapped Okta group.
- **Inactive OAuth secrets**: `list-secrets` entries with `status eq "INACTIVE"` are retained but no longer usable — useful when auditing credential rotation history.
- **Broad scope grants**: `list-grants` entries with high-privilege `scopeId` values (e.g. `okta.users.manage`) and no `userId` indicate app-wide consent rather than a single user's delegated consent.

### Cross-skill references

- `id` → `okta-logs list --q <app_id>` to see log events where this app is a target (SSO issuances, access grants, user membership changes)
- `id` → appears in log events as `target[].id` where `target[].type eq "AppInstance"` — event type `application.user_membership.add/remove` tracks assignment changes
- AppUser `id` → `okta-users get <id>` for the user's full profile and current status
- Group assignment `id` → `okta-groups get-members <id>` to enumerate which users get access via that group
- `signOnMode eq "SAML_2_0"` apps generate `user.authentication.sso` log events when users access them
- `list-group-push-mappings` `sourceGroupId` → `okta-groups get <id>` / `get-members <id>` to see the Okta-side group being pushed
- `get-saml-metadata` needs a `kid` — get one from `list-keys`
