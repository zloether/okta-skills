---
name: okta-identity-providers
description: Read Okta identity provider (IdP) integrations, their key credentials, CSRs, signing keys, linked users, and social auth tokens. Use when asked about federation configuration, which external IdPs (SAML, OIDC, social) are configured, IdP certificates/signing keys, or which Okta users are linked to an external IdP.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-identity-providers/scripts/identity_providers.py <command> [options]
```

### list
List all identity providers. Supports search and type filtering.
```bash
uv run skills/okta-identity-providers/scripts/identity_providers.py list
uv run skills/okta-identity-providers/scripts/identity_providers.py list --q "Example SAML"
uv run skills/okta-identity-providers/scripts/identity_providers.py list --type SAML2
```

### get
Get a single IdP by ID.
```bash
uv run skills/okta-identity-providers/scripts/identity_providers.py get 0oa62bfdjnK55Z5x80h7
```

### list-keys / get-key
List or get IdP key credentials in the org-wide key store (`/idps/credentials/keys`). These are certificates uploaded for use by any IdP — not scoped to a specific IdP.
```bash
uv run skills/okta-identity-providers/scripts/identity_providers.py list-keys
uv run skills/okta-identity-providers/scripts/identity_providers.py get-key KmMo85SSsU7TZzOShcGb
```

### list-csrs / get-csr
List or get certificate signing requests generated for a specific IdP.
```bash
uv run skills/okta-identity-providers/scripts/identity_providers.py list-csrs 0oa62bfdjnK55Z5x80h7
uv run skills/okta-identity-providers/scripts/identity_providers.py get-csr 0oa62bfdjnK55Z5x80h7 1uEhyE65oV3H6KM9gYcN
```

### list-signing-keys / get-active-signing-key / get-signing-key
List, get the active one, or get a specific signing key credential for a specific IdP (`/idps/{idpId}/credentials/keys`). These are distinct from `list-keys`/`get-key` above, which cover the org-wide key store rather than keys scoped to one IdP.
```bash
uv run skills/okta-identity-providers/scripts/identity_providers.py list-signing-keys 0oa62bfdjnK55Z5x80h7
uv run skills/okta-identity-providers/scripts/identity_providers.py get-active-signing-key 0oa62bfdjnK55Z5x80h7
uv run skills/okta-identity-providers/scripts/identity_providers.py get-signing-key 0oa62bfdjnK55Z5x80h7 KmMo85SSsU7TZzOShcGb
```

### list-users / get-user
List users linked to an IdP, or get a specific linked user.
```bash
uv run skills/okta-identity-providers/scripts/identity_providers.py list-users 0oa62bfdjnK55Z5x80h7
uv run skills/okta-identity-providers/scripts/identity_providers.py list-users 0oa62bfdjnK55Z5x80h7 --q jackson --expand user
uv run skills/okta-identity-providers/scripts/identity_providers.py get-user 0oa62bfdjnK55Z5x80h7 00ub0oNGTSWTBKOLGLNR
```

### list-tokens
List social auth tokens minted for a linked user by an OIDC/social IdP during Social Login.
```bash
uv run skills/okta-identity-providers/scripts/identity_providers.py list-tokens 0oa62bfdjnK55Z5x80h7 00ub0oNGTSWTBKOLGLNR
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list`-prefixed commands return arrays; `get`-prefixed commands return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

Note: `get-active-signing-key` calls an Okta endpoint (`listActiveIdentityProviderSigningKey`) that is a `list` operation in the spec despite returning at most one key — it always returns an array (empty if the IdP has no active signing key, since Okta returns `204 No Content` in that case).

## Output Schema

### IdP object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique key for the IdP |
| `name` | string | Unique, human-readable name for the IdP |
| `type` | string | IdP type, e.g. `SAML2`, `OIDC`, `GOOGLE`, `MICROSOFT`, `FACEBOOK`, `X509` — see Okta's IdP type reference for the full list |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `protocol` | object | Protocol-specific settings (endpoints, bindings, signing/encryption algorithms) — shape varies by `type` (SAML 2.0, OAuth 2.0, OIDC, mTLS, ID verification) |
| `policy` | object | Account link policy, provisioning policy (JIT/mapping), and max clock skew settings |
| `properties` | object | Protocol-specific extra properties, e.g. LinkedIn/GitHub API fields |
| `issuerMode` | string | Whether Okta uses the org's default domain or a custom domain as the issuer for this IdP |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |
| `_links.users.href` | string | Link to this IdP's linked users (`list-users`) |
| `_links.keys.href` | string | Link to this IdP's signing keys |

### IdP key credential object (`list-keys` / `get-key` / `list-signing-keys` / `get-active-signing-key` / `get-signing-key`)

| Field | Type | Description |
|---|---|---|
| `kid` | string | Unique identifier for the key — use with `get-key` or `get-signing-key` |
| `kty` | string | Cryptographic algorithm family, e.g. `RSA` |
| `use` | string | Intended use of the public key, e.g. `sig` |
| `x5c` | string[] | X.509 certificate chain |
| `x5t#S256` | string | SHA-256 thumbprint of the DER-encoded certificate |
| `expiresAt` | ISO 8601 string | Certificate expiration — check against the current date to flag expiring/expired keys |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### IdP CSR object (`list-csrs` / `get-csr`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the CSR |
| `csr` | string | Base64-encoded CSR in DER format |
| `kty` | string | Cryptographic algorithm family for the CSR's keypair |
| `created` | ISO 8601 string | When the CSR was generated |
| `_links.publish.href` | string | Endpoint to publish this CSR with a signed certificate (write operation, not covered by this read-only skill) |

### IdP linked user object (`list-users` / `get-user`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique key of the IdP-linked user record |
| `externalId` | string | The IdP-specific identifier for the user (e.g. SAML NameID, social provider subject) |
| `profile` | object | IdP-specific profile attributes as received from the IdP (varies per IdP configuration) |
| `_links.idp.href` | string | Link back to the parent IdP |
| `_links.user.href` | string | Link to the linked Okta user — extract the ID and pass to `okta-users get <id>` |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Social auth token object (`list-tokens`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the token |
| `token` | string | The raw token value issued by the social provider |
| `tokenType` | string | Token type per the OAuth Token Exchange spec, e.g. `urn:ietf:params:oauth:token-type:access_token` |
| `tokenAuthScheme` | string | Auth scheme defined by the social provider, e.g. `Bearer` |
| `scopes` | string[] | Scopes the token is valid for |
| `expiresAt` | ISO 8601 string | Token expiration |

## Interpretation

### What to look for

- **Inactive IdPs still routed to**: An IdP with `status: INACTIVE` can still be referenced by an `IDP_DISCOVERY` policy's routing rules in `okta-policies` — cross-check before assuming an inactive IdP is fully decommissioned; users hitting that route will fail to authenticate.
- **Expiring or expired signing keys**: Compare `expiresAt` on `list-signing-keys` / `get-active-signing-key` results against the current date. An IdP whose active signing key has expired (or is about to) will break inbound/outbound signature validation for that IdP.
- **No active signing key**: If `get-active-signing-key` returns an empty array for an IdP that requires Okta to sign outbound requests/assertions (e.g. SAML SP-initiated flows), that IdP integration is likely broken or was never fully configured.
- **Orphaned linked users**: An `IdentityProviderApplicationUser` (`list-users`/`get-user`) whose `_links.user` target 404s in `okta-users get` indicates the underlying Okta user was deleted without unlinking the federation record — stale data worth flagging.
- **Org-wide vs. per-IdP keys**: `list-keys`/`get-key` (the org-wide key store) can contain certificates not currently attached to any IdP's `protocol.credentials`. Cross-reference a key's `kid` against each IdP's `get` output to determine if it's actually in use before assuming it's live.
- **Social auth token exposure**: `list-tokens` returns raw, usable tokens for the external provider (e.g. a Google or Microsoft access token). Treat this output as sensitive — it grants whatever access the token's `scopes` allow directly against the third-party provider, not just against Okta.

### Cross-skill references

- IdP linked user's Okta-side ID (from `_links.user.href` on `list-users`/`get-user`) → `okta-users get <id>` for the corresponding Okta profile
- IdP `id` referenced in a policy's routing conditions (`IDP_DISCOVERY` policy type) → check `skills/okta-policies/SKILL.md`; use `okta-policies list --type IDP_DISCOVERY` and `get-rules` to see which rules route to this IdP
- IdP `id` in an `okta-users get-idps <user_id>` result → this skill's `get <idp_id>` for full IdP configuration
- IdP sign-on/link events (`user.authentication.auth_via_IDP`, `application.provision.*`) → `okta-logs` filtered with `eventType sw "user.authentication"` or by `target[].id` matching the IdP or linked-user ID
