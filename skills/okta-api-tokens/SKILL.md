---
name: okta-api-tokens
description: Read Okta API token metadata. Use when asked about API tokens, which tokens exist in the org, who created them, when they expire, or whether a token is scoped to a network zone.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-api-tokens/scripts/api_tokens.py <command> [options]
```

### list
List metadata for all active API tokens in the org.
```bash
uv run skills/okta-api-tokens/scripts/api_tokens.py list
```

### get
Get a single API token's metadata by ID.
```bash
uv run skills/okta-api-tokens/scripts/api_tokens.py get 00Tabcdefg1234567890
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

## Output

JSON to stdout. `list` returns an array of token metadata objects; `get` returns a single object. Errors are JSON with an `error` key on stderr; exit code 1.

Note: this is metadata only — the token secret value is never returned by the API (it's shown once, at creation time, outside this endpoint).

## Output Schema

| Field | Type | Description |
|---|---|---|
| `id` | string | API token ID (e.g. `00Tabcdefg1234567890`) |
| `name` | string | Human-readable label for the token |
| `userId` | string | ID of the user the token was created by/acts as; pass to `okta-users get <id>` |
| `clientName` | string | Name of the client that created the token, if applicable |
| `created` | ISO 8601 string | When the token was created |
| `expiresAt` | ISO 8601 string | When the token expires |
| `lastUpdated` | ISO 8601 string | When the token metadata was last modified |
| `tokenWindow` | string | ISO 8601 duration — how long the token stays valid after last use |
| `network.connection` | string | Network condition type applied to the token (e.g. `ANYWHERE`, `ZONE`) |
| `network.include` | string[] | Network zone IDs the token is restricted to, if `connection` is zone-scoped |
| `network.exclude` | string[] | Network zone IDs explicitly excluded |

## Interpretation

### What to look for

- **Tokens with no `network` restriction**: `network.connection eq "ANYWHERE"` (or absent) means the token can be used from any IP — a broader blast radius if leaked than a zone-restricted token.
- **A token acting as a highly-privileged user**: Since a token is unscoped and inherits all of `userId`'s permissions, check `okta-users get <userId>` (and any admin role assignments) to understand what a compromised token could do.
- **Stale tokens near `expiresAt`**: Tokens are typically long-lived; one close to expiring that's still actively used elsewhere may need rotation before it lapses.
- **Unrecognized `clientName` or `name`**: Tokens created by unfamiliar automation are worth investigating — cross-reference with `okta-logs` for the token's creation event.

### Cross-skill references

- `userId` → `okta-users get <userId>` for the full profile of the user this token acts as
- `network.include[]` / `network.exclude[]` → `okta-network-zones get <id>` to see the actual IP ranges the token is restricted to or blocked from
- Token creation/revocation appears in `okta-logs` as `system.api_token.create` / `system.api_token.revoke` events; `target[].id` is the token `id`
- API calls made with a given token appear in `okta-logs` events with `authenticationContext.credentialType eq "APITOKEN"` — cross-reference `actor.id` with `userId` here
