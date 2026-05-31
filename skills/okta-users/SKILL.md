---
name: okta-users
description: Read Okta user profiles, status, and attributes. Use when asked about users, user accounts, user status (active/suspended/deprovisioned), user profile fields, password state, or to look up a specific user by email address, login, or ID.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-users/scripts/users.py <command> [options]
```

### list
List users, optionally filtered.
```bash
uv run skills/okta-users/scripts/users.py list
uv run skills/okta-users/scripts/users.py list --filter 'status eq "ACTIVE"'
uv run skills/okta-users/scripts/users.py list --filter 'profile.department eq "Engineering"' --limit 100
```

### get
Get a single user by ID or login (email address).
```bash
uv run skills/okta-users/scripts/users.py get user@example.com
uv run skills/okta-users/scripts/users.py get 00u1ab2cd3EF4GH5IJ6K
```

### search
Search users by name or email using a keyword query.
```bash
uv run skills/okta-users/scripts/users.py search "Jane Smith"
uv run skills/okta-users/scripts/users.py search "jane@example"
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. List operations return an array of user objects. `get` returns a single user object. Errors are JSON with an `error` key written to stderr; exit code 1.

## Filter Reference

Common SCIM filter expressions for `--filter`:
- `status eq "ACTIVE"` — active users only
- `status eq "DEPROVISIONED"` — deprovisioned users
- `profile.department eq "Engineering"` — by department
- `lastUpdated gt "2024-01-01T00:00:00.000Z"` — recently updated

## Output Schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta user ID (e.g. `00u1ab2cd3EF4GH5IJ6K`); use this to look up the user in other skills |
| `status` | string | Current account state (see Status Values below) |
| `profile.login` | string | Username / email address used to sign in |
| `profile.email` | string | Primary email address |
| `profile.firstName` / `profile.lastName` | string | Display name components |
| `profile.department` | string | Department, if populated |
| `profile.mobilePhone` | string | Mobile phone number, if populated |
| `credentials.password.value` | — | Never populated in API responses; presence of the key indicates a password is set |
| `credentials.provider.type` | string | `OKTA`, `ACTIVE_DIRECTORY`, `LDAP`, `FEDERATION`, `SOCIAL` — where the user authenticates |
| `credentials.provider.name` | string | Name of the external provider, if applicable |
| `lastLogin` | ISO 8601 string | When the user last signed in |
| `lastUpdated` | ISO 8601 string | When the user record was last modified |
| `passwordChanged` | ISO 8601 string | When the password was last changed |
| `statusChanged` | ISO 8601 string | When the status last changed |
| `activated` | ISO 8601 string | When the account was first activated |
| `_links` | object | HAL links for lifecycle actions (activate, deactivate, suspend, etc.) — presence indicates the action is available |

## Interpretation

### Status values

| Status | Meaning |
|---|---|
| `ACTIVE` | User can sign in normally |
| `STAGED` | Account created but not yet activated; no activation email sent |
| `PROVISIONED` | Activation email sent; user has not yet completed activation |
| `RECOVERY` | User has a pending password reset or account unlock |
| `PASSWORD_EXPIRED` | Password is expired; user must reset before signing in |
| `LOCKED_OUT` | Account locked due to too many failed sign-in attempts; admin must unlock |
| `SUSPENDED` | Admin has suspended the account; user cannot sign in |
| `DEPROVISIONED` | Account deactivated; user cannot sign in and the account cannot be reactivated to ACTIVE directly |

### What to look for

- **Locked out users**: `status eq "LOCKED_OUT"` — correlate with `okta-logs login-failures --user <email>` to see the failure pattern
- **Stale accounts**: filter by `lastLogin` being very old or null combined with `status eq "ACTIVE"` — potential access hygiene issue
- **Federated vs. Okta-managed**: `credentials.provider.type` distinguishes users who authenticate via AD/LDAP/SAML from those managed directly in Okta; federated users cannot have their passwords reset in Okta
- **Recently deprovisioned**: filter by `status eq "DEPROVISIONED"` and `statusChanged gt "<date>"` to audit recent offboarding

### Cross-skill references

- `id` → use as the actor ID when correlating with `okta-logs list --q <id>` or `okta-logs login-failures --user <login>`
- `id` → `okta-groups get-members` results contain full user objects; match on `id` to confirm group membership
- `credentials.provider.type eq "ACTIVE_DIRECTORY"` → the user's authoritative source is AD; use `okta-logs list --filter 'eventType eq "user.authentication.auth_via_AD"'` to see authentication events
