---
name: okta-network-zones
description: Read Okta network zones including IP allowlists, blocklists, and dynamic zones. Use when asked about network zones, trusted IP ranges, blocked networks, geographic restrictions, or location-based access rules.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-network-zones/scripts/network_zones.py <command> [options]
```

### list
List all network zones, optionally filtered by type.
```bash
python skills/okta-network-zones/scripts/network_zones.py list
python skills/okta-network-zones/scripts/network_zones.py list --type IP
python skills/okta-network-zones/scripts/network_zones.py list --type DYNAMIC
```

### get
Get a single network zone by ID.
```bash
python skills/okta-network-zones/scripts/network_zones.py get nzo1ab2cd3EF4GH5IJ6K
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list` returns an array of zone objects; `get` returns a single zone. Errors are JSON with an `error` key on stderr; exit code 1.

## Zone Type Reference

| Type | Description |
|---|---|
| `IP` | Static IP range zones (CIDR blocks or individual IPs) |
| `DYNAMIC` | Dynamic zones based on ASN, geolocation, or other signals |
| `DYNAMIC_V2` | Enhanced dynamic zones (Okta Identity Engine) |
