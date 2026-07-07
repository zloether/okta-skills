---
name: okta-filters
description: Reference for constructing Okta API filter and search expressions. Use when building --filter or --search arguments for any Okta skill, or when deciding which skill to query for a given resource type.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
---

## Choosing the Right Skill

| What you need | Skill | Supports filtering? |
|---|---|---|
| User accounts, profile fields, status | `okta-users` | Yes (`--filter`) |
| Groups, group membership, group rules | `okta-groups` | Yes (`--filter` and `--search`) |
| App integrations, app assignments | `okta-apps` | Yes (`--filter`) |
| Enrolled devices | `okta-devices` | Yes (`--search`) |
| Audit log events, auth history | `okta-logs` | Yes (`--filter`) |
| Sign-on, MFA, password policies | `okta-policies` | No |
| IP and dynamic network zones | `okta-network-zones` | No |
| Device compliance requirements | `okta-device-assurance` | No |
| Real-time device health posture checks | `okta-device-posture` | No |
| API token metadata | `okta-api-tokens` | No |
| Session lookup by ID | `okta-sessions` | No |

## `--filter` vs `--search`

| Parameter | Scope | When to use |
|---|---|---|
| `--filter` | Limited to a fixed set of indexed fields per resource (documented below). | Core fields: `status`, `type`, `id`, top-level timestamps. |
| `--search` | Any attribute, including all profile fields. Same SCIM operators. | Required for profile attributes. Preferred for groups and devices. |

**Per-skill availability:**

| Skill | `--filter` | `--search` |
|---|---|---|
| okta-users | ✓ | — |
| okta-groups | ✓ (limited fields) | ✓ (preferred; all fields) |
| okta-apps | ✓ | — |
| okta-devices | — | ✓ |
| okta-logs | ✓ | — |

## Operators

| Operator | Meaning | Example |
|---|---|---|
| `eq` | Equals | `status eq "ACTIVE"` |
| `ne` | Not equals | `status ne "DEPROVISIONED"` |
| `sw` | Starts with | `profile.name sw "West"` |
| `ew` | Ends with | `profile.email ew "@example.com"` |
| `co` | Contains | `profile.name co "Engineering"` |
| `gt` | Greater than | `lastUpdated gt "2024-01-01T00:00:00.000Z"` |
| `lt` | Less than | `created lt "2020-01-01T00:00:00.000Z"` |
| `ge` | Greater than or equal | `lastUpdated ge "2024-01-01T00:00:00.000Z"` |
| `le` | Less than or equal | `created le "2024-12-31T00:00:00.000Z"` |
| `pr` | Present (non-null, non-empty) | `profile.mobilePhone pr` |

Combine with `and`, `or`, `not`. Use parentheses to group sub-expressions:

```
type eq "APP_GROUP" and (created lt "2014-01-01T00:00:00.000Z" and source.id eq "0oa2v0el0gP90aqjJ0g7")
```

All string values must be quoted. Timestamps use ISO 8601 with milliseconds: `"2024-01-01T00:00:00.000Z"`.

## Filterable Fields by Resource

### Users (`okta-users --filter`)

| Field | Type | Notes |
|---|---|---|
| `id` | string | Okta user ID |
| `status` | string | `STAGED`, `PROVISIONED`, `ACTIVE`, `RECOVERY`, `PASSWORD_EXPIRED`, `LOCKED_OUT`, `DEPROVISIONED` |
| `lastUpdated` | ISO 8601 | When the user record was last modified |
| `profile.login` | string | Username / email |
| `profile.email` | string | Primary email |
| `profile.firstName` | string | |
| `profile.lastName` | string | |
| `profile.department` | string | |
| `profile.organization` | string | |
| `credentials.provider.type` | string | `OKTA`, `ACTIVE_DIRECTORY`, `LDAP`, `FEDERATION`, `SOCIAL` |
| `credentials.provider.name` | string | External provider name |

### Groups (`okta-groups`)

Prefer `--search` for profile attributes. `--filter` is limited to the fields marked ★.

| Field | Type | `--filter` | `--search` | Notes |
|---|---|---|---|---|
| `id` | string | ★ | ✓ | |
| `type` | string | ★ | ✓ | `OKTA_GROUP`, `APP_GROUP`, `BUILT_IN` |
| `lastUpdated` | ISO 8601 | ★ | ✓ | |
| `lastMembershipUpdated` | ISO 8601 | ★ | ✓ | |
| `created` | ISO 8601 | — | ✓ | |
| `profile.name` | string | — | ✓ | |
| `profile.description` | string | — | ✓ | |
| `profile.samAccountName` | string | — | ✓ | AD-sourced groups; any profile attribute follows the same pattern |
| `source.id` | string | — | ✓ | Source app instance ID; only present on `APP_GROUP` |

### Apps (`okta-apps --filter`)

| Field | Type | Notes |
|---|---|---|
| `id` | string | Okta app ID |
| `status` | string | `ACTIVE`, `INACTIVE` |
| `name` | string | Technical app name (e.g. `workday`, `office365`) |
| `label` | string | Display name shown in the End-User Dashboard |

### Devices (`okta-devices --search`)

| Field | Type | Notes |
|---|---|---|
| `id` | string | Okta device ID |
| `status` | string | `ACTIVE`, `INACTIVE` |
| `profile.displayName` | string | Device display name |
| `profile.platform` | string | `WINDOWS`, `MACOS`, `IOS`, `ANDROID`, `CHROMEOS` |
| `profile.manufacturer` | string | |
| `profile.model` | string | |
| `profile.osVersion` | string | OS version string |
| `profile.serialNumber` | string | |
| `profile.udid` | string | Apple UDID |
| `profile.imei` | string | |
| `profile.registered` | boolean | Whether the device is registered in Okta |
| `profile.managed` | boolean | Whether the device is MDM-managed |

### Logs (`okta-logs --filter`)

| Field | Type | Notes |
|---|---|---|
| `eventType` | string | e.g. `user.session.start`, `user.authentication.auth_via_mfa` |
| `outcome.result` | string | `SUCCESS`, `FAILURE`, `SKIPPED`, `ALLOW`, `DENY`, `CHALLENGE`, `UNKNOWN` |
| `actor.id` | string | ID of the entity that performed the action |
| `actor.alternateId` | string | Email or login of the actor |
| `target.id` | string | ID of the affected entity |
| `target.alternateId` | string | Email or login of the affected entity |
| `client.ipAddress` | string | Source IP address |
| `client.geographicalContext.country` | string | Country derived from IP |

## Examples

### Users

```bash
# Active users only
uv run skills/okta-users/scripts/users.py list --filter 'status eq "ACTIVE"'

# Users in a specific department
uv run skills/okta-users/scripts/users.py list --filter 'profile.department eq "Engineering"'

# Users federated from Active Directory
uv run skills/okta-users/scripts/users.py list --filter 'credentials.provider.type eq "ACTIVE_DIRECTORY"'

# Users updated after a date
uv run skills/okta-users/scripts/users.py list --filter 'lastUpdated gt "2024-01-01T00:00:00.000Z"'
```

### Groups

```bash
# All app-pushed groups
uv run skills/okta-groups/scripts/groups.py list --search 'type eq "APP_GROUP"'

# Groups whose name contains "Engineering"
uv run skills/okta-groups/scripts/groups.py list --search 'profile.name co "Engineering"'

# Groups from a specific source app
uv run skills/okta-groups/scripts/groups.py list --search 'source.id eq "0oa2v0el0gP90aqjJ0g7"'

# Groups whose membership changed after a date
uv run skills/okta-groups/scripts/groups.py list --search 'lastMembershipUpdated gt "2024-01-01T00:00:00.000Z"'

# AD groups whose samAccountName starts with "West Coast"
uv run skills/okta-groups/scripts/groups.py list --search 'profile.samAccountName sw "West Coast"'

# APP_GROUPs from a specific source created before 2014
uv run skills/okta-groups/scripts/groups.py list --search 'type eq "APP_GROUP" and (created lt "2014-01-01T00:00:00.000Z" and source.id eq "0oa2v0el0gP90aqjJ0g7")'
```

### Apps

```bash
# Active apps only
uv run skills/okta-apps/scripts/apps.py list --filter 'status eq "ACTIVE"'

# App by technical name
uv run skills/okta-apps/scripts/apps.py list --filter 'name eq "workday"'
```

### Devices

```bash
# macOS devices only
uv run skills/okta-devices/scripts/devices.py list --search 'profile.platform eq "MACOS"'

# MDM-managed devices
uv run skills/okta-devices/scripts/devices.py list --search 'profile.managed eq true'

# Active Windows devices
uv run skills/okta-devices/scripts/devices.py list --search 'status eq "ACTIVE" and profile.platform eq "WINDOWS"'
```

### Logs

```bash
# Failed authentications
uv run skills/okta-logs/scripts/logs.py list --filter 'outcome.result eq "FAILURE"'

# Session start events
uv run skills/okta-logs/scripts/logs.py list --filter 'eventType eq "user.session.start"'

# Events by a specific user (by email)
uv run skills/okta-logs/scripts/logs.py list --filter 'actor.alternateId eq "user@example.com"'

# MFA challenge failures
uv run skills/okta-logs/scripts/logs.py list --filter 'eventType eq "user.authentication.auth_via_mfa" and outcome.result eq "FAILURE"'
```
