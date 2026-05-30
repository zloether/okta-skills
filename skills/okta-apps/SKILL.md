---
name: okta-apps
description: Read Okta application integrations and app assignments. Use when asked about applications, app integrations, which apps a user or group can access, which users or groups are assigned to an app, or app configuration details.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-apps/scripts/apps.py <command> [options]
```

### list
List applications, optionally filtered.
```bash
python skills/okta-apps/scripts/apps.py list
python skills/okta-apps/scripts/apps.py list --filter 'status eq "ACTIVE"'
python skills/okta-apps/scripts/apps.py list --filter 'name eq "workday"'
```

### get
Get a single application by ID.
```bash
python skills/okta-apps/scripts/apps.py get 0oa1ab2cd3EF4GH5IJ6K
```

### get-users
List users assigned to an application.
```bash
python skills/okta-apps/scripts/apps.py get-users 0oa1ab2cd3EF4GH5IJ6K
```

### get-groups
List groups assigned to an application.
```bash
python skills/okta-apps/scripts/apps.py get-groups 0oa1ab2cd3EF4GH5IJ6K
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. List operations return arrays; `get` returns a single app object. `get-users` returns AppUser objects (include a `credentials` and `profile` field in addition to user info). Errors are JSON with an `error` key on stderr; exit code 1.
