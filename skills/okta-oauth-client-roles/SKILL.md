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
uv run skills/okta-oauth-client-roles/scripts/oauth_client_roles.py list-app-targets 0oa1ab2cd3EF4GH5IJ6K <role_assignment_id> --page-size 200
```

### list-group-targets
List the group targets a `USER_ADMIN`/`HELP_DESK_ADMIN`/`GROUP_MEMBERSHIP_ADMIN` role assignment is scoped to.
```bash
uv run skills/okta-oauth-client-roles/scripts/oauth_client_roles.py list-group-targets 0oa1ab2cd3EF4GH5IJ6K <role_assignment_id> --limit 50
```

On both target commands, `--limit` caps total results and is also sent as the API `limit` (page size) when `--page-size` isn't given; `--page-size 1-200` sets items per request (spec default 20). `list` and `get` have no pagination params.

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

**Required OAuth scope** (`OKTA_CLIENT_SCOPES`): `okta.roles.read`. A `401`/`403` usually means the scope was not granted to the OAuth app.

## Output

JSON to stdout. `list`, `list-app-targets`, and `list-group-targets` return arrays; `get` returns a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### list / get

| Field | Type | Description |
|---|---|---|
| `id` | string | Role assignment ID |
| `type` | string | Role type: standard (`SUPER_ADMIN`, `ORG_ADMIN`, `APP_ADMIN`, `USER_ADMIN`, `HELP_DESK_ADMIN`, `GROUP_MEMBERSHIP_ADMIN`, `READ_ONLY_ADMIN`, `REPORT_ADMIN`, `API_ACCESS_MANAGEMENT_ADMIN`), IAM-based (`ACCESS_CERTIFICATIONS_ADMIN`, `ACCESS_REQUESTS_ADMIN`, `WORKFLOWS_ADMIN`), or `CUSTOM` |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `label` | string | Human-readable label for the assignment |
| `assignmentType` | string | How the role was assigned: `CLIENT` (directly to this client), `GROUP`, or `USER` |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |
| `role` / `resource-set` | string | **`CUSTOM` and IAM-based types (`ACCESS_CERTIFICATIONS_ADMIN`, `ACCESS_REQUESTS_ADMIN`, `WORKFLOWS_ADMIN`) only** — role ID and resource set ID; `id` is then the binding ID. Resolve with `okta-iam get <role>` / `get-resource-set <resource-set>` |
| `_embedded.targets` | object | Optional (standard roles). `{groups: [...], catalog: {apps: [...]}}` embedded targets; when it is populated versus omitted is unverified — use `list-app-targets` / `list-group-targets` to read targets authoritatively |

### list-app-targets / list-group-targets

`list-group-targets` returns group objects (match `okta-groups get`'s schema). `list-app-targets` returns OIN catalog entries: `name` (app key), `displayName`, `category`, `status` (`ACTIVE`/`INACTIVE`), `signOnModes`, `verificationStatus`, `website`, `features`, `lastUpdated`. `id` is present only for apps not in the OIN catalog (custom app instances).

An empty array means the role is **not scoped to specific targets** (per the spec for group targets: "If the role isn't scoped to specific group targets, Okta returns an empty array") — treat it as org-wide for that target type, not as "no access". The same applies to app targets, though that wording is not in the spec for that endpoint (unverified).

## Interpretation

### What to look for

- **Client apps with admin roles are non-human, machine-to-machine actors.** Any role assignment here means a service app (via client-credentials OAuth, not a person) can act with the assigned admin privileges — treat unexpected or broad assignments (e.g. `SUPER_ADMIN`, `ORG_ADMIN`) as higher risk than the same role on a human user, since there's no interactive login step to notice an intrusion.
- **Scoped vs. org-wide roles**: a role is scoped only if `list-app-targets` (for `APP_ADMIN`) or `list-group-targets` (for `USER_ADMIN`/`HELP_DESK_ADMIN`/`GROUP_MEMBERSHIP_ADMIN`) returns entries; an empty array means unscoped (spec-backed for group targets; unverified for app targets). Don't rely on `_embedded.targets` alone.
- **Bulk audit**: `list` once per client — there is no org-wide "all client role assignments" endpoint. To find all clients holding roles, enumerate service apps with `okta-apps list` and run `list <clientId>` for each; only call the target commands for `APP_ADMIN` / group-scoped types.
- **Unfamiliar or unused clients holding roles**: Cross-reference the `clientId` with `okta-apps get <clientId>` (service apps are also App instances) to confirm the app is still active and understand what it's for.
- **`assignmentType`**: Distinguishes a role granted directly to this client (`CLIENT`) from other assignment paths surfaced by other skills (e.g. `GROUP` via `okta-groups list-roles`).

### Cross-skill references

- The client app itself → `okta-apps get <clientId>` for the service app's full configuration, and `okta-apps list-tokens <clientId>` / `list-grants <clientId>` for its issued tokens and OAuth scope grants
- `list-app-targets` results → `okta-apps get <id>` only when `id` is present (non-OIN app instances); OIN catalog entries have only `name` (the app key), with no instance ID
- `list-group-targets` results → `okta-groups get <id>` for full details on each targeted group
- Role assignment changes on client apps appear in `okta-logs` as `application.lifecycle.*` or `role.*` events; `target[].id` includes the `clientId` or role assignment `id`
