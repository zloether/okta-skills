---
name: okta-logs
description: Read Okta system log events including authentication attempts, admin actions, user lifecycle events, and security alerts. Use when asked about audit logs, login history, failed authentications, MFA events, admin activity, policy evaluations, or any event history in the org.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-logs/scripts/logs.py <command> [options]
```

### list
Fetch log events, optionally scoped by time range, event type, or filter expression.
```bash
# Last 100 events
uv run skills/okta-logs/scripts/logs.py list

# Events since a specific time
uv run skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z

# Time range
uv run skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z --until 2024-01-02T00:00:00Z

# Filter by event type (use --filter with a SCIM expression)
uv run skills/okta-logs/scripts/logs.py list --filter 'eventType eq "user.session.start"'
uv run skills/okta-logs/scripts/logs.py list --filter 'eventType eq "user.authentication.auth_via_mfa"'

# Filter by outcome
uv run skills/okta-logs/scripts/logs.py list --filter 'outcome.result eq "FAILURE"'

# Keyword search
uv run skills/okta-logs/scripts/logs.py list --q "user@example.com"

# Sort order
uv run skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z --sort-order DESCENDING

# Limit results
uv run skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z --limit 500
```

### login-failures
Fetch all login failures and denials in a single query, grouped by outcome and event type. Defaults to the last 24 hours if `--since` is not provided.

```bash
# Last 24 hours (default)
uv run skills/okta-logs/scripts/logs.py login-failures

# Specific time range
uv run skills/okta-logs/scripts/logs.py login-failures --since 2024-01-01T00:00:00Z --until 2024-01-02T00:00:00Z

# Scoped to a single user
uv run skills/okta-logs/scripts/logs.py login-failures --user user@example.com

# Limit results
uv run skills/okta-logs/scripts/logs.py login-failures --limit 200

# Keyword search and sort order
uv run skills/okta-logs/scripts/logs.py login-failures --q "password" --sort-order DESCENDING
```

Returns `{ summary, events }` where `summary` contains `total` (number of events in this response, not the total matching count in Okta), `truncated` (true if `--limit` may have cut off additional matching events), `by_outcome` (counts per outcome result), `by_event_type` (counts per eventType sorted by frequency), `since`, `until`, and `user`.

> **DENY vs. FAILURE**: When a user says they "can't log in" or had a "login failure," this almost always maps to a `DENY` outcome in Okta — a policy blocked the attempt before credentials were evaluated. `FAILURE` means credentials were evaluated and rejected (wrong password, bad OTP, etc.). Check DENY events first.

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

## Output

JSON to stdout. `list` returns an array of LogEvent objects. `login-failures` returns `{summary, events}`. Each event includes `eventType`, `published` (ISO 8601 timestamp), `actor`, `target`, `outcome`, `client`, and `authenticationContext` fields. Errors are JSON with an `error` key on stderr; exit code 1.

## Notes

- `--since` and `--until` accept ISO 8601 format: `2024-01-01T00:00:00Z`
- Without `--since`, `list` defaults to the last 7 days; `login-failures` defaults to the last 24 hours
- Large time ranges may return many events; use `--limit` to cap results
- To filter by event type in `list`, use `--filter 'eventType eq "<type>"'` — there is no separate `--event-type` flag

## Output Schema

Each log event is a LogEvent object. Key fields:

| Field | Type | Description |
|---|---|---|
| `eventType` | string | What happened (see Event Types below) |
| `published` | ISO 8601 string | When the event occurred |
| `outcome.result` | string | `SUCCESS`, `FAILURE`, `SKIPPED`, `ALLOW`, `DENY`, `CHALLENGE`, `UNKNOWN` |
| `outcome.reason` | string | Human-readable explanation when result is not SUCCESS |
| `actor.id` | string | Okta ID of the entity that performed the action |
| `actor.alternateId` | string | Login/email of the actor (more human-readable than `actor.id`) |
| `actor.displayName` | string | Full name of the actor |
| `actor.type` | string | `User`, `SystemPrincipal`, `PublicClientApp`, `WebApp` |
| `target` | array | Resources affected by the event; each item has `id`, `alternateId`, `displayName`, `type` |
| `client.ipAddress` | string | IP address of the client that triggered the event |
| `client.geographicalContext` | object | City, state, country derived from IP |
| `client.userAgent.rawUserAgent` | string | Browser/client user agent string |
| `authenticationContext.authenticationProvider` | string | `OKTA_AUTHENTICATION_PROVIDER`, `ACTIVE_DIRECTORY`, `LDAP`, `FEDERATION`, `SOCIAL`, `FACTOR_PROVIDER` |
| `authenticationContext.credentialType` | string | `OTP`, `SMS`, `PASSWORD`, `ASSERTION`, `IWA`, `EMAIL`, `OAUTH2`, `JWT` |
| `securityContext.isProxy` | boolean | Whether the request came through a known proxy or anonymizer |
| `displayMessage` | string | Human-readable summary of the event, suitable for showing directly to users |
| `severity` | string | `DEBUG`, `INFO`, `WARN`, `ERROR` |
| `transaction.id` | string | Groups related events within a single request; useful for tracing a login flow |
| `uuid` | string | Unique identifier for this log event |

## Event Types

Okta has hundreds of event types. The full catalog is at:
**https://developer.okta.com/docs/reference/api/event-types/**

Event type names follow a `<category>.<subcategory>.<action>` pattern. Knowing the category is usually enough to understand an unfamiliar event type without looking it up.

### Categories and representative examples

**`user.session.*`** — user sign-in and sign-out
- `user.session.start` — successful sign-in
- `user.session.end` — sign-out
- `user.session.access_admin_app` — user accessed the Okta Admin Console

**`user.authentication.*`** — authentication steps within a session
- `user.authentication.auth_via_mfa` — MFA factor verified
- `user.authentication.auth_via_AD` — authenticated via Active Directory
- `user.authentication.sso` — SSO token issued to an application
- `user.authentication.verify` — an authenticator operation was verified. The `target[]` entry with `type eq "AuthenticatorMethod"` carries `detailEntry.authenticatorKey`, `detailEntry.methodTypeUsed`, and `detailEntry.methodUsedVerifiedProperties` — a bracketed list of the security properties that operation actually satisfied (e.g. `[USER_PRESENCE, PHISHING_RESISTANT, HARDWARE_PROTECTED, USER_VERIFYING, DEVICE_BOUND]`). These map directly to Authentication Policy Rule constraint fields (`phishingResistant`, `hardwareProtection`, `userVerification`) — see the DENY diagnosis flow below.
- `user.authentication.verify_push_accepted` — Okta Verify push approved
- `user.authentication.verify_push_denied` — Okta Verify push denied by user

**`user.account.*`** — account state changes
- `user.account.lock` — account locked after too many failed attempts
- `user.account.unlock` — account manually unlocked by admin
- `user.account.reset_password` — password reset initiated
- `user.account.update_password` — password changed successfully

**`user.lifecycle.*`** — provisioning and deprovisioning
- `user.lifecycle.activate` — user account activated
- `user.lifecycle.deactivate` — user account deactivated
- `user.lifecycle.suspend` — user account suspended
- `user.lifecycle.unsuspend` — user account unsuspended
- `user.lifecycle.create` — user account created

**`policy.evaluate_sign_on`** — sign-on policy evaluated for a login attempt; outcome is `ALLOW`, `DENY`, or `CHALLENGE`. The `target` array identifies which policy and rule matched.

**`app.oauth2.*`** — OAuth 2.0 / OIDC token operations
- `app.oauth2.token.grant` — access token issued
- `app.oauth2.token.revoke` — access token revoked
- `app.oauth2.token.refresh` — access token refreshed

**`application.user_membership.*`** — app assignment changes
- `application.user_membership.add` — user assigned to app
- `application.user_membership.remove` — user removed from app

**`group.user_membership.*`** — group membership changes
- `group.user_membership.add` — user added to group
- `group.user_membership.remove` — user removed from group

**`system.agent.*`** — AD/LDAP agent health
- `system.agent.start` — agent started
- `system.agent.disconnected` — agent lost connection to Okta

**`security.threat.*`** — threat signals
- `security.threat.detected` — Okta's ThreatInsight flagged suspicious activity

## Interpretation

### Reading outcomes

- `SUCCESS` — the action completed as intended
- `FAILURE` — the action was attempted but rejected (wrong password, expired token, etc.)
- `DENY` — a policy explicitly blocked the action before it was attempted
- `CHALLENGE` — the user was prompted for additional verification (MFA step-up); not a failure
- `SKIPPED` — the event was not evaluated, usually because an earlier step already handled it
- `ALLOW` — a policy explicitly permitted the action (common in `policy.evaluate_sign_on` events)

A single login attempt often generates multiple events: a `policy.evaluate_sign_on` with `ALLOW` or `DENY`, followed by `user.authentication.auth_via_mfa` with `CHALLENGE` or `SUCCESS`, followed by `user.session.start` with `SUCCESS`. Look at the sequence, not just individual events.

### Diagnosing login failures

Start with `login-failures` to get a count breakdown by event type. The summary's `by_outcome` field shows DENY and FAILURE counts separately — check DENY first (see note above). Then:

1. **High `policy.evaluate_sign_on` DENY count** — the most common cause of user-reported "login failures." A sign-on policy is blocking access before credentials are evaluated. Diagnose step by step:
   1. Fetch the most recent DENY event for the user (use `login-failures --user <email>` or `list --filter 'actor.alternateId eq "<email>" and outcome.result eq "DENY"' --sort-order DESCENDING --limit 1`). Note its `published` timestamp — every later step is evaluated as of that moment, not now.
   2. Enumerate **every** entry in the `target` array. A single DENY normally carries several, and each is a separate line of inquiry:

      | `target[].type` | Meaning | Next step |
      |---|---|---|
      | `Rule` **with** `detailEntry.policyId` | Authentication policy (`ACCESS_POLICY`) rule that fired. IDs start with `rul`. `detailEntry.policyName` and `policyRulePriority` give context. | `okta-policies get-rules <policyId>` |
      | `Rule` **without** `detailEntry.policyId` | Global Session Policy (`OKTA_SIGN_ON`) or Authenticator Enrollment Policy (`MFA_ENROLL`) rule. IDs start with `0pr` and only `detailEntry.policyName` is given — resolve it by running `okta-policies list --type OKTA_SIGN_ON` and `--type MFA_ENROLL`, then `get-rules` on each policy and matching the rule `id`. | `okta-policies get-rules <policyId>` on the owning policy |
      | `AppInstance` | The app being accessed. `detailEntry.signOnModeEvaluationResult` shows whether the app-level evaluation itself denied. | `okta-apps get <id>` |
      | `UDDevice` | The device used. `detailEntry` carries the device signals actually evaluated, including `deviceIntegrator` (osquery/CrowdStrike results). | `okta-devices get <id>` |

      Do not stop at the first `Rule` target. An authentication policy rule that would have allowed access still produces a DENY if the enrollment or session policy rule blocked it.
   3. For each policy identified, run `okta-policies get-rules <policyId>` to fetch all rules in priority order.
   4. Find the matching rule by its `id`. If it is the catch-all rule (`conditions: null`, highest priority number), it means the user didn't satisfy any earlier rule — the earlier rules' conditions are where the real answer is. Read **each** lower-priority-number rule's `conditions` to understand what it requires; rules are evaluated in ascending `priority` and the first match wins.
   5. Evaluate **every** condition on the allow rule — do not stop at the first failure. A single login attempt can fail multiple conditions simultaneously, and reporting only one gives an incomplete picture. Check all of the following that are present:
      - `conditions.network` → compare against `client.ipAddress` and `client.zone` in the event; run `okta-network-zones get <id>` on any included/excluded zone IDs to resolve their IP ranges or geographic rules
      - `conditions.device.registered` / `conditions.device.managed` → compare against `device.registered` and `device.managed` in the event
      - `conditions.device.assurance.include[]` → for each assurance policy ID listed, run `okta-device-assurance get <id>` and compare every requirement against the device attributes in the event's `device` field: `device.os_version`, `device.managed`, `device.disk_encryption_type`, `device.screen_lock_type`, `device.secure_hardware_present`. On macOS/iOS, ignore the raw `TpmPresent` debug signal — it is always `false` on Apple hardware (no TPM); use `Secure Hardware Present` / `device.secure_hardware_present` (Secure Enclave) instead.
      - `conditions.platform.include[]` → compare against `device.os_platform` and `device.os_version` in the event
      - `conditions.people.groups.include[]` / `.exclude[]` → run `okta-groups get-members <groupId>` to verify whether the user is in the required group
      - `conditions.people.users.include[]` / `.exclude[]` → compare against `actor.id`
      - `conditions.riskScore.level` → compare against `securityContext.risk.level` in the event
      - `conditions.elCondition.condition` → a custom Okta Expression Language expression; read it and resolve every user attribute it references with `okta-users get <id>`
   6. Check the **enrollment gate**. Read the matched (or would-have-matched) authentication policy rule's `actions.appSignOn.verificationMethod.constraints[]` for the authenticator methods it demands — e.g. `{"key": "okta_verify", "method": "signed_nonce"}` (Okta FastPass). For each one, confirm the user could actually have used it:
      - `okta-policies get <mfaEnrollPolicyId>` → `settings.authenticators[]`: an entry with `enroll.self: NOT_ALLOWED`, or the key missing entirely, makes the requirement impossible to satisfy and guarantees a DENY regardless of every other condition passing
      - `okta-authenticators list` / `list-methods <id>` → the authenticator and the specific method must both be `ACTIVE` org-wide
      - `okta-users get-enrollments <userId>` → whether the user had that authenticator enrolled at the time. Its `key` values (`okta_password`, `okta_verify`, `webauthn`, …) match the policy vocabulary directly; `get-factors <userId>` gives the same picture keyed by `factorType` (e.g. `signed_nonce`). Both accept a user ID or a login — take the ID from `actor.id` on the event
   7. Check the constraint's **verified properties**, not just whether the right authenticator was used. `constraints[]` elements can require `phishingResistant`, `hardwareProtection`, and/or `userVerification` (each `REQUIRED` or absent) — an enrolled, correct-method authenticator can still fail the rule if the specific operation didn't carry those properties (e.g. a synced/cloud passkey lacking `hardwareProtection`, or a WebAuthn assertion without user verification). Find the matching `user.authentication.verify` event near the same `transaction.id` and read its `target[]` entry with `type eq "AuthenticatorMethod"`: `detailEntry.methodUsedVerifiedProperties` lists what the operation actually satisfied (`PHISHING_RESISTANT`, `HARDWARE_PROTECTED`, `USER_VERIFYING`, `USER_PRESENCE`, `DEVICE_BOUND`). Compare each `REQUIRED` constraint field against the presence of its corresponding property in that list.
   8. Present findings as a table with columns **Check**, **Required**, **Actual**, and **Pass?** — one row per condition, per assurance requirement, per required authenticator method, and per verified property, covering all checks regardless of whether earlier ones already failed, and grouped by which policy each check came from. Mark each row yes/no/unknown. If an integrator (osquery, CrowdStrike, etc.) returned an error instead of a value, show the error text in the Actual column and mark Pass? as **NO** — an unreadable signal fails the check.

2. **High `user.session.start` FAILURE count** — wrong password or locked account. Check `outcome.reason` for detail. If the account is locked, `user.account.lock` events will appear nearby.

3. **High `user.authentication.auth_via_mfa` FAILURE count** — MFA failures. Check `authenticationContext.credentialType` to see which factor is failing (OTP, PUSH, etc.).

4. **Failures from unexpected IPs** — compare `client.ipAddress` and `securityContext.isProxy` across events. A spike of failures from a single IP or proxy suggests a credential-stuffing attack.

5. **Failures for a specific user** — use `login-failures --user user@example.com` to scope. Then look up the user's current status with `okta-users get user@example.com` to see if their account is locked or deactivated.

### Reconstructing state as of the failure

Policies are evaluated against the user's state at the instant of the request, but every other skill returns state **as it is now**. Between the failure and your investigation, group membership, profile attributes, device posture, and the policy rules themselves may all have changed — so current data can contradict what actually happened and lead to the wrong conclusion.

After noting the failure's `published` timestamp, search the log for changes in the window between that timestamp and now:

```bash
# Group membership changes for the user
uv run skills/okta-logs/scripts/logs.py list \
  --filter 'eventType sw "group.user_membership." and target.id eq "<userId>"' \
  --since <failure_timestamp>

# Profile attribute changes for the user
uv run skills/okta-logs/scripts/logs.py list \
  --filter 'eventType eq "user.account.update_profile" and target.id eq "<userId>"' \
  --since <failure_timestamp>

# Policy and rule changes
uv run skills/okta-logs/scripts/logs.py list \
  --filter 'eventType sw "policy.rule." or eventType sw "policy.lifecycle."' \
  --since <failure_timestamp>
```

Then:

- **Group membership** — a `group.user_membership.add` after the failure means the user was *not* in that group at the time, even though `okta-groups get-members` shows them there now. The reverse applies to `.remove`.
- **Profile attributes** — relevant whenever a rule uses `conditions.elCondition`; the expression is evaluated against the profile as it was then.
- **Policy configuration** — compare each policy's and rule's `lastUpdated` (from `okta-policies get` / `get-rules`) against the failure timestamp. If it is newer, you are reading a configuration that did not exist during the attempt; the `policy.rule.update` events show what changed.
- **Device signals** — prefer the `device` object and the `UDDevice` target's `detailEntry` **on the event itself** over a current `okta-devices get`. The event records the signals that were actually evaluated.

Say explicitly which timestamp your conclusion is assessed against, and flag any check you could only answer with present-day data.

### Correlating across skills

- `actor.id` or `actor.alternateId` → `okta-users get <id>` to get the user's current profile and status
- `target[].id` where `target[].type eq "AppInstance"` → `okta-apps get <id>` to get app details
- `target[].id` where `target[].type eq "Rule"` → look up `target[].detailEntry.policyId`, then run `okta-policies get-rules <policyId>` to read all rules; match the denying rule by its `id`. When `detailEntry.policyId` is absent (rule IDs starting with `0pr`), the rule belongs to an `OKTA_SIGN_ON` or `MFA_ENROLL` policy — list both types and match on rule `id`
- `target[].id` where `target[].type eq "UDDevice"` → `okta-devices get <id>`; `detailEntry.deviceIntegrator` is a JSON string of per-integrator results (osquery, CrowdStrike, …) — an entry containing `genericError(...)` means that signal could not be read, which fails any device assurance check depending on it
- Authenticator methods named in a policy rule's `verificationMethod.constraints[]` → `okta-authenticators list-methods <id>` for org-wide availability and `okta-users get-factors <email>` for the user's enrollments
- `transaction.id` → filter `list` with `--q <transaction_id>` to retrieve all events in the same request chain
- `client.ipAddress` → cross-reference against `okta-network-zones list` to see if the IP falls within a known zone
