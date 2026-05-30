---
name: okta-users
description: Read Okta user profiles, status, and attributes. Use when asked about users, user accounts, user status (active/suspended/deprovisioned), user profile fields, password state, or to look up a specific user by email address, login, or ID.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-users/scripts/users.py <command> [options]
```

### list
List users, optionally filtered.
```bash
python skills/okta-users/scripts/users.py list
python skills/okta-users/scripts/users.py list --filter 'status eq "ACTIVE"'
python skills/okta-users/scripts/users.py list --filter 'profile.department eq "Engineering"' --limit 100
```

### get
Get a single user by ID or login (email address).
```bash
python skills/okta-users/scripts/users.py get user@example.com
python skills/okta-users/scripts/users.py get 00u1ab2cd3EF4GH5IJ6K
```

### search
Search users by name or email using a keyword query.
```bash
python skills/okta-users/scripts/users.py search "Jane Smith"
python skills/okta-users/scripts/users.py search "jane@example"
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
