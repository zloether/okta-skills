---
name: okta-attack-protection
description: Read Okta Attack Protection settings — authenticator lockout/enforcement behavior and user lockout policy for brute-force protection. Use when asked whether brute-force lockout is enabled, how account lockout is configured, or how authenticators enforce factor ordering during high-assurance sign-in.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. `get-authenticator-settings` is Limited GA (`isGenerallyAvailable: false`); `get-user-lockout-settings` is GA.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-attack-protection/scripts/attack_protection.py <command> [options]
```

### get-authenticator-settings
Get the org's authenticator lockout/enforcement settings. ⚠️ Limited GA.
```bash
uv run skills/okta-attack-protection/scripts/attack_protection.py get-authenticator-settings
```

### get-user-lockout-settings
Get the org's user lockout policy settings.
```bash
uv run skills/okta-attack-protection/scripts/attack_protection.py get-user-lockout-settings
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

JSON to stdout. Both commands return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### Authenticator settings (`get-authenticator-settings`)

| Field | Type | Description |
|---|---|---|
| `verifyKnowledgeSecondWhen2faRequired` | boolean | If `true`, requires users to verify a possession factor before a knowledge factor when the assurance requires two-factor authentication (default: `false`) |

### User lockout settings (`get-user-lockout-settings`)

| Field | Type | Description |
|---|---|---|
| `preventBruteForceLockoutFromUnknownDevices` | boolean | If `true`, prevents brute-force lockout from unknown devices for the password authenticator (default: `false`) |

## Interpretation

### What to look for

- **`preventBruteForceLockoutFromUnknownDevices: false` (the default)**: repeated failed password attempts from an unrecognized device count toward the account's lockout threshold like any other attempt — an attacker can lock a legitimate user out of their account from a device the user has never used. `true` exempts unknown-device attempts from counting toward lockout, closing that denial-of-service vector at the cost of allowing more brute-force guesses from unknown devices before Okta's other rate limiting kicks in.
- **`verifyKnowledgeSecondWhen2faRequired: false` (the default)**: when 2FA is required, a knowledge factor (password, PIN) can be verified before a possession factor. `true` forces possession-first ordering, which reduces the value of a phished or leaked password alone.
- Neither setting on its own determines whether an account can be locked out at all — actual lockout thresholds (max attempts, lockout duration) live on the password policy, not here. Cross-check `okta-policies` for the active password policy's lockout configuration.

### Cross-skill references

- Account lockout events surface in `okta-logs` as `user.account.lock` — filter with `eventType eq "user.account.lock"` to see who has actually been locked out and correlate with `preventBruteForceLockoutFromUnknownDevices`.
- Lockout thresholds (max failed attempts before lockout, auto-unlock behavior) are set on the password policy — see `okta-policies get` for policies of type `PASSWORD`.
