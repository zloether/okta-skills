---
name: okta-policies
description: Read Okta policies and policy rules including sign-on, MFA enrollment, password, and access policies. Use when asked about authentication policies, MFA requirements, password requirements, session lifetimes, or policy rule configurations.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-policies/scripts/policies.py <command> [options]
```

### list
List policies by type. `--type` is required by the Okta API.
```bash
uv run skills/okta-policies/scripts/policies.py list --type OKTA_SIGN_ON
uv run skills/okta-policies/scripts/policies.py list --type MFA_ENROLL
uv run skills/okta-policies/scripts/policies.py list --type PASSWORD
uv run skills/okta-policies/scripts/policies.py list --type ACCESS_POLICY
```

### get
Get a single policy by ID.
```bash
uv run skills/okta-policies/scripts/policies.py get 00p1ab2cd3EF4GH5IJ6K
```

### get-rules
List all rules for a policy.
```bash
uv run skills/okta-policies/scripts/policies.py get-rules 00p1ab2cd3EF4GH5IJ6K
```

### get-rule
Get a single rule by ID.
```bash
uv run skills/okta-policies/scripts/policies.py get-rule 00p1ab2cd3EF4GH5IJ6K <rule_id>
```

### list-mappings / get-mapping
List or get the resources (apps) mapped to a policy — mainly relevant to `ACCESS_POLICY` (app sign-on) policies.
```bash
uv run skills/okta-policies/scripts/policies.py list-mappings 00p1ab2cd3EF4GH5IJ6K
uv run skills/okta-policies/scripts/policies.py get-mapping 00p1ab2cd3EF4GH5IJ6K <mapping_id>
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. List operations return arrays; `get`, `get-rule`, and `get-mapping` return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

Note: `listPolicyApps` (`GET /policies/{id}/app`) is deprecated by Okta in favor of `list-mappings`/`get-mapping` and is intentionally not implemented here.

## Policy Type Reference

| Type | Description |
|---|---|
| `OKTA_SIGN_ON` | Global session and authentication policies |
| `MFA_ENROLL` | MFA enrollment policies |
| `PASSWORD` | Password policies |
| `ACCESS_POLICY` | App sign-on (access) policies |
| `PROFILE_ENROLLMENT` | Profile enrollment policies |
| `IDP_DISCOVERY` | IdP routing/discovery policies |
| `OAUTH_AUTHORIZATION_POLICY` | OAuth 2.0 authorization server policies |

## Output Schema

### Policy object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta policy ID (e.g. `00p1ab2cd3EF4GH5IJ6K`) |
| `name` | string | Human-readable policy name |
| `type` | string | Policy type — see Policy Type Reference above |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `priority` | integer | Evaluation order; lower number = higher priority. Okta evaluates policies in priority order and stops at the first match. |
| `description` | string | Optional description |
| `conditions` | object | Conditions that determine which users/apps this policy applies to (e.g. group membership, app context) |
| `created` | ISO 8601 string | When the policy was created |
| `lastUpdated` | ISO 8601 string | When the policy was last modified |

### Rule object (`get-rules`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta rule ID; appears as `target[].id` in log events when this rule is matched |
| `name` | string | Human-readable rule name |
| `priority` | integer | Evaluation order within the policy; lower = higher priority |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `conditions` | object | Rule-level conditions: network zones, groups, device state, risk level, etc. |
| `actions` | object | What happens when this rule matches — see Actions below |

### Common rule actions by policy type

- **OKTA_SIGN_ON / ACCESS_POLICY**: `actions.signon.access` (`ALLOW` or `DENY`), `actions.signon.requireFactor` (boolean), `actions.signon.factorPromptMode` (`ALWAYS`, `SESSION`, `DEVICE`), `actions.signon.session.maxSessionLifetimeMinutes`
- **MFA_ENROLL**: `actions.enroll.self` (`REQUIRED`, `OPTIONAL`, `NOT_ALLOWED`) per factor type
- **PASSWORD**: `actions.passwordChange.access`, `actions.selfServiceUnlock.access`, `actions.selfServicePasswordReset.access`

### Policy mapping object (`list-mappings` / `get-mapping`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Mapping ID |
| `_links.application.href` | string | URL of the mapped application; extract the app ID from the URL path and pass to `okta-apps get <id>` |
| `_links.policy.href` | string | URL of this policy |

## Interpretation

### How Okta evaluates policies and rules

1. All policies of the requested type are sorted by `priority` (ascending).
2. Each policy's `conditions` is evaluated — the first policy whose conditions match is selected.
3. Within the selected policy, rules are sorted by `priority` and evaluated in order; the first matching rule applies.
4. If no rule matches, the default rule (lowest priority, always present) applies.

This means: a user hitting an unexpected `DENY` is matching a specific policy + rule combination. Find the policy from the log event's `target` array, then use `get-rules` to read the matching rule's conditions.

### What to look for

- **Catch-all rules**: The last rule in any policy (highest priority number) usually has no conditions — it's the default fallback. Its action tells you what happens to users who don't match any explicit rule.
- **DENY rules before ALLOW rules**: Rules are evaluated in order. A DENY rule with broad conditions (no network zone restriction, no group restriction) will block users who should be allowed if it has a lower priority number than the ALLOW rule.
- **Inactive rules**: `status eq "INACTIVE"` rules are skipped during evaluation. A rule that looks like it should be protecting access but is inactive is effectively not enforcing anything.
- **ACCESS_POLICY device conditions**: `conditions.device.managed`, `conditions.device.assurance.id` — these link to device assurance policies; fetch the referenced policy with `okta-device-assurance get <id>` to see what's required.

### Cross-skill references

- Rule `id` → appears as `target[].id` in `okta-logs` events of type `policy.evaluate_sign_on`; `target[].alternateId` usually contains the rule name — use this to map a log denial back to its source rule
- Policy `id` → use `get-rules <policy_id>` to enumerate rules; check `conditions.network.include[].id` against `okta-network-zones get <id>` to see which IP ranges the rule applies to
- Rule `conditions.device.assurance.id` → `okta-device-assurance get <id>` to read the device compliance requirements enforced by that rule
- Rule `conditions.people.groups.include[]` → `okta-groups get-members <group_id>` to enumerate which users the rule applies to
- `list-mappings` `_links.application.href` → extract the app ID and pass to `okta-apps get <id>` to see which app this `ACCESS_POLICY` governs
