---
name: okta-org-settings
description: Read Okta org-level settings — general org info, contact assignments, CAPTCHA, third-party admin, end-user preferences, Aerial consent, Okta communication opt-in, Okta Support access, admin console auto-assignment, public client app privileges, and YubiKey OTP tokens. Use when asked how the org itself is configured, who the billing/technical contacts are, whether Okta Support currently has access, or which YubiKey tokens are provisioned.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. `get-captcha-settings` is Limited GA (`isGenerallyAvailable: false`); all other operations are GA.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-org-settings/scripts/org_settings.py <command> [options]
```

### get
Get the org's general settings (name, address, support contact info, status, etc.).
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get
```

### list-contact-types / get-contact
List all org contact types, or get the user assigned to a specific one (`BILLING` or `TECHNICAL`).
```bash
uv run skills/okta-org-settings/scripts/org_settings.py list-contact-types
uv run skills/okta-org-settings/scripts/org_settings.py get-contact BILLING
```

### get-captcha-settings
Get the org-wide CAPTCHA settings (which CAPTCHA instance is enabled and on which pages). ⚠️ Limited GA.
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get-captcha-settings
```

### get-third-party-admin-setting
Get whether third-party admins are permitted to perform administrative actions.
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get-third-party-admin-setting
```

### get-preferences
Get the org's end-user UI preferences (currently just End-User Dashboard footer visibility).
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get-preferences
```

### get-aerial-consent
Get Okta Aerial consent grant details for the org. Returns `null` if consent hasn't been granted — that's the expected/normal response, not a failure.
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get-aerial-consent
```

### get-communication-settings
Get whether org users are opted in or out of Okta communication emails.
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get-communication-settings
```

### get-support-settings / list-support-cases
Get whether Okta Support currently has access to the org, or list all open Okta Support cases.
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get-support-settings
uv run skills/okta-org-settings/scripts/org_settings.py list-support-cases
```

### get-auto-assign-admin-app-setting
Get whether the Admin Console app is auto-assigned when an admin role is granted.
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get-auto-assign-admin-app-setting
```

### get-client-privileges-setting
Get whether new public client apps default to the Super Admin role.
```bash
uv run skills/okta-org-settings/scripts/org_settings.py get-client-privileges-setting
```

### list-yubikey-tokens / get-yubikey-token
List all YubiKey OTP tokens provisioned in the org, or get one by ID.
```bash
uv run skills/okta-org-settings/scripts/org_settings.py list-yubikey-tokens
uv run skills/okta-org-settings/scripts/org_settings.py list-yubikey-tokens --filter 'status eq "UNASSIGNED"' --limit 50
uv run skills/okta-org-settings/scripts/org_settings.py list-yubikey-tokens --expand-user
uv run skills/okta-org-settings/scripts/org_settings.py get-yubikey-token ykkwcx13nrDq8g4oy0g3
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list-`-prefixed commands return an array, except `list-support-cases` which returns a single object with a `supportCases` array field (the underlying endpoint doesn't paginate or wrap results the same way as the rest of the API). All other commands return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### General org settings (`get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Org ID |
| `companyName` | string | Org display name |
| `subdomain` | string | Okta subdomain |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `website`, `phoneNumber`, `supportPhoneNumber`, `endUserSupportHelpURL` | string | Contact/support info shown to end users |
| `address1` / `address2` / `city` / `state` / `postalCode` / `country` | string | Org's physical address |
| `created` / `lastUpdated` / `expiresAt` | ISO 8601 string | Timestamps |

### Contact type object (`list-contact-types`)

| Field | Type | Description |
|---|---|---|
| `contactType` | string | `BILLING` or `TECHNICAL` |

### Contact user (`get-contact`)

| Field | Type | Description |
|---|---|---|
| `userId` | string | ID of the user assigned to this contact type — cross-reference with `okta-users get` |

### CAPTCHA settings (`get-captcha-settings`)

| Field | Type | Description |
|---|---|---|
| `captchaId` | string | ID of the CAPTCHA instance enabled org-wide, if any |
| `enabledPages` | string[] | Which pages have CAPTCHA enabled, e.g. `SSPR`, `SSR`, `SIGN_IN` |

An empty object means no org-wide CAPTCHA settings are configured.

### Third-party admin setting (`get-third-party-admin-setting`)

| Field | Type | Description |
|---|---|---|
| `thirdPartyAdmin` | boolean | Whether third-party admin functionality is enabled |

### End-user preferences (`get-preferences`)

| Field | Type | Description |
|---|---|---|
| `showEndUserFooter` | boolean | Whether the footer is shown on the End-User Dashboard |

### Aerial consent (`get-aerial-consent`)

| Field | Type | Description |
|---|---|---|
| `accountId` | string | ID of the Aerial account with granted access |
| `grantedBy` | string | Principal ID of the user who granted access |
| `grantedDate` | ISO 8601 string | When access was granted |

### Communication settings (`get-communication-settings`)

| Field | Type | Description |
|---|---|---|
| `optOutEmailUsers` | boolean | If `true`, org users are opted out of Okta communication emails |

### Support settings (`get-support-settings`)

| Field | Type | Description |
|---|---|---|
| `support` | string | `ENABLED` (Okta Support currently has access) or `DISABLED` |
| `caseNumber` | string or null | Support case number tied to the current access grant, if any |
| `expiration` | ISO 8601 string or null | When the current access grant expires |

### Support case object (`list-support-cases`, under `supportCases`)

| Field | Type | Description |
|---|---|---|
| `caseNumber` | string | Okta Support case number |
| `subject` | string | Subject of the support case |
| `impersonation.status` | string | Whether Okta Support can sign in as an admin to troubleshoot this case |
| `impersonation.expiration` | ISO 8601 string or null | When impersonation access expires |
| `selfAssigned.status` | string | Whether self-assigned-case access is allowed |

### Auto-assign admin app setting (`get-auto-assign-admin-app-setting`)

| Field | Type | Description |
|---|---|---|
| `autoAssignAdminAppSetting` | boolean | If `true`, the Admin Console is auto-assigned whenever an admin role is assigned (doesn't apply to `SUPER_ADMIN`, which always gets it) |

### Client privileges setting (`get-client-privileges-setting`)

| Field | Type | Description |
|---|---|---|
| `clientPrivilegesSetting` | boolean | If `true`, new public client apps default to the Super Admin role |

### YubiKey OTP token object (`list-yubikey-tokens` / `get-yubikey-token`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the token — use with `get-yubikey-token` |
| `status` | string | `UNASSIGNED`, `ACTIVE`, `BLOCKED`, `REVOKED`, `DELETED`, or `INACTIVE` |
| `profile.serial` | string | The YubiKey's serial number |
| `created` / `lastUpdated` / `lastVerified` | ISO 8601 string | Timestamps |
| `_links.user.href` | string | Present only if the token is assigned to a user |

## Interpretation

### What to look for

- **`support: ENABLED` in `get-support-settings`**: Okta Support currently has standing access to sign in to the org as an admin — check `caseNumber` and `expiration` to see whether this is tied to an active, time-bound support case or has been left open indefinitely.
- **`thirdPartyAdmin: true`**: third-party admins can act in the Admin Console but can't receive Okta admin notifications, contact Okta Support, or sign in to the Help Center — a gap worth knowing about if you're relying on admin notification emails reaching everyone with admin access.
- **Empty `get-captcha-settings` response**: no org-wide CAPTCHA is configured — this doesn't mean CAPTCHA is off everywhere, since bot protection (`okta-security get-bot-protection-config`) and per-flow CAPTCHA settings are configured separately.
- **`optOutEmailUsers: true`**: org users won't receive Okta's own operational/product emails — this is independent of any org-specific email templates or notifications configured elsewhere.
- **Unassigned YubiKey tokens (`status: UNASSIGNED`)**: hardware provisioned but not yet handed to a user — a large unassigned pool may indicate a stalled rollout or inventory to reconcile against actual headcount.
- **`get-aerial-consent` returning `null`**: this is the documented behavior when no Aerial consent has been granted, not a broken skill — treat it the same as "no grant exists."

### Cross-skill references

- `get-contact` → `okta-users get <userId>` for the billing/technical contact's own profile and status
- YubiKey token `_links.user.href` → the assigned user's ID, cross-reference with `okta-users get-factors` to see it alongside their other enrolled factors
- Bot/CAPTCHA enforcement details beyond org-wide CAPTCHA config → `okta-security get-bot-protection-config`
