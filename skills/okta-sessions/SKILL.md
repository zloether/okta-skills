---
name: okta-sessions
description: Read Okta session information. Use when asked about a user's active session, session status, session expiration, authentication methods used in a session, or which identity provider a session was established through.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-sessions/scripts/sessions.py <command> [options]
```

### get
Retrieve information about a session by session ID.
```bash
uv run skills/okta-sessions/scripts/sessions.py get l7FbDVqS8zHSy65uJD85
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

JSON to stdout. `get` returns a single session object. Errors are JSON with an `error` key on stderr; exit code 1.

Note: there is no `list` operation — the Okta API only supports retrieving a session by its specific ID (e.g. from a session cookie or a log event's `target[].id`). Session IDs are not enumerable.

## Output Schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Session ID |
| `login` | string | Username of the session owner |
| `userId` | string | Okta user ID of the session owner; pass to `okta-users get <id>` |
| `status` | string | `ACTIVE`, `MFA_ENROLL`, or `MFA_REQUIRED` — see Status Reference below |
| `createdAt` | ISO 8601 string | When the session was created |
| `expiresAt` | ISO 8601 string | When the session expires absent further activity |
| `lastFactorVerification` | ISO 8601 string | When MFA was last verified in this session |
| `lastPasswordVerification` | ISO 8601 string | When the password was last verified in this session |
| `amr` | string[] | Authentication method reference codes used to establish/verify this session — see AMR Reference below |
| `idp.id` | string | ID of the identity provider that established the session (org ID if `type` is `OKTA`) |
| `idp.type` | string | `OKTA`, `ACTIVE_DIRECTORY`, `FEDERATION`, `LDAP`, etc. |

### Status Reference

| Status | Meaning |
|---|---|
| `ACTIVE` | Session is fully established and validated |
| `MFA_REQUIRED` | Session exists but requires second-factor verification before it's fully active |
| `MFA_ENROLL` | Session exists but the user must enroll an MFA factor |

### AMR Reference

| Code | Meaning |
|---|---|
| `pwd` | Password |
| `swk` | Proof-of-possession of a software key (e.g. Okta Verify Push) |
| `hwk` | Proof-of-possession of a hardware key (e.g. YubiKey) |
| `otp` | One-time passcode |
| `sms` | SMS |
| `tel` | Telephone call |
| `geo` | Geo-location signal |
| `fpt` | Fingerprint biometric |
| `kba` | Knowledge-based authentication (security question) |
| `mfa` | Generic multifactor verification occurred |
| `mca` | Multiple-channel authentication |
| `sc` | Smart card |

## Interpretation

### What to look for

- **`status eq "MFA_REQUIRED"` or `"MFA_ENROLL"`**: The session is not fully authenticated yet — the user has not completed sign-on. Don't treat this as equivalent to an `ACTIVE` session when reasoning about access.
- **`amr` without any MFA-related code** (`swk`, `hwk`, `otp`, `sms`, `tel`, `fpt`, `kba`, `mfa`, `mca`, `sc`) alongside a sensitive action: the session was established with password-only (`pwd`) authentication — check policy rules to see if MFA should have been required.
- **`idp.type` other than `OKTA`**: The session was established via federation/AD/LDAP rather than native Okta credentials — password-related fields may not reflect what the user actually entered.
- **Stale `lastFactorVerification` on a long-lived session**: If a policy re-prompts for MFA periodically, an old verification timestamp relative to `expiresAt` may indicate the session is coasting on an earlier factor check rather than a recent one.

### Cross-skill references

- `userId` → `okta-users get <userId>` for the full profile of the session owner
- `idp.id` (when `idp.type` is not `OKTA`) → `okta-users get-idps <userId>` to see the IdP link details
- Session `id` appears as `target[].id` in `okta-logs` events like `user.session.start`, `user.session.end`, and `policy.evaluate_sign_on` — use those events to find a session ID before calling `get`
- `amr` codes correspond to `authenticationContext` fields on related `okta-logs` events for the same session
