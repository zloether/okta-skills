---
name: okta-users
description: Read Okta user profiles, status, attributes, group memberships, app assignments, MFA factors, roles, devices, OAuth grants, and related resources. Use when asked about users, user accounts, user status, user profile fields, what groups or apps a user has access to, what MFA factors a user has enrolled, whether a user has admin roles, or to look up a specific user by email address, login, or ID.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-users/scripts/users.py <command> [options]
```

### list
List users, optionally filtered.
```bash
uv run skills/okta-users/scripts/users.py list
uv run skills/okta-users/scripts/users.py list --filter 'status eq "ACTIVE"'
uv run skills/okta-users/scripts/users.py list --filter 'profile.department eq "Engineering"' --limit 100
uv run skills/okta-users/scripts/users.py list --search 'profile.department eq "Engineering"' --sort-by profile.lastName --sort-order asc
uv run skills/okta-users/scripts/users.py list --q jane --fields profile.login,profile.email --expand blocks
```
Options: `--search` (any profile attribute), `--q` (name-prefix search), `--sort-by`/`--sort-order` (search queries only), `--fields` (comma-separated), `--expand`.

### get
Get a single user by ID or login (email address).
```bash
uv run skills/okta-users/scripts/users.py get user@example.com
uv run skills/okta-users/scripts/users.py get 00u1ab2cd3EF4GH5IJ6K --expand blocks
```

### search
Search users by name or email using a keyword query.
```bash
uv run skills/okta-users/scripts/users.py search "Jane Smith"
uv run skills/okta-users/scripts/users.py search "jane@example"
```

### get-apps
List all app links (direct and indirect via group) assigned to a user.
```bash
uv run skills/okta-users/scripts/users.py get-apps user@example.com
```

### get-blocks
List what is blocking a user from accessing their account (e.g. pending terms of service, unknown device policy).
```bash
uv run skills/okta-users/scripts/users.py get-blocks user@example.com
```

### get-groups
List all groups the user is a member of.
```bash
uv run skills/okta-users/scripts/users.py get-groups user@example.com
```

### get-idps
List identity providers linked to the user.
```bash
uv run skills/okta-users/scripts/users.py get-idps user@example.com
```

### get-linked-objects
List linked object relationships for a user. The `relationship` argument is the relationship name (e.g. `manager`, `subordinates`).
```bash
uv run skills/okta-users/scripts/users.py get-linked-objects user@example.com manager
uv run skills/okta-users/scripts/users.py get-linked-objects user@example.com subordinates
```

### get-enrollments
List authenticator enrollments for a user. **Requires Okta Identity Engine (OIE).**
```bash
uv run skills/okta-users/scripts/users.py get-enrollments 00u1ab2cd3EF4GH5IJ6K
uv run skills/okta-users/scripts/users.py get-enrollments 00u1ab2cd3EF4GH5IJ6K --disclose-identifiers
```

### get-classification
Retrieve the user's classification (e.g. FULL, LITE). **Early Access feature — may not be available in all orgs.**
```bash
uv run skills/okta-users/scripts/users.py get-classification 00u1ab2cd3EF4GH5IJ6K
```

### get-clients
List OAuth clients for which the user has active grants or tokens.
```bash
uv run skills/okta-users/scripts/users.py get-clients user@example.com
```

### get-client-grants
List OAuth2 scope consent grants for a specific user+client pair.
```bash
uv run skills/okta-users/scripts/users.py get-client-grants user@example.com 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-users/scripts/users.py get-client-grants user@example.com 0oa1ab2cd3EF4GH5IJ6K --limit 50
```

### get-client-tokens
List refresh tokens issued to a specific user+client pair.
```bash
uv run skills/okta-users/scripts/users.py get-client-tokens user@example.com 0oa1ab2cd3EF4GH5IJ6K
uv run skills/okta-users/scripts/users.py get-client-tokens user@example.com 0oa1ab2cd3EF4GH5IJ6K --limit 50
```

### get-client-token
Get a specific refresh token for a user+client pair.
```bash
uv run skills/okta-users/scripts/users.py get-client-token user@example.com 0oa1ab2cd3EF4GH5IJ6K <tokenId>
```

### get-devices
List devices enrolled by a user. **Requires Okta Identity Engine (OIE).**
```bash
uv run skills/okta-users/scripts/users.py get-devices 00u1ab2cd3EF4GH5IJ6K
```

### get-factors
List enrolled MFA factors for a user.
```bash
uv run skills/okta-users/scripts/users.py get-factors user@example.com
```

### get-grants
List all OAuth2 scope consent grants for a user, optionally filtered by scope.
```bash
uv run skills/okta-users/scripts/users.py get-grants user@example.com
uv run skills/okta-users/scripts/users.py get-grants user@example.com --scope-id okta.users.read
uv run skills/okta-users/scripts/users.py get-grants user@example.com --limit 50
uv run skills/okta-users/scripts/users.py get-grants user@example.com --expand scope
```

### get-grant
Get a specific OAuth2 grant for a user.
```bash
uv run skills/okta-users/scripts/users.py get-grant user@example.com <grantId>
uv run skills/okta-users/scripts/users.py get-grant user@example.com <grantId> --expand scope
```

### get-risk
Retrieve the user's current risk level. **Not generally available — requires a specific SKU.**
```bash
uv run skills/okta-users/scripts/users.py get-risk 00u1ab2cd3EF4GH5IJ6K
```

### get-roles
List admin roles assigned to a user. Requires `okta.roles.read` scope for OAuth2 auth.
```bash
uv run skills/okta-users/scripts/users.py get-roles user@example.com
uv run skills/okta-users/scripts/users.py get-roles user@example.com --expand targets/groups
```

### get-role
Get a specific role assignment for a user.
```bash
uv run skills/okta-users/scripts/users.py get-role user@example.com <roleAssignmentId>
```

### get-subscriptions
List all notification subscriptions for a user.
```bash
uv run skills/okta-users/scripts/users.py get-subscriptions 00u1ab2cd3EF4GH5IJ6K
```

### get-subscription
Get a specific notification subscription by type.
```bash
uv run skills/okta-users/scripts/users.py get-subscription 00u1ab2cd3EF4GH5IJ6K OKTA_ANNOUNCEMENT
```

### get-factors-catalog
List the factor types available for enrollment by a user under the applicable authenticator enrollment policy.
```bash
uv run skills/okta-users/scripts/users.py get-factors-catalog user@example.com
```

### get-factors-questions
List available security questions for a user.
```bash
uv run skills/okta-users/scripts/users.py get-factors-questions user@example.com
```

### get-factor
Get a specific enrolled factor for a user by ID.
```bash
uv run skills/okta-users/scripts/users.py get-factor user@example.com <factorId>
```

### get-factor-transaction
Get the status of a `push` factor verification transaction.
```bash
uv run skills/okta-users/scripts/users.py get-factor-transaction user@example.com <factorId> <transactionId>
```

### get-enrollment
Get a specific authenticator enrollment by ID. **Requires Okta Identity Engine (OIE); Limited GA.**
```bash
uv run skills/okta-users/scripts/users.py get-enrollment 00u1ab2cd3EF4GH5IJ6K <enrollmentId>
uv run skills/okta-users/scripts/users.py get-enrollment 00u1ab2cd3EF4GH5IJ6K <enrollmentId> --disclose-identifiers
```

### get-role-governance
Retrieve the governance sources of a role assignment. **Limited GA.**
```bash
uv run skills/okta-users/scripts/users.py get-role-governance user@example.com <roleAssignmentId>
```

### get-role-governance-grant
Retrieve a specific governance source for a role assignment. **Limited GA.**
```bash
uv run skills/okta-users/scripts/users.py get-role-governance-grant user@example.com <roleAssignmentId> <grantId>
```

### get-role-governance-grant-resources
List the resources of a role governance source grant. **Limited GA.**
```bash
uv run skills/okta-users/scripts/users.py get-role-governance-grant-resources user@example.com <roleAssignmentId> <grantId>
```

### get-role-app-targets
List app targets for an `APP_ADMIN` role assignment.
```bash
uv run skills/okta-users/scripts/users.py get-role-app-targets user@example.com <roleAssignmentId>
```

### get-role-group-targets
List group targets for a `USER_ADMIN`, `HELP_DESK_ADMIN`, or `GROUP_MEMBERSHIP_ADMIN` role assignment.
```bash
uv run skills/okta-users/scripts/users.py get-role-group-targets user@example.com <roleAssignmentId>
```

### get-role-targets
Retrieve all role targets (apps and/or groups) for a role assignment, optionally filtered by assignment type.
```bash
uv run skills/okta-users/scripts/users.py get-role-targets user@example.com <roleAssignmentId>
uv run skills/okta-users/scripts/users.py get-role-targets user@example.com <roleAssignmentId> --assignment-type GROUP
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

Every command's `id` argument accepts either an Okta user ID (`00u…`) or a login. Only `/api/v1/users/{idOrLogin}` accepts a login natively, so for the sub-resource commands a login costs one extra lookup to resolve it to an ID first; an unknown login surfaces as a 404 on that lookup.

JSON to stdout. List operations return an array. Single-resource operations (`get`, `get-classification`, `get-client-token`, `get-grant`, `get-risk`, `get-role`, `get-subscription`, `get-factor`, `get-factor-transaction`, `get-enrollment`, `get-role-governance`, `get-role-governance-grant`) return a single object. Errors are JSON with an `error` key written to stderr; exit code 1.

## Filter Reference

Common SCIM filter expressions for `--filter`:
- `status eq "ACTIVE"` — active users only
- `status eq "DEPROVISIONED"` — deprovisioned users
- `profile.department eq "Engineering"` — by department
- `lastUpdated gt "2024-01-01T00:00:00.000Z"` — recently updated

## Output Schema

### User object (`get`, `list`, `search`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta user ID (e.g. `00u1ab2cd3EF4GH5IJ6K`); use this to look up the user in other skills |
| `status` | string | Current account state (see Status Values below) |
| `profile.login` | string | Username / email address used to sign in |
| `profile.email` | string | Primary email address |
| `profile.firstName` / `profile.lastName` | string | Display name components |
| `profile.department` | string | Department, if populated |
| `profile.mobilePhone` | string | Mobile phone number, if populated |
| `credentials.password.value` | — | Never populated in API responses; presence of the key indicates a password is set |
| `credentials.provider.type` | string | `OKTA`, `ACTIVE_DIRECTORY`, `LDAP`, `FEDERATION`, `SOCIAL` — where the user authenticates |
| `credentials.provider.name` | string | Name of the external provider, if applicable |
| `lastLogin` | ISO 8601 string | When the user last signed in |
| `lastUpdated` | ISO 8601 string | When the user record was last modified |
| `passwordChanged` | ISO 8601 string | When the password was last changed |
| `statusChanged` | ISO 8601 string | When the status last changed |
| `activated` | ISO 8601 string | When the account was first activated |
| `_links` | object | HAL links for lifecycle actions (activate, deactivate, suspend, etc.) — presence indicates the action is available |

### App link object (`get-apps`)

| Field | Type | Description |
|---|---|---|
| `id` | string | App instance ID |
| `label` | string | Display name of the application |
| `appName` | string | App integration name (e.g. `salesforce`, `google`) |
| `appInstanceId` | string | App instance ID (same as `id`) |
| `linkUrl` | string | URL users click to launch the app |
| `logoUrl` | string | App logo image URL |
| `sortOrder` | integer | Display order in the Okta dashboard |
| `hidden` | boolean | Whether the app is hidden from the user's dashboard |

### Factor object (`get-factors`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Factor ID |
| `factorType` | string | `token:software:totp`, `token:hardware`, `push`, `sms`, `call`, `email`, `question`, `web`, `u2f`, `webauthn` |
| `provider` | string | `OKTA`, `GOOGLE`, `SYMANTEC`, `RSA`, `DUO`, `YUBICO`, `FIDO`, `CUSTOM` |
| `status` | string | `ACTIVE`, `INACTIVE`, `PENDING_ACTIVATION`, `EXPIRED` |
| `created` | ISO 8601 | When the factor was enrolled |
| `lastUpdated` | ISO 8601 | When the factor was last updated |
| `profile` | object | Factor-specific detail (e.g. `phoneNumber` for SMS, `credentialId` for TOTP) |

### Role object (`get-roles`, `get-role`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Role assignment ID |
| `type` | string | `SUPER_ADMIN`, `ORG_ADMIN`, `APP_ADMIN`, `USER_ADMIN`, `GROUP_MEMBERSHIP_ADMIN`, `HELP_DESK_ADMIN`, `READ_ONLY_ADMIN`, `MOBILE_ADMIN`, `API_ACCESS_MANAGEMENT_ADMIN`, `REPORT_ADMIN`, `CUSTOM` |
| `label` | string | Human-readable role name |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `created` / `lastUpdated` | ISO 8601 | Timestamps |
| `assignmentType` | string | `USER` (direct) or `GROUP` (via group membership) |

### Grant object (`get-grants`, `get-grant`, `get-client-grants`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Grant ID |
| `clientId` | string | OAuth client that received the grant |
| `scopeId` | string | The scope that was consented (e.g. `okta.users.read`) |
| `status` | string | `ACTIVE` or `REVOKED` |
| `created` | ISO 8601 | When the grant was created |
| `issuer` | string | Authorization server issuer URL |
| `source` | string | `END_USER` or `ADMIN` — who granted consent |

### Block object (`get-blocks`)

| Field | Type | Description |
|---|---|---|
| `blockType` | string | Reason the user is blocked: `UNKNOWN_DEVICE` (device trust required but device not recognized), `ANY_DEVICE` (all device access blocked) |

### Risk object (`get-risk`)

| Field | Type | Description |
|---|---|---|
| `riskLevel` | string | `LOW`, `MEDIUM`, `HIGH` |
| `reasons` | array | List of reason objects describing why the risk level was set |

## Interpretation

### Status values

| Status | Meaning |
|---|---|
| `ACTIVE` | User can sign in normally |
| `STAGED` | Account created but not yet activated; no activation email sent |
| `PROVISIONED` | Activation email sent; user has not yet completed activation |
| `RECOVERY` | User has a pending password reset or account unlock |
| `PASSWORD_EXPIRED` | Password is expired; user must reset before signing in |
| `LOCKED_OUT` | Account locked due to too many failed sign-in attempts; admin must unlock |
| `SUSPENDED` | Admin has suspended the account; user cannot sign in |
| `DEPROVISIONED` | Account deactivated; user cannot sign in and the account cannot be reactivated to ACTIVE directly |

### What to look for

- **Locked out users**: `status eq "LOCKED_OUT"` — correlate with `okta-logs login-failures --user <email>` to see the failure pattern
- **Stale accounts**: filter by `lastLogin` being very old or null combined with `status eq "ACTIVE"` — potential access hygiene issue
- **Federated vs. Okta-managed**: `credentials.provider.type` distinguishes users who authenticate via AD/LDAP/SAML from those managed directly in Okta; federated users cannot have their passwords reset in Okta
- **Recently deprovisioned**: filter by `status eq "DEPROVISIONED"` and `statusChanged gt "<date>"` to audit recent offboarding
- **Admin users**: `get-roles` returns non-empty when a user has admin role assignments — a user with `SUPER_ADMIN` or `ORG_ADMIN` has full org access
- **App access**: `get-apps` shows the full set of applications a user can launch, including those assigned via group membership; use when auditing what a specific user can reach
- **MFA gaps**: `get-factors` returns empty or only weak factors when a user has not completed MFA enrollment — check `factorType` and `status eq "ACTIVE"` to confirm
- **OAuth grants**: `get-grants` and `get-clients` show third-party apps the user has authorized; a long list of active grants may indicate shadow IT

### Cross-skill references

- `id` → use as the actor ID when correlating with `okta-logs list --q <id>` or `okta-logs login-failures --user <login>`
- `id` → `okta-groups get-members` results contain full user objects; match on `id` to confirm group membership
- `credentials.provider.type eq "ACTIVE_DIRECTORY"` → the user's authoritative source is AD; use `okta-logs list --filter 'eventType eq "user.authentication.auth_via_AD"'` to see authentication events
- `get-devices` → device IDs can be cross-referenced with `okta-devices get <deviceId>` for full device detail and `okta-device-assurance` for compliance status
- `get-groups` → group IDs can be passed to `okta-groups get <groupId>` or `okta-groups get-apps <groupId>` to see what that group assignment grants
