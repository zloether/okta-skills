---
name: okta-realms
description: Read Okta realms and realm assignments — multi-tenant segmentation boundaries that partition users, and the rules that assign users to realms. Use when asked what realms exist, which realm a class of users belongs to, what domains or conditions route users into a realm, or the status of in-flight realm assignment operations.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. All operations are GA.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-realms/scripts/realms.py <command> [options]
```

### list-realms / get-realm
List all realms, or get one by ID.
```bash
uv run skills/okta-realms/scripts/realms.py list-realms
uv run skills/okta-realms/scripts/realms.py list-realms --search 'profile.name co "Partner"' --sort-by profile.name --sort-order asc
uv run skills/okta-realms/scripts/realms.py get-realm guox9jQ16k9V8IFEL0g3
```

### list-realm-assignments / get-realm-assignment
List all realm assignments, or get one by ID. Realm assignments are the rules (domain lists + conditions, ordered by priority) that route users into a realm.
```bash
uv run skills/okta-realms/scripts/realms.py list-realm-assignments
uv run skills/okta-realms/scripts/realms.py get-realm-assignment rul2jy7jLUlnO3ng00g4
```

### list-realm-assignment-operations
List all realm assignment operations — the async jobs that execute a realm assignment (bulk-move matching users into their target realm). Sorted most recent to oldest.
```bash
uv run skills/okta-realms/scripts/realms.py list-realm-assignment-operations
uv run skills/okta-realms/scripts/realms.py list-realm-assignment-operations --limit 50
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

JSON to stdout. `list-`-prefixed commands return an array (paginated via cursor/`Link` header). `get-`-prefixed commands return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### Realm object (`list-realms` / `get-realm`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique ID for the realm — use with `get-realm` |
| `isDefault` | boolean | Whether this is the default realm every new user starts in |
| `profile.name` | string | Realm display name |
| `profile.realmType` | string | `PARTNER` if used to store partner users for Okta's external partner portal; absent otherwise |
| `profile.domains` | string[] | Allowed username/email domains for users created or updated in this realm |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |
| `_links.self.href` | string | Self link |

### Realm assignment object (`list-realm-assignments` / `get-realm-assignment`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique ID for the realm assignment — use with `get-realm-assignment` |
| `name` | string | Assignment display name |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `isDefault` | boolean | Whether this is the catch-all assignment for users that match no other assignment |
| `priority` | integer | Evaluation priority — lower number wins when multiple assignments could match |
| `domains` | string[] | Allowed username/email domains, enforced independently of `conditions` |
| `conditions.profileSourceId` | string | ID of the profile source the condition evaluates against |
| `conditions.expression.value` | string | Expression Language condition that must match for this assignment to apply |
| `actions.assignUserToRealm.realmId` | string | Target realm ID matching users are moved into — cross-reference with `get-realm` |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |
| `_links.self.href` | string | Self link |

### Realm assignment operation object (`list-realm-assignment-operations`)

| Field | Type | Description |
|---|---|---|
| `id` | string | ID of the async operation |
| `type` | string | Operation type, e.g. `realm:assignment` |
| `status` | string | `SCHEDULED`, `IN_PROGRESS`, `COMPLETED`, or `FAILED` |
| `realmId` / `realmName` | string | Target realm the operation moved users into |
| `numUserMoved` | number | Count of users moved by this operation |
| `assignmentOperation.configuration.id` | string | Source realm assignment ID, or `ALL` if the operation executed every assignment |
| `assignmentOperation.configuration.name` | string | Source realm assignment name |
| `assignmentOperation.configuration.actions.assignUserToRealm.realmId` | string | Target realm ID from the assignment's action |
| `assignmentOperation.configuration.conditions` | object | Conditions from the source assignment, if any |
| `created` / `started` / `completed` | ISO 8601 string | Timestamps |
| `_links.self.href` | string | Self link |

## Interpretation

### What to look for

- **`isDefault: true`**: identifies the catch-all realm (`list-realms`) or catch-all assignment (`list-realm-assignments`) — users landing here matched no other realm assignment.
- **`priority` collisions or gaps**: realm assignments are evaluated in ascending priority order; a low-priority (high-number) assignment with broad `conditions` can unexpectedly shadow more specific ones if priorities aren't ordered as intended.
- **`status: FAILED` on a realm assignment operation**: a bulk user-move job didn't complete — check `numUserMoved` against the expected population and re-run via the source assignment if needed.
- **Assignment `domains` vs. realm `profile.domains`**: both gate which usernames/emails are valid, but at different points — the assignment's `domains` constrains eligibility for the *assignment* rule itself, while the target realm's `profile.domains` constrains the user once they're *in* that realm.

### Cross-skill references

- `actions.assignUserToRealm.realmId` / `assignmentOperation...realmId` → `get-realm <realmId>` for the target realm's full profile
- `conditions.profileSourceId` → `okta-identity-providers get <id>` if the profile source is an external IdP
- Realm-scoped users → `okta-users` (a user's `realmId` field indicates realm membership)
