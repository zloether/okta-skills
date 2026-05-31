---
name: okta-groups
description: Read Okta groups and group memberships. Use when asked about groups, which users belong to a group, which groups a user is a member of, or to list all groups in the org.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-groups/scripts/groups.py <command> [options]
```

### list
List groups, optionally filtered.
```bash
uv run skills/okta-groups/scripts/groups.py list
uv run skills/okta-groups/scripts/groups.py list --filter 'type eq "OKTA_GROUP"'
```

### get
Get a single group by ID.
```bash
uv run skills/okta-groups/scripts/groups.py get 00g1ab2cd3EF4GH5IJ6K
```

### get-members
List all users that are members of a group.
```bash
uv run skills/okta-groups/scripts/groups.py get-members 00g1ab2cd3EF4GH5IJ6K
```

### search
Search groups by name.
```bash
uv run skills/okta-groups/scripts/groups.py search "Admins"
uv run skills/okta-groups/scripts/groups.py search "Engineering"
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. List and `get-members` return arrays; `get` returns a single group object. Errors are JSON with an `error` key on stderr; exit code 1.

## Filter Reference

Common SCIM filter expressions for `--filter`:
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

### Cross-skill references

- `id` → `okta-apps get-groups <app_id>` results include group objects; match on `id` to confirm which groups are assigned to an app
- `id` → search `okta-logs list --q <group_id>` to see audit events (membership changes, group updates) associated with this group
- `get-members` → each user object contains `id`; pass to `okta-users get <id>` for full profile details, or to `okta-logs login-failures --user <login>` for login history
- Group membership changes appear in logs as `group.user_membership.add` / `group.user_membership.remove` events; `target[].id` in those events is the group `id`
