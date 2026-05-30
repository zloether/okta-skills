---
name: okta-devices
description: Read Okta enrolled device records. Use when asked about devices, enrolled endpoints, which devices are registered to a user, device platform details, or device management status.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-devices/scripts/devices.py <command> [options]
```

### list
List enrolled devices, optionally filtered by a SCIM search expression.
```bash
python skills/okta-devices/scripts/devices.py list
python skills/okta-devices/scripts/devices.py list --search 'status eq "ACTIVE"'
python skills/okta-devices/scripts/devices.py list --search 'profile.platform eq "MACOS"'
```

### get
Get a single device by ID.
```bash
python skills/okta-devices/scripts/devices.py get guo1ab2cd3EF4GH5IJ6K
```

### get-users
List users associated with a device.
```bash
python skills/okta-devices/scripts/devices.py get-users guo1ab2cd3EF4GH5IJ6K
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

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
| `status` | string | `ACTIVE` or `INACTIVE` |
| `profile.displayName` | string | Device name as reported by the device/MDM |
| `profile.platform` | string | OS family — `WINDOWS`, `MACOS`, `IOS`, `ANDROID`, `CHROMEOS` |
| `profile.manufacturer` | string | Hardware manufacturer (e.g. `Apple`, `Dell`) |
| `profile.model` | string | Hardware model (e.g. `MacBookPro18,1`) |
| `profile.osVersion` | string | OS version string as reported by the device |
| `profile.serialNumber` | string | Device serial number |
| `profile.udid` | string | Unique Device Identifier (iOS/macOS) |
| `profile.imei` | string | IMEI (mobile devices) |
| `profile.managed` | boolean | Whether the device is under MDM management |
| `profile.registered` | boolean | Whether the device has completed Okta device registration |
| `profile.secureHardwarePresent` | boolean | Whether a secure enclave / TPM is present |
| `profile.diskEncryptionType` | string | `ALL_INTERNAL_VOLUMES`, `SYSTEM_VOLUME`, or absent if not encrypted |
| `profile.screenLockType` | string | `PASSCODE`, `BIOMETRIC`, or absent if no screen lock |
| `created` | ISO 8601 string | When the device was first registered with Okta |
| `lastUpdated` | ISO 8601 string | When the device record was last updated |
| `_links` | object | HAL links including `users` (to retrieve associated users) |

### Device-user object (`get-users`)

Each object in the array represents a user associated with the device:

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta user ID |
| `status` | string | User's account status (same values as `okta-users`) |
| `profile.login` | string | User's login / email |
| `managementStatus` | string | `MANAGED` or `NOT_MANAGED` — whether this user/device relationship is MDM-managed |
| `screenLockType` | string | Screen lock type for this user on this device |

## Interpretation

### What managed vs. registered means

- **`profile.registered = true`**: The device has enrolled with the Okta device trust flow. Okta knows it exists.
- **`profile.managed = true`**: The device is additionally enrolled in an MDM solution (Jamf, Intune, etc.). MDM management is what device assurance policies typically require to enforce OS version and encryption checks.
- A device can be registered (Okta knows it) but unmanaged (no MDM) — it will fail device assurance rules that require `managed eq true`.

### What to look for

- **Registered but unmanaged devices**: `profile.registered eq true and profile.managed eq false` — users have enrolled but their devices aren't MDM-managed; they may be failing access policies silently.
- **Missing screen lock or disk encryption**: `profile.screenLockType` or `profile.diskEncryptionType` absent or not matching what device assurance requires — the device won't satisfy posture checks.
- **Multiple users per device**: `get-users` returning more than one user on a device is normal for shared workstations; unusual on mobile devices and worth flagging.
- **Stale device records**: `lastUpdated` very old + `status eq "ACTIVE"` — device may be lost, decommissioned, or from a former employee.

### Cross-skill references

- `id` → referenced in `okta-logs` as `target[].id` where `target[].type eq "DeviceEnrollment"` or similar device lifecycle events
- `profile.platform` + `profile.osVersion` → compare against `okta-device-assurance list` to check whether the device meets the platform's OS version requirement
- Device-user `id` → `okta-users get <id>` for the user's full profile; `okta-logs login-failures --user <login>` for recent login failures associated with that user
