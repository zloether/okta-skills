---
name: okta-policies
description: Read Okta policies and policy rules including sign-on, MFA enrollment, password, and access policies. Use when asked about authentication policies, MFA requirements, password requirements, session lifetimes, or policy rule configurations.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
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
uv run skills/okta-policies/scripts/policies.py list --type ACCESS_POLICY --status ACTIVE --q Engineering --expand rules --sort-by name --resource-id 0oa1ab2cd3EF4GH5IJ6K
```
Options: `--status` (`ACTIVE`/`INACTIVE`), `--q` (name-prefix search), `--expand`, `--sort-by`, `--resource-id` (scope to policies tied to an authorization server), `--limit` (maximum number of results).

### get
Get a single policy by ID.
```bash
uv run skills/okta-policies/scripts/policies.py get 00p1ab2cd3EF4GH5IJ6K
uv run skills/okta-policies/scripts/policies.py get 00p1ab2cd3EF4GH5IJ6K --expand rules
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

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

## Output

JSON to stdout. List operations return arrays; `get`, `get-rule`, and `get-mapping` return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

Note: `listPolicyApps` (`GET /policies/{id}/app`) is deprecated by Okta in favor of `list-mappings`/`get-mapping` and is intentionally not implemented here.

## Policy Type Reference

| Type | Admin console name | Description |
|---|---|---|
| `OKTA_SIGN_ON` | Global Session Policy | Session lifetime, idle timeout, primary factor, IdP/session-level access |
| `ACCESS_POLICY` | Authentication Policies | App sign-in policies — the per-app ALLOW/DENY and factor requirements |
| `ACCESS_POLICY` | Okta Account Management Policy | Self-service recovery/unlock. Same type as above; distinguished by `_embedded.resourceType eq "END_USER_ACCOUNT_MANAGEMENT"` (all other `ACCESS_POLICY` objects return `APP`) |
| `MFA_ENROLL` | Authenticator Enrollment Policies | Which authenticators a user may or must enroll |
| `PASSWORD` | Password Policy | Password complexity, age, and self-service settings |
| `PROFILE_ENROLLMENT` | Profile Enrollment Policies | Self-registration and progressive profiling |
| `IDP_DISCOVERY` | Identity Provider Routing Rules | IdP routing/discovery |
| `ENTITY_RISK` / `POST_AUTH_SESSION` | Identity Threat Protection | Entity risk policies and session violation enforcement |
| `OAUTH_AUTHORIZATION_POLICY` | — | OAuth 2.0 authorization server policies (see `okta-authorization-servers`) |

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

- **OKTA_SIGN_ON**: `actions.signon.access` (`ALLOW` or `DENY`), `actions.signon.requireFactor` (boolean), `actions.signon.primaryFactor` (e.g. `PASSWORD_IDP_ANY_FACTOR`), `actions.signon.factorPromptMode` (`ALWAYS`, `SESSION`, `DEVICE`), `actions.signon.session.maxSessionLifetimeMinutes` / `maxSessionIdleMinutes` / `usePersistentCookie`
- **ACCESS_POLICY**: `actions.appSignOn.access` (`ALLOW` or `DENY`) and `actions.appSignOn.verificationMethod` — see Factor requirements below
- **MFA_ENROLL**: `actions.enroll.self` (`REQUIRED`, `OPTIONAL`, `CHALLENGE`, `NOT_ALLOWED`). This is the rule-level trigger; **which** authenticators are permitted lives on the policy object at `settings.authenticators[]`, not on the rule — see below
- **PASSWORD**: `actions.passwordChange.access`, `actions.selfServiceUnlock.access`, `actions.selfServicePasswordReset.access`. When `actions.selfServicePasswordReset.requirement.accessControl eq "AUTH_POLICY"`, the real requirements are deferred to the Okta Account Management Policy, not defined here

### Factor requirements (`ACCESS_POLICY`)

`actions.appSignOn.verificationMethod` is where an authentication policy states what the user must present:

| Field | Description |
|---|---|
| `type` | `ASSURANCE` (constraint-based, OIE) or `FACTOR` |
| `factorMode` | `1FA` or `2FA` |
| `reauthenticateIn` | ISO 8601 duration; `PT0S` means re-authenticate on every attempt |
| `constraints[]` | Array of constraint objects. **Only one array element needs to be satisfied**, but within an element, every property must be satisfied. |

Each `constraints[]` element may contain `knowledge` and/or `possession` objects with:
- `authenticationMethods[]` — each `{key, method}`, e.g. `{"key": "okta_verify", "method": "signed_nonce"}` (Okta FastPass)
- `required` (boolean), `hardwareProtection`, `phishingResistant`, `userVerification` — each `REQUIRED` or absent

These properties aren't just declarative — Okta records what each authentication operation actually satisfied. `okta-logs`' `user.authentication.verify` events carry `target[].detailEntry.methodUsedVerifiedProperties` (`PHISHING_RESISTANT`, `HARDWARE_PROTECTED`, `USER_VERIFYING`, `USER_PRESENCE`, `DEVICE_BOUND`), which maps directly to these constraint fields. Use it to tell apart "user doesn't have this authenticator enrolled" from "user has it enrolled, but this particular operation didn't meet the required properties" (e.g. a synced passkey lacking `hardwareProtection`).

Any method named in `authenticationMethods[]` must be enrollable under the user's `MFA_ENROLL` policy **and** actually enrolled by the user, or the rule can never be satisfied. See the Interpretation section.

### Authenticator settings (`MFA_ENROLL` policy object)

`settings.authenticators[]` on the policy (from `get`, not `get-rules`) lists each authenticator with:

| Field | Description |
|---|---|
| `key` | Authenticator key — `okta_verify`, `okta_password`, `okta_email`, `webauthn`, `phone_number`, `google_otp`, etc. |
| `enroll.self` | `REQUIRED`, `OPTIONAL`, or `NOT_ALLOWED` |
| `constraints.aaguidGroups[]` | For `webauthn`, which AAGUID groups are permitted (`ANY` or specific IDs → `okta-authenticators get-aaguid`) |

`enroll.self eq "NOT_ALLOWED"` means the user cannot enroll that authenticator at all. An authenticator absent from the array is likewise unavailable.

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

### Four policies gate a single sign-in — check all of them

A `policy.evaluate_sign_on` DENY is never explained by one policy alone. Four policy types participate, and a failure in any one of them produces the same DENY outcome:

| Policy | Type to fetch | What it can block |
|---|---|---|
| Authentication policy (app sign-in) | `ACCESS_POLICY` (`resourceType: APP`) | Per-app ALLOW/DENY and the factor requirements the user must meet |
| Global Session Policy | `OKTA_SIGN_ON` | Whether an Okta session may be established at all; primary factor; session lifetime |
| Authenticator Enrollment Policy | `MFA_ENROLL` | Whether the user is even permitted to enroll the factor the authentication policy demands |
| Okta Account Management Policy | `ACCESS_POLICY` (`resourceType: END_USER_ACCOUNT_MANAGEMENT`) | Self-service recovery/unlock — relevant when the failure is a password reset or account unlock, not an app sign-in |

The log event's `target` array typically carries **more than one** `Rule` entry — one per policy that was evaluated. Resolve every one of them, not just the first. See `okta-logs` for how to map each `Rule` target back to its owning policy.

**The enrollment gate.** If the authentication policy's matched rule requires a method (e.g. `{"key": "okta_verify", "method": "signed_nonce"}`) that the user's `MFA_ENROLL` policy sets to `enroll.self: NOT_ALLOWED` — or omits from `settings.authenticators[]` entirely — the sign-in will DENY no matter how cleanly every other condition passes. Always compare the authentication policy's `verificationMethod.constraints[]` against the `MFA_ENROLL` policy's `settings.authenticators[]` before concluding that a condition on the authentication policy was the cause.

### Authentication policy rule conditions — evaluate every one

Run `get-rules <policyId>` and read the rules in ascending `priority` order. The rule that fired is not the whole story: if it is the catch-all (`conditions: null`, highest priority number, usually `DENY`), the user failed to match **every** earlier rule, so each earlier rule's conditions are where the answer lives. Work through all of them.

An `ACCESS_POLICY` rule's `conditions` may contain any of:

| Condition path | Resolve with |
|---|---|
| `people.groups.include[]` / `.exclude[]` | `okta-groups get-members <groupId>` |
| `people.users.include[]` / `.exclude[]` | `okta-users get <userId>` |
| `device.registered`, `device.managed` | Compare to `device.registered` / `device.managed` on the log event |
| `device.assurance.include[]` | `okta-device-assurance get <id>`, then compare each requirement to the event's `device` fields |
| `platform.include[]` | Compare to `device.os_platform` / `os_version` on the log event |
| `network.connection` (`ANYWHERE`/`ZONE`) with `network.include[]` / `.exclude[]` | `okta-network-zones get <zoneId>`; compare to `client.ipAddress` and `client.zone` on the event |
| `riskScore.level` | Compare to `securityContext.risk.level` on the event |
| `elCondition.condition` (custom Okta Expression Language) | See `okta-expression-language` (Identity Engine EL dialect) for full syntax/function reference and how to resolve every attribute it references |
| `userType.include[]` / `.exclude[]` | `okta-schemas get-user-type <typeId>` |
| `authenticationProviderCondition`, `clients`, `appInstances` | Compare to `authenticationContext` and the `AppInstance` target on the event |

Report **all** conditions, not just the first one that fails — a single attempt commonly fails several at once, and stopping at the first gives an incomplete answer.

### Point-in-time evaluation

Policy rules are evaluated against the user's state **at the moment of the request**, and policy configuration itself changes over time. Current state can therefore contradict what actually happened:

- Group membership: a user in the required group today may not have been then. Search `okta-logs` for `group.user_membership.add` / `group.user_membership.remove` between the failure timestamp and now.
- User profile attributes referenced by `elCondition` expressions: search for `user.account.update_profile` in the same window.
- The rules themselves: compare each policy's and rule's `lastUpdated` against the failure's `published` timestamp. If `lastUpdated` is newer, the configuration you are reading is not the configuration that ran — look for `policy.rule.update`, `policy.rule.deactivate`, and `policy.lifecycle.update` events in `okta-logs` to see what changed.
- Device state: `device.managed`, `device.registered`, OS version, and device-assurance signals as recorded on the log event are authoritative for that attempt; the current record from `okta-devices get` may have drifted.

State the assessed timestamp explicitly when reporting a conclusion.

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
- `actions.appSignOn.verificationMethod.constraints[].possession.authenticationMethods[].key` → check the authenticator is `ACTIVE` org-wide with `okta-authenticators list`, that the named `method` is `ACTIVE` under `okta-authenticators list-methods <id>`, and that the `MFA_ENROLL` policy's `settings.authenticators[]` does not set it to `NOT_ALLOWED`
- Policy/rule `lastUpdated` newer than the failure timestamp → search `okta-logs` for `policy.rule.update` and `policy.lifecycle.update` to recover the configuration that was actually in effect
- Rule `conditions.elCondition.condition` → `okta-expression-language` for the Identity Engine EL syntax/function reference, including the `accessRequest.*` attributes specific to the Okta Account Management Policy
