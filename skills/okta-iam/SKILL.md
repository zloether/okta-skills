---
name: okta-iam
description: Read Okta custom admin roles, resource sets, role bindings, and governance bundles. Use when asked about custom admin roles, who has admin access, resource-based access control, role permissions, or entitlement management governance bundles.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. `list-bundles`, `get-bundle`, `list-bundle-entitlements`, `list-bundle-entitlement-values`, and `get-opt-in-status` are Limited GA (`isGenerallyAvailable: false`) — governance bundles require the org to be opted in to entitlement management for the Admin Console. All other operations are GA.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-iam/scripts/iam.py <command> [options]
```

### list / get
List all custom roles, or get one by ID or label.
```bash
uv run skills/okta-iam/scripts/iam.py list
uv run skills/okta-iam/scripts/iam.py get cr0Yq6IJxGIr0ouum0g3
```

### list-permissions / get-permission
List permissions assigned to a custom role, or get a specific one.
```bash
uv run skills/okta-iam/scripts/iam.py list-permissions cr0Yq6IJxGIr0ouum0g3
uv run skills/okta-iam/scripts/iam.py get-permission cr0Yq6IJxGIr0ouum0g3 okta.users.manage
```

### list-assignees
List all users in the org who have any role assignment (standard or custom).
```bash
uv run skills/okta-iam/scripts/iam.py list-assignees
```

### list-resource-sets / get-resource-set
List resource sets, or get one by ID or label. A resource set groups specific Okta resources (e.g. a subset of groups or apps) for scoped custom-role bindings.
```bash
uv run skills/okta-iam/scripts/iam.py list-resource-sets
uv run skills/okta-iam/scripts/iam.py get-resource-set iamoJDFKaJxGIr0oamd9g
```

### list-bindings / get-binding
List the role bindings on a resource set, or get one binding by role ID/label. A binding links a custom role + resource set + members (users/groups).
```bash
uv run skills/okta-iam/scripts/iam.py list-bindings iamoJDFKaJxGIr0oamd9g
uv run skills/okta-iam/scripts/iam.py get-binding iamoJDFKaJxGIr0oamd9g cr0Yq6IJxGIr0ouum0g3
```

### list-binding-members / get-binding-member
List the members (users/groups) assigned to a role resource-set binding, or get one member.
```bash
uv run skills/okta-iam/scripts/iam.py list-binding-members iamoJDFKaJxGIr0oamd9g cr0Yq6IJxGIr0ouum0g3
uv run skills/okta-iam/scripts/iam.py get-binding-member iamoJDFKaJxGIr0oamd9g cr0Yq6IJxGIr0ouum0g3 irb1qe6PGuMc7Oh8N0g4
```

### list-resources / get-resource
List the individual resources (by ORN) included in a resource set, or get one.
```bash
uv run skills/okta-iam/scripts/iam.py list-resources iamoJDFKaJxGIr0oamd9g
uv run skills/okta-iam/scripts/iam.py get-resource iamoJDFKaJxGIr0oamd9g ire106sQKoHoXXsAe0g4
```

### list-bundles / get-bundle
List or get governance bundles — pre-packaged sets of entitlements for the Admin Console. Limited GA.
```bash
uv run skills/okta-iam/scripts/iam.py list-bundles
uv run skills/okta-iam/scripts/iam.py get-bundle enbllojq9J9J105DL1d6
```

### list-bundle-entitlements / list-bundle-entitlement-values
List the entitlements in a governance bundle, or the values available for one entitlement. Limited GA.
```bash
uv run skills/okta-iam/scripts/iam.py list-bundle-entitlements enbllojq9J9J105DL1d6
uv run skills/okta-iam/scripts/iam.py list-bundle-entitlement-values enbllojq9J9J105DL1d6 ent4rg7fltWSgrlDT8g6
```

### get-opt-in-status
Get whether the Admin Console has opted in to entitlement management (governance bundles). Limited GA.
```bash
uv run skills/okta-iam/scripts/iam.py get-opt-in-status
```

### list-role-subscriptions / get-role-subscription
List or get email notification subscriptions for a role (standard role type or custom role ID).
```bash
uv run skills/okta-iam/scripts/iam.py list-role-subscriptions SUPER_ADMIN
uv run skills/okta-iam/scripts/iam.py get-role-subscription SUPER_ADMIN CONNECTOR_AGENT
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list`-prefixed commands return arrays; `get`-prefixed commands return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

Unlike the classic Okta API, these endpoints wrap list results in a named field (`roles`, `resource-sets`, `bundles`, etc.) and paginate via a `_links.next.href` cursor in the response body rather than an HTTP `Link` header. The script follows this automatically and always returns a flat JSON array — the wrapping is not visible in the output.

## Output Schema

### Role object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique key for the custom role |
| `label` | string | Unique, human-readable label for the role |
| `description` | string | Description of the role |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Permission object (`list-permissions` / `get-permission`)

| Field | Type | Description |
|---|---|---|
| `label` | string | The Okta permission, e.g. `okta.users.read` |
| `conditions` | object \| null | Optional `include`/`exclude` maps that further restrict the permission to specific attribute values |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Role assignee object (`list-assignees`)

| Field | Type | Description |
|---|---|---|
| `id` | string | User ID — pass to `okta-users get <id>` |
| `orn` | string | Okta Resource Name identifying the assignee |
| `_links.roles` | object | Link to the user's role assignments |

### Resource set object (`list-resource-sets` / `get-resource-set`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique ID for the resource set |
| `label` | string | Unique label |
| `description` | string | Description |
| `_links.resources` / `_links.bindings` | object | Links to this resource set's resources and role bindings |

### Binding object (`list-bindings` / `get-binding`)

`list-bindings` returns one entry per **role** bound to the resource set (`id` = role ID, `_links.members` = link to that binding's members). `get-binding` returns `{id, _links: {resource-set, members}}` for a specific role's binding.

### Binding member object (`list-binding-members` / `get-binding-member`)

| Field | Type | Description |
|---|---|---|
| `id` | string | User or group ID that's a member of the binding — cross-reference `okta-users get <id>` or `okta-groups get <id>` |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Resource set resource object (`list-resources` / `get-resource`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Resource set resource object ID |
| `orn` | string | Okta Resource Name (ORN) of the actual resource, e.g. a group or app |
| `conditions.Exclude.okta:ORN` | string[] | Specific resources excluded from an otherwise broader inclusion (e.g. exclude one group from a "GROUPS" resource type) |

### Governance bundle object (`list-bundles` / `get-bundle`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Bundle ID |
| `name` | string | Bundle name |
| `description` | string | Description |
| `status` | string | Bundle status |
| `orn` | string | Okta Resource Name for the bundle |

### Bundle entitlement / entitlement value objects

`list-bundle-entitlements` returns the entitlements packaged in a bundle (each an ORN-based reference plus values); `list-bundle-entitlement-values` returns the specific values available for one of those entitlements (e.g. specific app roles or group memberships that can be granted).

### Opt-in status object (`get-opt-in-status`)

| Field | Type | Description |
|---|---|---|
| `optInStatus` | string | `OPTING_IN`, `OPTED_IN`, `OPTING_OUT`, or `OPTED_OUT` — only `OPTED_IN` orgs can use governance bundles |

### Subscription object (`list-role-subscriptions` / `get-role-subscription`)

| Field | Type | Description |
|---|---|---|
| `notificationType` | string | e.g. `USER_LOCKED_OUT`, `CONNECTOR_AGENT`, `RATELIMIT_NOTIFICATION`, `OKTA_ANNOUNCEMENT` |
| `status` | string | `subscribed` or `unsubscribed` |
| `channels` | string[] | Notification channels — currently only `email` |

## Interpretation

### Standard roles vs. custom roles

`list-role-subscriptions` and `get-role-subscription` accept a `roleRef`, which can be either a **standard role type** (e.g. `SUPER_ADMIN`, `ORG_ADMIN`, `APP_ADMIN`, `HELP_DESK_ADMIN`, `USER_ADMIN`, `READ_ONLY_ADMIN`, `GROUP_MEMBERSHIP_ADMIN`, `REPORT_ADMIN`, `API_ACCESS_MANAGEMENT_ADMIN`, `ACCESS_CERTIFICATIONS_ADMIN`, `ACCESS_REQUESTS_ADMIN`, `WORKFLOWS_ADMIN`) or a **custom role ID**. Everything under `list` / `get` / `list-permissions` in this skill is a custom role only — standard-role assignments on individual users/groups are read via `okta-users get-roles` and `okta-groups list-roles`, not here.

### What to look for

- **Overly broad permissions**: A custom role with `okta.users.manage` (full manage, not scoped) bound to a resource set covering many groups is effectively a near-super-admin. Check `conditions` on each permission (`list-permissions`) — a permission with no `conditions` applies unconditionally within whatever the resource set covers.
- **Resource set scope creep**: `list-resources` shows exactly what a resource set covers. A resource set with a broad ORN (e.g. all groups) combined with a permission like `okta.groups.manage` gives far more access than a narrowly-scoped one — compare against what the binding's members actually need.
- **Unused custom roles**: A role returned by `list` with no bindings (check `list-bindings` on every resource set for a matching role ID) is defined but not granting anyone access — dead configuration, not a security issue by itself.
- **Governance bundle opt-out mid-use**: If `get-opt-in-status` returns anything other than `OPTED_IN`, bundle-based entitlement management isn't active — `list-bundles` may still return previously-created bundles that aren't currently enforced.
- **Permission conditions asymmetry**: A permission's `conditions.include` restricts it to matching values only; `conditions.exclude` allows everything except matching values. Misreading which one is set inverts the actual access — always check which key is present, not just that `conditions` exists.

### Cross-skill references

- Role assignee `id` (from `list-assignees`) → `okta-users get <id>` for profile details; `okta-users get-roles <id>` for that user's full set of role assignments (standard + custom)
- Binding member `id` (from `list-binding-members`) → could be a user or a group; try `okta-users get <id>` first, then `okta-groups get <id>` if that 404s
- Resource set resource `orn` → identifies the underlying Okta object (group, app, etc.); the ORN's resource type segment indicates which skill to cross-reference (e.g. a `group` ORN → `okta-groups get <id>`)
- Permission `label` values correspond 1:1 with Okta's documented permission catalog — cross-reference against the specific action (`.read` vs `.manage`) when assessing blast radius
- Admin role changes and custom role assignment events surface in `okta-logs` under event types like `application.lifecycle.update` and `user.account.privilege.grant` / `role.*` — filter with `eventType sw "role."` or `eventType sw "iam."`
