---
name: okta-groups
description: Read Okta groups and group memberships. Use when asked about groups, which users belong to a group, which groups a user is a member of, which apps are assigned to a group, who owns a group, or group rules (dynamic membership rules) in the org.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-groups/scripts/groups.py <command> [options]
```

### list
List groups, optionally filtered or searched.
```bash
uv run skills/okta-groups/scripts/groups.py list
uv run skills/okta-groups/scripts/groups.py list --filter 'type eq "OKTA_GROUP"'
uv run skills/okta-groups/scripts/groups.py list --search 'profile.name co "Engineering"'
uv run skills/okta-groups/scripts/groups.py list --search 'type eq "APP_GROUP" and lastMembershipUpdated gt "2024-01-01T00:00:00.000Z"'
uv run skills/okta-groups/scripts/groups.py list --q Engineering --expand stats --sort-by profile.name --sort-order asc
```
`--filter`, `--search`, and `--q` are mutually exclusive. `--sort-by`/`--sort-order` apply only to `--search` queries.

### get
Get a single group by ID.
```bash
uv run skills/okta-groups/scripts/groups.py get 00g1ab2cd3EF4GH5IJ6K
```

### get-members
List all users that are members of a group.
```bash
uv run skills/okta-groups/scripts/groups.py get-members 00g1ab2cd3EF4GH5IJ6K --limit 50
```

### search
Search groups by name.
```bash
uv run skills/okta-groups/scripts/groups.py search "Admins"
uv run skills/okta-groups/scripts/groups.py search "Engineering"
```

### get-apps
List all apps assigned to a group.
```bash
uv run skills/okta-groups/scripts/groups.py get-apps 00g1ab2cd3EF4GH5IJ6K --limit 50
```

### get-owners
List all owners of a group.
```bash
uv run skills/okta-groups/scripts/groups.py get-owners 00g1ab2cd3EF4GH5IJ6K
uv run skills/okta-groups/scripts/groups.py get-owners 00g1ab2cd3EF4GH5IJ6K --search 'type eq "USER"' --limit 50
```

### list-rules
List all group rules in the org, optionally filtered by keyword.
```bash
uv run skills/okta-groups/scripts/groups.py list-rules
uv run skills/okta-groups/scripts/groups.py list-rules --search "Engineering"
uv run skills/okta-groups/scripts/groups.py list-rules --limit 50
```

### get-rule
Retrieve a single group rule by ID.
```bash
uv run skills/okta-groups/scripts/groups.py get-rule 0pr1ab2cd3EF4GH5IJ6K
```

### list-roles
List all admin role assignments for a group.
```bash
uv run skills/okta-groups/scripts/groups.py list-roles 00g1ab2cd3EF4GH5IJ6K
uv run skills/okta-groups/scripts/groups.py list-roles 00g1ab2cd3EF4GH5IJ6K --expand targets/groups
```

### get-role
Get a specific role assignment for a group.
```bash
uv run skills/okta-groups/scripts/groups.py get-role 00g1ab2cd3EF4GH5IJ6K <role_assignment_id>
```

### list-role-app-targets
List the app targets a group's admin role is scoped to.
```bash
uv run skills/okta-groups/scripts/groups.py list-role-app-targets 00g1ab2cd3EF4GH5IJ6K <role_assignment_id> --limit 50
```

### list-role-group-targets
List the group targets a group's admin role is scoped to.
```bash
uv run skills/okta-groups/scripts/groups.py list-role-group-targets 00g1ab2cd3EF4GH5IJ6K <role_assignment_id> --limit 50
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. List, `get-members`, `get-apps`, `get-owners`, `list-rules`, `list-roles`, `list-role-app-targets`, and `list-role-group-targets` return arrays; `get`, `get-rule`, and `get-role` return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Filter / Search Reference

**`--search`** (recommended) — searches any group property including all profile attributes. Supports `eq`, `sw`, `co`, `gt`, `lt` operators and compound expressions with `and`/`or`.

- `id eq "00gak46y5hydV6NdM0g4"` — exact group ID match
- `profile.name eq "West Coast Users"` — exact name match
- `profile.name co "Engineering"` — name contains
- `profile.name sw "Eng"` — name starts with
- `profile.samAccountName sw "West Coast"` — any profile attribute; replace `samAccountName` with the actual attribute name
- `type eq "OKTA_GROUP"` — manually managed groups
- `type eq "APP_GROUP"` — groups pushed from an app
- `lastMembershipUpdated gt "2024-01-01T00:00:00.000Z"` — membership changed after a date
- `created lt "2014-01-01T00:00:00.000Z"` — groups created before a date
- `source.id eq "<app_id>"` — groups from a specific app
- `type eq "APP_GROUP" and source.id eq "<app_id>"` — compound
- `type eq "APP_GROUP" and (created lt "2014-01-01T00:00:00.000Z" and source.id eq "<app_id>")` — compound with grouped sub-clauses

**`--filter`** — limited to `id`, `type`, `lastUpdated`, `lastMembershipUpdated` only. Use `--search` instead unless you specifically need filter semantics.

- `type eq "OKTA_GROUP"` — manually managed groups
- `type eq "APP_GROUP"` — groups pushed from an app
- `type eq "BUILT_IN"` — built-in groups (e.g. Everyone)

## Output Schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta group ID (e.g. `00g1ab2cd3EF4GH5IJ6K`); use this to look up members or app assignments |
| `type` | string | Group origin — `OKTA_GROUP`, `APP_GROUP`, or `BUILT_IN` (see Group Types below) |
| `profile.name` | string | Display name of the group |
| `profile.description` | string | Optional description, if populated |
| `lastUpdated` | ISO 8601 string | When the group record was last modified |
| `lastMembershipUpdated` | ISO 8601 string | When the group's member list was last changed |
| `_links` | object | HAL links for related resources (users, apps, logo) |

`get-members` returns an array of user objects with the same schema as `okta-users get` — all profile fields and status are present.

### get-owners output schema

| Field | Type | Description |
|---|---|---|
| `id` | string | ID of the owner (user or group) |
| `displayName` | string | Display name of the owner |
| `type` | string | Entity type — `USER` or `GROUP` |
| `originType` | string | Where ownership is managed — `OKTA_DIRECTORY` or `APPLICATION` |
| `originId` | string | App instance ID when `originType` is `APPLICATION`; `null` for `OKTA_DIRECTORY` |
| `resolved` | boolean | For `APPLICATION` origin, `false` until the owner ID is reconciled with an Okta ID |
| `lastUpdated` | ISO 8601 string | When the owner record was last modified |

### list-rules / get-rule output schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Group rule ID (e.g. `0pr1ab2cd3EF4GH5IJ6K`) |
| `name` | string | Human-readable rule name |
| `status` | string | `ACTIVE`, `INACTIVE`, or `INVALID` |
| `created` | ISO 8601 string | When the rule was created |
| `lastUpdated` | ISO 8601 string | When the rule was last modified |
| `actions.assignUserToGroups.groupIds` | string[] | IDs of groups users are added to when the rule matches |
| `conditions.expression.value` | string | Okta expression language condition (e.g. `user.department=="Engineering"`) |
| `conditions.people.users.exclude` | string[] | User IDs explicitly excluded from this rule |

### list-roles / get-role output schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Role assignment ID |
| `type` | string | Standard role type (e.g. `HELP_DESK_ADMIN`, `SUPER_ADMIN`) or `CUSTOM` |
| `status` | string | Role assignment status |
| `label` | string | Human-readable label for the assignment |
| `assignmentType` | string | How the role was assigned (e.g. `GROUP`) |
| `_embedded.targets` | object | Present when the role is scoped to specific apps/groups rather than org-wide; see `list-role-app-targets` / `list-role-group-targets` |

### list-role-app-targets / list-role-group-targets output schema

Each returns an array of the app or group resources a scoped admin role applies to (app objects match `okta-apps get`/group objects match `okta-groups get` schemas). An empty array with a scoped role type means the role currently grants no effective access — worth flagging.

## Interpretation

### Group types

| Type | Meaning |
|---|---|
| `OKTA_GROUP` | Manually managed in Okta; membership is controlled by admins or group rules |
| `APP_GROUP` | Pushed from an external application (e.g. Active Directory, Workday); membership is controlled by the source app and cannot be changed directly in Okta |
| `BUILT_IN` | System-level groups Okta creates automatically, such as "Everyone" (all users) |

### What to look for

- **APP_GROUP membership**: Membership is authoritative in the source system. If a user should be in an APP_GROUP but isn't, the issue is in the upstream app's provisioning, not Okta.
- **`lastMembershipUpdated` vs `lastUpdated`**: A group with a very stale `lastMembershipUpdated` and `OKTA_GROUP` type may have been forgotten — worth auditing members.
- **Empty OKTA_GROUP with app assignments**: Use `okta-apps get-groups <app_id>` to see if a group is assigned to apps; an empty group means no users get access via that group assignment.
- **Group rule status**: `ACTIVE` rules continuously evaluate and add matching users. `INACTIVE` rules exist but do not run. `INVALID` rules have a broken expression or reference a deleted group — investigate with `get-rule <id>` and check `conditions.expression.value`.
- **Finding why a user is in a group**: If the group type is `OKTA_GROUP`, run `list-rules` and look for rules whose `actions.assignUserToGroups.groupIds` contains the group's `id`. If a matching rule is `ACTIVE`, the user's membership may be rule-driven rather than manually assigned.
- **Group owner types**: An owner with `type=USER` is an individual admin. `type=GROUP` means a group owns another group — uncommon but used in delegated admin setups. `originType=APPLICATION` means ownership was pushed from an external system.
- **Group-assigned admin roles**: `list-roles` shows delegated admin access granted to every member of the group — this is a common way orgs scale admin delegation. A broad role (e.g. `SUPER_ADMIN`) assigned to a large group is worth auditing.
- **Scoped vs. org-wide roles**: If a role assignment's `_embedded.targets` is present, the role only applies to the apps/groups listed via `list-role-app-targets` / `list-role-group-targets`. If absent, the role applies org-wide — a materially larger blast radius.

### Cross-skill references

- `id` → `okta-groups get-apps <group_id>` lists all apps assigned to this group (reverse of `okta-apps get-groups <app_id>`)
- `id` → `okta-apps get-groups <app_id>` results include group objects; match on `id` to confirm which groups are assigned to an app
- `id` → search `okta-logs list --q <group_id>` to see audit events (membership changes, group updates) associated with this group
- `get-members` → each user object contains `id`; pass to `okta-users get <id>` for full profile details, or to `okta-logs login-failures --user <login>` for login history
- `get-apps` → each app object contains `id`; pass to `okta-apps get <id>` for full app details, or to `okta-apps get-users <id>` for direct user assignments
- `get-owners` → owner `id` with `type=USER` can be passed to `okta-users get <id>` for full profile details
- `list-rules` / `get-rule` → `actions.assignUserToGroups.groupIds` contains group IDs; pass each to `okta-groups get <id>` to resolve group names
- Group membership changes appear in logs as `group.user_membership.add` / `group.user_membership.remove` events; `target[].id` in those events is the group `id`
- Group rule changes appear in logs as `group.rule.create`, `group.rule.update`, `group.rule.activate`, `group.rule.deactivate` events; `target[].id` is the rule `id`
- `list-roles` app targets → `okta-apps get <id>` for full app details; group targets → `okta-groups get <id>`
- Role assignment changes appear in logs as `group.privilege.grant` / `group.privilege.revoke` events
