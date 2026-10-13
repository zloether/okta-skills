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

**Required OAuth scope** (`OKTA_CLIENT_SCOPES`): `okta.deviceAssurance.read`. A `401`/`403` usually means the scope was not granted to the OAuth app.

## Output

JSON to stdout. `list` returns an array of device assurance policy objects; `get` returns a single policy. Each object includes platform-specific requirements (e.g. `osVersion`, `diskEncryptionType.include`, `screenLockType.include`). The list endpoint has no pagination or filter params. Errors are JSON with an `error` key on stderr; exit code 1.

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
| `gracePeriod` | object | Optional. `type` is `BY_DATE_TIME` or `BY_DURATION`; `expiry` is the date-time or duration after which the policy is enforced |
| `displayRemediationMode` | string | `HIDE` or `SHOW` — whether remediation instructions are shown in the Sign-In Widget when a user is denied |
| `_links.self.href` | string | Self link |

### Platform-specific requirement fields

These fields are conditionally present depending on the platform:

| Field | Platforms | Description |
|---|---|---|
| `osVersion.minimum` | ANDROID, IOS, MACOS, WINDOWS | Static minimum OS version string the device must be running (e.g. `"14.0"`). Not present on CHROMEOS |
| `osVersion.dynamicVersionRequirement` | ANDROID, IOS, MACOS | Dynamic alternative to `minimum` (never both): `type` is `MINIMUM`, `EXACT`, or `EXACT_ANY_SUPPORTED`; `distanceFromLatestMajor` (integer 0-1; omitted for `EXACT_ANY_SUPPORTED`); `latestSecurityPatch` (boolean). On WINDOWS use `osVersionConstraints[]` instead |
| `osVersionConstraints[]` | WINDOWS | Per-major-version static or dynamic requirements, max 2 entries; mutually exclusive with `osVersion.minimum`. Each entry requires `majorVersionConstraint` (`WINDOWS_10` or `WINDOWS_11`); its `dynamicVersionRequirement.type` may also be `NOT_ALLOWED` |
| `diskEncryptionType.include[]` | MACOS, WINDOWS, ANDROID | MACOS/WINDOWS: `ALL_INTERNAL_VOLUMES` (FileVault / BitLocker). ANDROID: `FULL`, `USER` |
| `screenLockType.include[]` | ANDROID, IOS, MACOS, WINDOWS | Accepted screen locks: any of `PASSCODE`, `BIOMETRIC`, `NONE` |
| `jailbreak` | ANDROID, IOS | `false` means jailbroken/rooted devices are denied |
| `secureHardwarePresent` | WINDOWS, ANDROID, MACOS | Requires TPM (Windows/Android) or Secure Enclave (macOS). Not a field on IOS policies |
| `thirdPartySignalProviders` | all platforms | Signals from external providers. ANDROID: `androidDeviceTrust`, `devicePostureIdP`. IOS: `devicePostureIdP`. MACOS/WINDOWS/CHROMEOS: `dtc` (Chrome Device Trust Connector checks) and `devicePostureIdP` (`managed`, `compliant`) |
| `thirdPartySignalProviders.dtc.crowdStrikeAgentId` / `crowdStrikeCustomerId` | WINDOWS | CrowdStrike agent / customer ID the Chrome Device Trust check must report |
| `callerContext` | ANDROID | Caller context settings |
| `devicePostureChecks.include[]` | MACOS (observed live) | `{variableName, value}` entries — custom osquery posture checks the policy requires; not in the OpenAPI spec. `variableName` matches `okta-device-posture` output |

## Interpretation

### How device assurance policies work

Device assurance policies define *static* minimum requirements. At authentication time, Okta compares the device's reported attributes (from the Okta device record) against the policy requirements. If the device doesn't meet all requirements, access is denied.

Each policy applies to exactly one platform. An org typically has one policy per platform, but can have multiple (e.g. a stricter policy for privileged access apps and a relaxed one for standard apps).

### What to look for

- **`osVersion.dynamicVersionRequirement` instead of `minimum`**: the effective minimum moves as Apple/Google/Microsoft release versions; there is no fixed version string to compare against.
- **`osVersion.minimum` set to a recently released version**: Users on older devices may be abruptly locked out if the OS update hasn't been deployed yet via MDM. Cross-reference with `okta-devices list --search 'profile.platform eq "<PLATFORM>"'` to see how many devices are below the required version.
- **`jailbreak: false` missing on a mobile policy**: If `jailbreak` is not set, jailbroken devices are not blocked. This is the default; its absence is worth flagging for mobile platforms.
- **`thirdPartySignalProviders` present**: The policy is relying on signals from an EDR tool. The EDR integration must be working for any user to pass this check — an EDR outage can lock out all users subject to this policy.
- **`screenLockType` not set, or `include` contains `NONE`**: Devices with no screen lock will pass. Check whether this is intentional for the policy's use case.
- **Troubleshooting `secureHardwarePresent` on Apple devices**: the raw `TpmPresent` log attribute is always `false` on macOS/iOS — Apple hardware has no TPM, so this is expected and not a failure signal. Use `Secure Hardware Present` (`device.secure_hardware_present` in log events) instead; it reflects Secure Enclave support, which is what this requirement actually evaluates on Apple devices.

### Cross-skill references

- `id` → appears in `okta-policies get-rules` output as `conditions.device.assurance.include[]` (an array of policy IDs); use `get <id>` to read what the rule is enforcing
- `platform` + `osVersion.minimum` → compare against `okta-devices list --search 'profile.platform eq "<PLATFORM>"'` output (`profile.osVersion`) to identify non-compliant devices. This only works for static `minimum`, and the Devices API does not return CHROMEOS devices
- `devicePostureChecks.include[].variableName` → matches `variableName` on `okta-device-posture list` / `list-defaults` output
- Compliance failures surface in `okta-logs` as `policy.evaluate_sign_on` events with `outcome.result eq "DENY"` and a reason referencing device assurance; `target` will identify the policy rule
