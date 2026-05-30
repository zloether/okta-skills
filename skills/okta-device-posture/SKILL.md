---
name: okta-device-posture
description: Read Okta device posture checks that evaluate real-time device health signals from endpoint management integrations. Use when asked about device posture checks, device health signals, or real-time compliance signals from tools like CrowdStrike, Carbon Black, or Microsoft Intune.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables. The Device Posture Checks API is Early Access; the org must have it enabled.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-device-posture/scripts/device_posture.py <command> [options]
```

### list
List all device posture checks.
```bash
python skills/okta-device-posture/scripts/device_posture.py list
```

### get
Get a single device posture check by ID.
```bash
python skills/okta-device-posture/scripts/device_posture.py get dpc1ab2cd3EF4GH5IJ6K
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list` returns an array of device posture check objects; `get` returns a single check. Errors are JSON with an `error` key on stderr; exit code 1.

## Notes

Device posture checks are distinct from device assurance policies. Assurance policies define static requirements (OS version, disk encryption); posture checks evaluate dynamic signals from integrated endpoint security tools at authentication time. Both can be used together in access policies.

The device posture checks API requires an Okta Adaptive MFA license.
