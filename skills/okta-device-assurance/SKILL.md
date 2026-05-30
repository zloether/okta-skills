---
name: okta-device-assurance
description: Read Okta device assurance policies that define device compliance requirements such as OS version minimums, disk encryption, and screen lock. Use when asked about device assurance policies, device compliance requirements, or what security standards a device must meet to access apps.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-device-assurance/scripts/device_assurance.py <command> [options]
```

### list
List all device assurance policies.
```bash
python skills/okta-device-assurance/scripts/device_assurance.py list
```

### get
Get a single device assurance policy by ID.
```bash
python skills/okta-device-assurance/scripts/device_assurance.py get dap1ab2cd3EF4GH5IJ6K
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list` returns an array of device assurance policy objects; `get` returns a single policy. Each object includes platform-specific requirements (e.g. `osVersion`, `diskEncryptionType`, `screenLockType`). Errors are JSON with an `error` key on stderr; exit code 1.

## Notes

Device assurance policies are platform-specific (ANDROID, IOS, MACOS, WINDOWS, CHROMEOS). Each policy applies to one platform. They are referenced by access policies to enforce compliance at authentication time.
