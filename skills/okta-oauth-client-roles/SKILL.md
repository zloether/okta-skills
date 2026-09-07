---
name: okta-oauth-client-roles
description: Read Okta admin role assignments on OAuth 2.0 client apps (service apps). Use when asked which admin roles a service app/OAuth client has, whether a client's role is scoped to specific apps or groups, or auditing non-human/machine-to-machine admin access.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-oauth-client-roles/scripts/oauth_client_roles.py <command> [options]
```

### list
List all admin role assignments for an OAuth 2.0 client app.
```bash
uv run skills/okta-oauth-client-roles/scripts/oauth_client_roles.py list 0oa1ab2cd3EF4GH5IJ6K
```

### get
Get a specific role assignment for a client app.
```bash
uv run skills/okta-oauth-client-roles/scripts/oauth_client_roles.py get 0oa1ab2cd3EF4GH5IJ6K <role_assignment_id>
```

### list-app-targets
List the OIN app targets an `APP_ADMIN` role assignment is scoped to.
```bash
uv run skills/okta-oauth-client-roles/scripts/oauth_client_roles.py list-app-targets 0oa1ab2cd3EF4GH5IJ6K <role_assignment_id> --limit 50
```

### list-group-targets
List the group targets a `USER_ADMIN`/`HELP_DESK_ADMIN`/`GROUP_MEMBERSHIP_ADMIN` role assignment is scoped to.
```bash
uv run skills/okta-oauth-client-roles/scripts/oauth_client_roles.py list-group-targets 0oa1ab2cd3EF4GH5IJ6K <role_assignment_id> --limit 50
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

JSON to stdout. `list`, `list-app-targets`, and `list-group-targets` return arrays; `get` returns a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### list / get

| Field | Type | Description |
|---|---|---|
| `id` | string | Role assignment ID |
| `type` | string | Standard role type (e.g. `APP_ADMIN`, `SUPER_ADMIN`, `USER_ADMIN`) or `CUSTOM` |
| `status` | string | Role assignment status |
| `label` | string | Human-readable label for the assignment |
| `assignmentType` | string | How the role was assigned (e.g. `CLIENT`) |
| `_embedded.targets` | object | Present when the role is scoped to specific apps/groups rather than org-wide; see `list-app-targets` / `list-group-targets` |

### list-app-targets / list-group-targets

Each returns an array of the OIN app catalog entries or group resources the client's scoped role applies to (group objects match `okta-groups get`'s schema). An empty array on a scoped role means the assignment currently grants no effective access.

## Interpretation

### What to look for

- **Client apps with admin roles are non-human, machine-to-machine actors.** Any role assignment here means a service app (via client-credentials OAuth, not a person) can act with the assigned admin privileges — treat unexpected or broad assignments (e.g. `SUPER_ADMIN`, `ORG_ADMIN`) as higher risk than the same role on a human user, since there's no interactive login step to notice an intrusion.
- **Scoped vs. org-wide roles**: If `_embedded.targets` is present on a role, it only applies to the apps/groups returned by `list-app-targets` / `list-group-targets`. If absent, the role applies org-wide.
- **Unfamiliar or unused clients holding roles**: Cross-reference the `clientId` with `okta-apps get <clientId>` (service apps are also App instances) to confirm the app is still active and understand what it's for.
- **`assignmentType`**: Distinguishes a role granted directly to this client (`CLIENT`) from other assignment paths surfaced by other skills (e.g. `GROUP` via `okta-groups list-roles`).

### Cross-skill references

- The client app itself → `okta-apps get <clientId>` for the service app's full configuration, and `okta-apps list-tokens <clientId>` / `list-grants <clientId>` for its issued tokens and OAuth scope grants
- `list-app-targets` results → `okta-apps get <id>` for full app details on each targeted OIN app instance
- `list-group-targets` results → `okta-groups get <id>` for full details on each targeted group
- Role assignment changes on client apps appear in `okta-logs` as `application.lifecycle.*` or `role.*` events; `target[].id` includes the `clientId` or role assignment `id`
