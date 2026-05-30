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
