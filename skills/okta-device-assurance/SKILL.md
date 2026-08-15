---
name: okta-device-assurance
description: Read Okta device assurance policies that define device compliance requirements such as OS version minimums, disk encryption, and screen lock. Use when asked about device assurance policies, device compliance requirements, or what security standards a device must meet to access apps.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-device-assurance/scripts/device_assurance.py <command> [options]
```

### list
List all device assurance policies.
```bash
uv run skills/okta-device-assurance/scripts/device_assurance.py list
```

### get
Get a single device assurance policy by ID.
```bash
uv run skills/okta-device-assurance/scripts/device_assurance.py get dap1ab2cd3EF4GH5IJ6K
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

JSON to stdout. `list` returns an array of device assurance policy objects; `get` returns a single policy. Each object includes platform-specific requirements (e.g. `osVersion`, `diskEncryptionType`, `screenLockType`). Errors are JSON with an `error` key on stderr; exit code 1.

## Notes

Device assurance policies are platform-specific (ANDROID, IOS, MACOS, WINDOWS, CHROMEOS). Each policy applies to one platform. They are referenced by access policies to enforce compliance at authentication time.

## Output Schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Device assurance policy ID (e.g. `dap1ab2cd3EF4GH5IJ6K`) |
| `name` | string | Human-readable policy name |
| `platform` | string | Target platform: `ANDROID`, `IOS`, `MACOS`, `WINDOWS`, `CHROMEOS` |
| `createdDate` | ISO 8601 string | When the policy was created |
| `lastUpdate` | ISO 8601 string | When the policy was last modified |
| `createdBy` / `lastUpdatedBy` | string | ID of the admin who created/last modified the policy |

### Platform-specific requirement fields

These fields are conditionally present depending on the platform:

| Field | Platforms | Description |
|---|---|---|
| `osVersion.minimum` | All | Minimum OS version string the device must be running (e.g. `"14.0"`) |
| `diskEncryptionType` | MACOS, WINDOWS | Required encryption state: `ALL_INTERNAL_VOLUMES` (macOS FileVault / Windows BitLocker) |
| `screenLockType` | All | Required screen lock: `PASSCODE`, `BIOMETRIC`, or both |
| `jailbreak` | ANDROID, IOS | `false` means jailbroken/rooted devices are denied |
| `secureHardwarePresent` | WINDOWS, ANDROID | Requires TPM / secure enclave |
| `thirdPartySignalProviders` | MACOS, WINDOWS, CHROMEOS | Integration with CrowdStrike / Carbon Black / Chrome Browser Cloud Management; contains `dtc` (device trust check) sub-object |
| `tpspCrowdStrikeAgentId` | MACOS, WINDOWS | Specific CrowdStrike agent ID required |
| `tpspCrowdStrikeCustomerId` | MACOS, WINDOWS | CrowdStrike customer ID for verification |

## Interpretation

### How device assurance policies work

Device assurance policies define *static* minimum requirements. At authentication time, Okta compares the device's reported attributes (from the Okta device record) against the policy requirements. If the device doesn't meet all requirements, access is denied.

Each policy applies to exactly one platform. An org typically has one policy per platform, but can have multiple (e.g. a stricter policy for privileged access apps and a relaxed one for standard apps).

### What to look for

- **`osVersion.minimum` set to a recently released version**: Users on older devices may be abruptly locked out if the OS update hasn't been deployed yet via MDM. Cross-reference with `okta-devices list --search 'profile.platform eq "<PLATFORM>"'` to see how many devices are below the required version.
- **`jailbreak: false` missing on a mobile policy**: If `jailbreak` is not set, jailbroken devices are not blocked. This is the default; its absence is worth flagging for mobile platforms.
- **`thirdPartySignalProviders` present**: The policy is relying on signals from an EDR tool. The EDR integration must be working for any user to pass this check — an EDR outage can lock out all users subject to this policy.
- **`screenLockType` not set**: Devices with no screen lock will pass. Check whether this is intentional for the policy's use case.

### Cross-skill references

- `id` → appears in `okta-policies get-rules` output as `conditions.device.assurance.id`; use `get <id>` to read what the rule is enforcing
- `platform` + `osVersion.minimum` → compare against `okta-devices list --search 'profile.platform eq "<PLATFORM>"'` output (`profile.osVersion`) to identify non-compliant devices
- Compliance failures surface in `okta-logs` as `policy.evaluate_sign_on` events with `outcome.result eq "DENY"` and a reason referencing device assurance; `target` will identify the policy rule
