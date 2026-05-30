---
name: okta-logs
description: Read Okta system log events including authentication attempts, admin actions, user lifecycle events, and security alerts. Use when asked about audit logs, login history, failed authentications, MFA events, admin activity, policy evaluations, or any event history in the org.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-logs/scripts/logs.py <command> [options]
```

### list
Fetch log events, optionally scoped by time range, event type, or filter expression.
```bash
# Last 100 events
python skills/okta-logs/scripts/logs.py list

# Events since a specific time
python skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z

# Time range
python skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z --until 2024-01-02T00:00:00Z

# Filter by event type (use --filter with a SCIM expression)
python skills/okta-logs/scripts/logs.py list --filter 'eventType eq "user.session.start"'
python skills/okta-logs/scripts/logs.py list --filter 'eventType eq "user.authentication.auth_via_mfa"'

# Filter by outcome
python skills/okta-logs/scripts/logs.py list --filter 'outcome.result eq "FAILURE"'

# Keyword search
python skills/okta-logs/scripts/logs.py list --q "user@example.com"

# Sort order
python skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z --sort-order DESCENDING

# Limit results
python skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z --limit 500
```

## Common Event Types

| Event Type | Description |
|---|---|
| `user.session.start` | User sign-in |
| `user.session.end` | User sign-out |
| `user.authentication.auth_via_mfa` | MFA authentication |
| `user.authentication.sso` | SSO authentication to an app |
| `user.account.lock` | Account locked |
| `user.account.unlock` | Account unlocked |
| `user.lifecycle.activate` | User activated |
| `user.lifecycle.deactivate` | User deactivated |
| `policy.evaluate_sign_on` | Sign-on policy evaluated |
| `system.agent.start` | AD/LDAP agent started |

### login-failures
Fetch all login failures and denials, grouped by outcome and event type. Makes two API calls (one per outcome) since Okta cannot OR across outcome values in a single filter. Defaults to the last 24 hours if `--since` is not provided.

```bash
# Last 24 hours (default)
python skills/okta-logs/scripts/logs.py login-failures

# Specific time range
python skills/okta-logs/scripts/logs.py login-failures --since 2024-01-01T00:00:00Z --until 2024-01-02T00:00:00Z

# Scoped to a single user
python skills/okta-logs/scripts/logs.py login-failures --user user@example.com

# Limit events per outcome
python skills/okta-logs/scripts/logs.py login-failures --limit 200
```

Returns a JSON object with a `summary` (total count, counts by outcome and event type, query window) and an `events` array containing all matching log events.

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list` returns an array of LogEvent objects. `login-failures` returns `{summary, events}`. Each event includes `eventType`, `published` (ISO 8601 timestamp), `actor`, `target`, `outcome`, `client`, and `authenticationContext` fields. Errors are JSON with an `error` key on stderr; exit code 1.

## Common Event Types

| Event Type | Description |
|---|---|
| `user.session.start` | User sign-in |
| `user.session.end` | User sign-out |
| `user.authentication.auth_via_mfa` | MFA authentication |
| `user.authentication.sso` | SSO authentication to an app |
| `user.account.lock` | Account locked |
| `user.account.unlock` | Account unlocked |
| `user.lifecycle.activate` | User activated |
| `user.lifecycle.deactivate` | User deactivated |
| `policy.evaluate_sign_on` | Sign-on policy evaluated |
| `system.agent.start` | AD/LDAP agent started |

## Notes

- `--since` and `--until` accept ISO 8601 format: `2024-01-01T00:00:00Z`
- Without `--since`, `list` defaults to the last 7 days; `login-failures` defaults to the last 24 hours
- Large time ranges may return many events; use `--limit` to cap results
- To filter by event type in `list`, use `--filter 'eventType eq "<type>"'` — there is no separate `--event-type` flag
