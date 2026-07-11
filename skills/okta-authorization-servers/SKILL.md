---
name: okta-authorization-servers
description: Read Okta authorization servers including their custom scopes, claims, policies, policy rules, signing keys, registered clients, and refresh tokens. Use when asked about OAuth/OIDC authorization servers, custom scopes or claims, access/refresh token policies, authorization server signing keys, or which OAuth clients are registered with an authorization server.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py <command> [options]
```

### list
List all authorization servers.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list --q api
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list --limit 50
```

### get
Get a single authorization server by ID.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get ausatv1u4d2y1F1Nu0h7
```

### list-associated-servers
List authorization servers trusted by (or trusting) a given authorization server.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-associated-servers ausatv1u4d2y1F1Nu0h7
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-associated-servers ausatv1u4d2y1F1Nu0h7 --trusted true
```

### list-claims / get-claim
List or get custom token claims for an authorization server.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-claims ausatv1u4d2y1F1Nu0h7
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-claim ausatv1u4d2y1F1Nu0h7 <claimId>
```

### list-clients
List OAuth clients registered with an authorization server.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-clients ausatv1u4d2y1F1Nu0h7
```

### list-tokens / get-token
List or get refresh tokens issued to a client on an authorization server.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-tokens ausatv1u4d2y1F1Nu0h7 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-tokens ausatv1u4d2y1F1Nu0h7 0oa1ab2cd3EF4GH5IJ6K --expand scope
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-token ausatv1u4d2y1F1Nu0h7 0oa1ab2cd3EF4GH5IJ6K <tokenId>
```

### list-keys / get-key
List or get the signing keys used by an authorization server to sign access tokens.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-keys ausatv1u4d2y1F1Nu0h7
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-key ausatv1u4d2y1F1Nu0h7 <kid>
```

### list-policies / get-policy
List or get the access policies attached to an authorization server.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-policies ausatv1u4d2y1F1Nu0h7
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-policy ausatv1u4d2y1F1Nu0h7 <policyId>
```

### list-policy-rules / get-policy-rule
List or get the rules within an authorization server policy.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-policy-rules ausatv1u4d2y1F1Nu0h7 <policyId>
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-policy-rule ausatv1u4d2y1F1Nu0h7 <policyId> <ruleId>
```

### list-resource-server-keys / get-resource-server-key
List or get the resource server's own public JWKs (used to validate tokens presented to a resource server, distinct from the authorization server's signing keys).
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-resource-server-keys ausatv1u4d2y1F1Nu0h7
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-resource-server-key ausatv1u4d2y1F1Nu0h7 <keyId>
```

### list-scopes / get-scope
List or get the custom scopes defined on an authorization server.
```bash
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-scopes ausatv1u4d2y1F1Nu0h7
uv run skills/okta-authorization-servers/scripts/authorization_servers.py list-scopes ausatv1u4d2y1F1Nu0h7 --q read
uv run skills/okta-authorization-servers/scripts/authorization_servers.py get-scope ausatv1u4d2y1F1Nu0h7 <scopeId>
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list*` operations return an array. `get*` operations return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### Authorization server object (`list`, `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Authorization server ID (e.g. `ausatv1u4d2y1F1Nu0h7`) |
| `name` | string | Human-readable name |
| `audiences` | array | Intended token audiences (resource identifiers) |
| `issuer` | string | The `iss` claim value clients validate against |
| `issuerMode` | string | `ORG_URL`, `CUSTOM_URL`, or `DYNAMIC` |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `credentials.signing` | object | `kid` (active signing key), `rotationMode`, `lastRotated`, `nextRotation` |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Claim object (`list-claims`, `get-claim`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Claim ID |
| `name` | string | Claim name as it appears in issued tokens |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `claimType` | string | `IDENTITY` (ID token) or `RESOURCE` (access token) |
| `valueType` | string | `EXPRESSION`, `GROUPS`, or `SYSTEM` |
| `value` | string | Okta Expression Language expression or group filter, depending on `valueType` |
| `alwaysIncludeInToken` | boolean | Whether the claim is included regardless of scope |
| `conditions.scopes` | array | Scopes that must be requested for this claim to be included (when not always-included) |

### Policy object (`list-policies`, `get-policy`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Policy ID |
| `name` | string | Human-readable policy name |
| `type` | string | `OAUTH_AUTHORIZATION_POLICY` |
| `priority` | integer | Evaluation order; lower number = higher priority |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `system` | boolean | Whether this is Okta's built-in default policy (cannot be deleted) |
| `conditions.clients` | object | Which OAuth clients this policy applies to |

### Policy rule object (`list-policy-rules`, `get-policy-rule`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Rule ID |
| `name` | string | Human-readable rule name |
| `priority` | integer | Evaluation order within the policy |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `conditions.grantTypes.include` | array | OAuth grant types this rule applies to (e.g. `authorization_code`, `client_credentials`) |
| `conditions.scopes.include` | array | Scopes this rule applies to |
| `conditions.people` | object | User/group conditions (for grant types involving a user) |
| `actions.token.accessTokenLifetimeMinutes` | integer | Access token lifetime granted by this rule |
| `actions.token.refreshTokenLifetimeMinutes` / `refreshTokenWindowMinutes` | integer | Refresh token lifetime and idle window |

### Scope object (`list-scopes`, `get-scope`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Scope ID |
| `name` | string | Scope name as requested in the `scope` parameter (e.g. `orders:read`) |
| `displayName` | string | Human-readable name shown on the consent screen |
| `default` | boolean | Whether this scope is granted when no `scope` parameter is specified |
| `optional` | boolean | Whether this scope can be omitted from a request without causing an error |
| `system` | boolean | Whether this is a built-in OIDC scope (e.g. `openid`, `profile`) |
| `consent` | string | `REQUIRED` or `IMPLICIT` — whether end-user consent is prompted |

### Key object (`list-keys`, `get-key`, `list-resource-server-keys`, `get-resource-server-key`)

| Field | Type | Description |
|---|---|---|
| `kid` | string | Key ID; matches the `kid` header on tokens signed with this key |
| `kty` | string | Key type, `RSA` |
| `alg` | string | Signing algorithm, `RS256` |
| `use` | string | `sig` (authorization server signing keys) or `enc` (resource server keys) |
| `status` | string | `ACTIVE`, `NEXT` (pending rotation), or `EXPIRED` (signing keys); `ACTIVE`/`INACTIVE` (resource server keys) |

### Client object (`list-clients`)

| Field | Type | Description |
|---|---|---|
| `client_id` | string | OAuth client ID; cross-reference with `okta-apps` to find the owning app |
| `client_name` | string | Human-readable client name |
| `client_uri` | string | Client's homepage URL |

### Refresh token object (`list-tokens`, `get-token`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Token ID |
| `clientId` | string | OAuth client the token was issued to |
| `userId` | string | Okta user ID the token was issued for; use with `okta-users get <id>` |
| `scopes` | array | Scopes granted to this token |
| `status` | string | `ACTIVE` |
| `expiresAt` | ISO 8601 string | When the token expires (absent if it doesn't expire) |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

## Interpretation

### What to look for

- **Custom scopes with `consent eq "IMPLICIT"`**: No user consent screen is shown when this scope is requested — combined with a broad `conditions.clients` policy match, this can grant sensitive access silently.
- **Policy rules with long `accessTokenLifetimeMinutes`**: A long-lived access token issued under a permissive rule (broad `conditions.scopes.include`, no group restriction) increases the blast radius of a leaked token.
- **`client_credentials` grant type rules with no client restriction**: `conditions.grantTypes.include` containing `client_credentials` with an empty/wildcard `conditions.clients` means any registered service client can mint machine-to-machine tokens under that rule.
- **Claims with `valueType eq "EXPRESSION"`**: The `value` field contains an Okta Expression Language expression — read it to understand exactly what's being embedded in tokens (e.g. `user.profile` fields that shouldn't be exposed to a given audience).
- **Signing keys with `status eq "NEXT"`**: A rotation is pending; tokens signed with the current `ACTIVE` key remain valid until it moves to `EXPIRED`. Useful when debugging JWT validation failures during a rotation window.
- **`isGenerallyAvailable: false` in the spec**: Nearly every operation under this API path carries this flag in Okta's OpenAPI spec even though the feature is fully GA in practice — don't treat it as an availability warning for this skill.

### Cross-skill references

- `id` (authorization server) → appears as the audience/issuer context for `okta-policies list --type OAUTH_AUTHORIZATION_POLICY`-style access policies; also referenced by app OIDC configuration in `okta-apps get <id>`
- `list-clients` `client_id` → `okta-apps get <appId>` to find the application that owns this OAuth client (the app's `credentials.oauthClient.client_id` matches)
- `list-tokens` / `get-token` `userId` → `okta-users get <userId>` to see who the refresh token belongs to; `okta-users get-grants <userId>` to see the scope consent that produced it
- Policy rule `conditions.people.groups.include[]` → `okta-groups get-members <groupId>` to see which users this token policy rule applies to
- A denied or unexpected token request in `okta-logs` (`eventType eq "app.oauth2.token.grant"` or similar) → cross-reference the authorization server's `list-policies`/`list-policy-rules` to see which rule should have matched
