---
name: okta-schemas
description: Read Okta profile mappings, user/group/app schemas, user types, log stream schemas, linked object definitions, and UI schemas. Use when asked how user attributes flow between Okta and apps, what custom profile attributes exist, what user types are configured, or how a linked-object relationship (e.g. manager) is defined.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-schemas/scripts/schemas.py <command> [options]
```

### list / get
List all profile mappings (optionally filtered by source/target), or get one by ID. A profile mapping describes how properties flow between an Okta user type and an app instance (or between two Okta user types).
```bash
uv run skills/okta-schemas/scripts/schemas.py list
uv run skills/okta-schemas/scripts/schemas.py list --source-id 0oa1b2c3d4E5f6G7h8i9
uv run skills/okta-schemas/scripts/schemas.py list --target-id oty1b2c3d4E5f6G7h8i9
uv run skills/okta-schemas/scripts/schemas.py list --limit 50
uv run skills/okta-schemas/scripts/schemas.py get prm1b2c3d4E5f6G7h8i9
```

### get-app-user-schema
Get the default app user schema for an app — the custom profile properties available for users of that app.
```bash
uv run skills/okta-schemas/scripts/schemas.py get-app-user-schema 0oa1b2c3d4E5f6G7h8i9
```

### get-group-schema
Get the org's group schema (custom group profile properties). There is only one group schema per org.
```bash
uv run skills/okta-schemas/scripts/schemas.py get-group-schema
```

### list-log-stream-schemas / get-log-stream-schema
List all log stream type schemas, or get the schema for a specific type (`aws_eventbridge` or `splunk_cloud_logstreaming`).
```bash
uv run skills/okta-schemas/scripts/schemas.py list-log-stream-schemas
uv run skills/okta-schemas/scripts/schemas.py get-log-stream-schema aws_eventbridge
```

### list-linked-objects / get-linked-object
List all linked object definitions (e.g. manager/subordinate), or get one by its primary or associated name.
```bash
uv run skills/okta-schemas/scripts/schemas.py list-linked-objects
uv run skills/okta-schemas/scripts/schemas.py get-linked-object manager
```

### get-user-schema
Get a user schema by ID. Use `default` for the default user type's schema.
```bash
uv run skills/okta-schemas/scripts/schemas.py get-user-schema default
```

### list-user-types / get-user-type
List all user types in the org, or get one by ID. Use `default` for the default user type.
```bash
uv run skills/okta-schemas/scripts/schemas.py list-user-types
uv run skills/okta-schemas/scripts/schemas.py get-user-type default
```

### list-ui-schemas / get-ui-schema
List all UI schemas (enrollment form field definitions), or get one by ID. ⚠️ Limited GA.
```bash
uv run skills/okta-schemas/scripts/schemas.py list-ui-schemas
uv run skills/okta-schemas/scripts/schemas.py get-ui-schema uis1b2c3d4E5f6G7h8i9
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list`-prefixed commands return arrays; `get`-prefixed commands (and `list` for profile mappings, `get-group-schema`) return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### Profile mapping object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the mapping — use with `get` |
| `source` | object | `{id, name, type}` — the side expressions read from. `type` is `appuser` or `user` |
| `target` | object | `{id, name, type}` — the side expressions write to |
| `properties` | object | **`get` only** — map of target property name → `{expression, pushStatus}`. `expression` is an [Okta Expression Language](https://developer.okta.com/docs/reference/okta-expression-language/) string; `pushStatus` is `PUSH` (updates on create and update) or `DONT_PUSH` (create only) |
| `_links.self.href` | string | Link to this mapping |

Note: `list` (`ListProfileMappings`) omits `properties` — call `get <id>` to see the actual property expressions.

### User schema / app user schema object (`get-user-schema` / `get-app-user-schema`)

| Field | Type | Description |
|---|---|---|
| `id` | string | URI of the schema |
| `name` | string | Schema name |
| `title` | string | User-defined display name |
| `definitions.base.properties` | object | Okta-defined base properties (e.g. `login`, `email`, `firstName`, `lastName`) — only `permissions`, nullability of `firstName`/`lastName`, and `login`'s `pattern` are editable |
| `definitions.custom.properties` | object | Custom properties, keyed by property name. Each has `type`, `title`, `description`, `required`, `permissions`, `scope` (`NONE` = not user-editable via self-service, `SELF` = user-editable), and optionally `enum`/`oneOf` for restricted values |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Group schema object (`get-group-schema`)

Same shape as the user schema (`definitions.base.properties` / `definitions.custom.properties`), but for group profiles. There is exactly one group schema per org — no ID is needed.

### Log stream schema object (`list-log-stream-schemas` / `get-log-stream-schema`)

| Field | Type | Description |
|---|---|---|
| `id` | string | URI of the schema |
| `title` | string | Schema title |
| `oneOf` | array | Type-specific property definitions (log stream schemas are polymorphic — AWS EventBridge and Splunk Cloud have different required fields) |

### Linked object definition (`list-linked-objects` / `get-linked-object`)

| Field | Type | Description |
|---|---|---|
| `primary` | object | `{name, title, description, type}` — the "one" or "many" side that owns the relationship. `type` is `USER` |
| `associated` | object | Same shape as `primary` — the other side of the relationship |
| `_links.self.href` | string | Link to this definition |

The classic example is `manager` (primary) / `subordinates` (associated).

### User type object (`list-user-types` / `get-user-type`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique key for the user type — use with `get-user-type` and as a `sourceId`/`targetId` filter on `list` (profile mappings) |
| `name` | string | Internal name, immutable after creation |
| `displayName` | string | Human-readable name |
| `description` | string | Description |
| `default` | boolean | `true` for the org's default user type — every org has exactly one |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |
| `_links.schema.href` | string | Link to this user type's schema — extract the trailing segment and pass to `get-user-schema` |

### UI schema object (`list-ui-schemas` / `get-ui-schema`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the UI schema |
| `uiSchema` | object | Form field layout/ordering definition used to render an enrollment or self-service form |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

## Interpretation

### What to look for

- **`DONT_PUSH` on a mapping property that should stay in sync**: If an app-bound mapping property has `pushStatus: DONT_PUSH`, updates to the Okta user after initial provisioning never propagate to the app — a common cause of "I changed it in Okta but the app still shows the old value" reports.
- **Custom attribute with `scope: SELF` and no `enum`/`oneOf`**: End users can set this attribute to any value matching its `type` via the profile self-service UI — worth flagging if the attribute feeds into an authorization decision elsewhere (e.g. a group rule or policy condition).
- **Multiple user types with divergent schemas**: `list-user-types` returning more than one type usually means different attribute sets exist per population; a `get-user-schema` call using one type's schema ID won't reflect attributes only present in another type's schema.
- **Linked object definitions with no corresponding data**: A `manager`/`subordinates` definition existing in `list-linked-objects` doesn't guarantee any user actually has linked objects populated — check `okta-users get-linked-objects <user_id> manager` for actual data.
- **App user schema properties not covered by any profile mapping**: A custom property on `get-app-user-schema` that never appears as a target in `get <mapping_id>` `properties` for that app means the app has the field defined but nothing populates it from Okta.

### Cross-skill references

- Profile mapping `source.id` / `target.id` (when `type` is `appuser`) → `okta-apps get <id>` for the app instance
- Profile mapping `source.id` / `target.id` (when `type` is `user`) → this skill's `get-user-type <id>` for the user type, or `get-user-schema <id>` for its schema
- User type `_links.schema.href` → extract the schema ID from the URL and pass to `get-user-schema`
- App `id` from `okta-apps get <app_id>` → this skill's `get-app-user-schema <app_id>` for its custom profile fields, and `list --target-id <app_id>` for mappings that populate them
- Linked object `primary.name` / `associated.name` (e.g. `manager`) → `okta-users get-linked-objects <user_id> <name>` for a specific user's linked object data
