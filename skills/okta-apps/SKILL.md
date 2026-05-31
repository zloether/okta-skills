---
name: okta-apps
description: Read Okta application integrations and app assignments. Use when asked about applications, app integrations, which apps a user or group can access, which users or groups are assigned to an app, or app configuration details.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
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
```

### get
Get a single application by ID.
```bash
uv run skills/okta-apps/scripts/apps.py get 0oa1ab2cd3EF4GH5IJ6K
```

### get-users
List users assigned to an application.
```bash
uv run skills/okta-apps/scripts/apps.py get-users 0oa1ab2cd3EF4GH5IJ6K
```

### get-groups
List groups assigned to an application.
```bash
uv run skills/okta-apps/scripts/apps.py get-groups 0oa1ab2cd3EF4GH5IJ6K
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

### Group assignment object (`get-groups`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta group ID |
| `priority` | integer | Assignment priority (lower = higher priority) |
| `lastUpdated` | ISO 8601 string | When the group assignment was last modified |

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

### Cross-skill references

- `id` → `okta-logs list --q <app_id>` to see log events where this app is a target (SSO issuances, access grants, user membership changes)
- `id` → appears in log events as `target[].id` where `target[].type eq "AppInstance"` — event type `application.user_membership.add/remove` tracks assignment changes
- AppUser `id` → `okta-users get <id>` for the user's full profile and current status
- Group assignment `id` → `okta-groups get-members <id>` to enumerate which users get access via that group
- `signOnMode eq "SAML_2_0"` apps generate `user.authentication.sso` log events when users access them
