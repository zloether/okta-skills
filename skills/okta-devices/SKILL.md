---
name: okta-devices
description: Read Okta enrolled device records. Use when asked about devices, enrolled endpoints, which devices are registered to a user, device platform details, or device management status.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-devices/scripts/devices.py <command> [options]
```

### list
List enrolled devices, optionally filtered by a SCIM search expression.
```bash
uv run skills/okta-devices/scripts/devices.py list
uv run skills/okta-devices/scripts/devices.py list --search 'status eq "ACTIVE"'
uv run skills/okta-devices/scripts/devices.py list --search 'profile.platform eq "MACOS"'
uv run skills/okta-devices/scripts/devices.py list --expand user
uv run skills/okta-devices/scripts/devices.py list --limit 50
uv run skills/okta-devices/scripts/devices.py list --expand user --page-size 50 > devices.json
```
`--expand` (`user` or `userSummary`) embeds associated-user detail under `_embedded.users[]` (same shape as `get-users`, see below). `--limit` caps the total number of results and, when no `--page-size` is given, is also sent as the per-request page size (capped at 200). `--page-size` (1–200) sets that per-request size explicitly.

⚠️ `--expand` with Okta's default page size (200) can fail with a `500`. When `--expand` is set and `--page-size` is not, the script sends `limit=50`. Lower `--page-size` if you still see 500s.

Output is the full result as one indented JSON array (about 12 MB for ~8,000 devices) — redirect it to a file for fleet-wide pulls. Once a pull spans multiple pages, a `[okta-skills] fetched N devices` progress line is written to stderr after each page; expanded pages are slow (~160 calls took over 5 minutes for ~8,000 devices).

#### Fleet-wide device → user joins

Do **not** loop `get-users <id>` over every device — that is one Okta call per device (8,000 devices = 8,000 calls). Use one paginated expanded listing instead:
```bash
uv run skills/okta-devices/scripts/devices.py list --expand user --page-size 50 > devices.json
```
Each device then carries its users in `_embedded.users[]`. Use `--expand userSummary` for a lighter payload if the full user object isn't needed. Reserve `get-users` for a single device.

### get
Get a single device by ID.
```bash
uv run skills/okta-devices/scripts/devices.py get guo1ab2cd3EF4GH5IJ6K
```

### get-users
List users associated with a device.
```bash
uv run skills/okta-devices/scripts/devices.py get-users guo1ab2cd3EF4GH5IJ6K
```

### get-os-accounts / get-os-account
List all OS accounts for a device, or get a specific one. ⚠️ Early Access.
```bash
uv run skills/okta-devices/scripts/devices.py get-os-accounts guo1ab2cd3EF4GH5IJ6K
uv run skills/okta-devices/scripts/devices.py get-os-accounts guo1ab2cd3EF4GH5IJ6K --expand users
uv run skills/okta-devices/scripts/devices.py get-os-account guo1ab2cd3EF4GH5IJ6K <os_account_id>
```
`--expand` accepts a comma-separated list of `users`, `account_linked_enrollments`.

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

**Required OAuth scope** (`OKTA_CLIENT_SCOPES`): `okta.devices.read`. A `401`/`403` usually means the scope was not granted to the OAuth app.

## Output

JSON to stdout. List and `get-users` return arrays; `get` returns a single device object. Errors are JSON with an `error` key on stderr; exit code 1.

## Search Reference

Common SCIM expressions for `--search`:
- `status eq "ACTIVE"` — active devices
- `profile.platform eq "MACOS"` — macOS devices
- `profile.platform eq "WINDOWS"` — Windows devices
- `profile.managed eq true` — MDM-managed devices

## Output Schema

### Device object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta device ID (e.g. `guo1ab2cd3EF4GH5IJ6K`) |
| `status` | string | `ACTIVE`, `DEACTIVATED`, or `SUSPENDED` |
| `profile.displayName` | string | Device name as reported by the device/MDM |
| `profile.platform` | string | OS family — `WINDOWS`, `MACOS`, `IOS`, `ANDROID` (the Devices API does not return `CHROMEOS`; see Interpretation) |
| `profile.manufacturer` | string | Hardware manufacturer (free text, e.g. `APPLE` live; `Dell`) |
| `profile.model` | string | Hardware model (e.g. `MacBookPro18,1`) |
| `profile.osVersion` | string | OS version string as reported by the device |
| `profile.serialNumber` | string | Device serial number |
| `profile.udid` | string | Unique Device Identifier (iOS/macOS) |
| `profile.imei` | string | IMEI (mobile devices) |
| `profile.managed` | boolean | Whether the device is under MDM management |
| `profile.registered` | boolean | Whether the device has completed Okta device registration |
| `profile.secureHardwarePresent` | boolean | Whether secure hardware is present: TPM (Windows/Android) or Secure Enclave (macOS/iOS) |
| `profile.diskEncryptionType` | string | `ALL_INTERNAL_VOLUMES`, `FULL`, `USER` (encryption ON) or `NONE`, `SYSTEM_VOLUME` (encryption OFF); may be absent |
| `created` | ISO 8601 string | When the device was first registered with Okta |
| `lastUpdated` | ISO 8601 string | When the device record was last updated |
| `_embedded.users[]` | array | Only with `--expand user`/`userSummary`; each entry is a device-user object (below) |
| `_links` | object | HAL links including `users` (to retrieve associated users) |

### Device-user object (`get-users`)

Each object in the array (and each `_embedded.users[]` entry from `list --expand`) represents a user associated with the device. The user's own fields are **nested under `user`**, not at the top level:

| Field | Type | Description |
|---|---|---|
| `user.id` | string | Okta user ID |
| `user.status` | string | User's account status (same values as `okta-users`) |
| `user.profile.login` | string | User's login / email |
| `created` | ISO 8601 string | When the device-user link was created |
| `managementStatus` | string | `MANAGED` or `NOT_MANAGED` — whether this user/device relationship is MDM-managed |
| `screenLockType` | string | `NONE`, `PASSCODE`, or `BIOMETRIC` — screen lock for this user on this device |

With `--expand userSummary`, `user` holds a summary rather than the full user object.

## Interpretation

### What managed vs. registered means

- **`profile.registered = true`**: The device has enrolled with the Okta device trust flow. Okta knows it exists.
- **`profile.managed = true`**: The device is additionally enrolled in an MDM solution (Jamf, Intune, etc.). MDM management is what device assurance policies typically require to enforce OS version and encryption checks.
- A device can be registered (Okta knows it) but unmanaged (no MDM) — it will fail device assurance rules that require `managed eq true`.

### What to look for

- **Registered but unmanaged devices**: `profile.registered eq true and profile.managed eq false` — users have enrolled but their devices aren't MDM-managed; they may be failing access policies silently.
- **Missing screen lock or disk encryption**: device-user `screenLockType` of `NONE`, or `profile.diskEncryptionType` of `NONE`/`SYSTEM_VOLUME` or absent, not matching what device assurance requires — the device won't satisfy posture checks.
- **Multiple users per device**: `get-users` returning more than one user on a device is normal for shared workstations; unusual on mobile devices and worth flagging.
- **Stale device records**: `lastUpdated` very old + `status eq "ACTIVE"` — device may be lost, decommissioned, or from a former employee.
- **`secureHardwarePresent` on macOS/iOS**: the raw `TpmPresent` log attribute is always `false` on Apple devices (no TPM) — this is expected, not a failure. Use `profile.secureHardwarePresent` (Secure Enclave) to evaluate this requirement instead.

### Cross-skill references

- `id` → referenced in `okta-logs` as `target[].id` where `target[].type eq "DeviceEnrollment"` or similar device lifecycle events
- **ChromeOS**: the Devices API only returns `WINDOWS`, `MACOS`, `IOS` and `ANDROID`, so it cannot answer Chromebook questions. ChromeOS device trust is configured via Chrome Device Trust — see `okta-device-integrations` (connector config) and `okta-device-assurance` (ChromeOS assurance policies).
- `profile.platform` + `profile.osVersion` → compare against `okta-device-assurance list` to check whether the device meets the platform's OS version requirement
- Device-user `user.id` → `okta-users get <id>` for the user's full profile; `okta-logs login-failures --user <login>` for recent login failures associated with that user
