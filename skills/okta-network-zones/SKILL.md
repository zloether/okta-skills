---
name: okta-network-zones
description: Read Okta network zones including IP allowlists, blocklists, and dynamic zones. Use when asked about network zones, trusted IP ranges, blocked networks, geographic restrictions, or location-based access rules.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-network-zones/scripts/network_zones.py <command> [options]
```

### list
List all network zones, optionally filtered by type, usage, or system flag (mutually exclusive).
```bash
uv run skills/okta-network-zones/scripts/network_zones.py list
uv run skills/okta-network-zones/scripts/network_zones.py list --type IP
uv run skills/okta-network-zones/scripts/network_zones.py list --type DYNAMIC
uv run skills/okta-network-zones/scripts/network_zones.py list --usage POLICY --limit 50
uv run skills/okta-network-zones/scripts/network_zones.py list --system true
```
`--type`, `--usage` (`POLICY`/`BLOCKLIST`), and `--system` (`true`/`false`) are mutually exclusive; note the spec documents filtering as supported on id/usage/system, not type — verify `--type` against a live org. `--limit` caps results.

### get
Get a single network zone by ID.
```bash
uv run skills/okta-network-zones/scripts/network_zones.py get nzo1ab2cd3EF4GH5IJ6K
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

## Output Schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Okta zone ID (e.g. `nzo1ab2cd3EF4GH5IJ6K`) |
| `name` | string | Human-readable zone name |
| `type` | string | `IP`, `DYNAMIC`, or `DYNAMIC_V2` |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `usage` | string | `POLICY` (used in policy conditions) or `BLOCKLIST` (traffic is always blocked) |
| `gateways` | array | **IP zones only** — list of `{type, value}` entries where `type` is `CIDR` or `RANGE` and `value` is the IP or range |
| `proxies` | array | **IP zones only** — same structure as `gateways`; IPs known to be proxy exit nodes for this zone |
| `asns` | array | **DYNAMIC zones only** — list of ASN strings (e.g. `"AS12345"`) |
| `locations` | array | **DYNAMIC zones only** — list of `{country, include}` objects for geographic restrictions |
| `proxyType` | string | **DYNAMIC zones** — `Any`, `TorAnonymizer`, `NotTorAnonymizer` |
| `created` | ISO 8601 string | When the zone was created |
| `lastUpdated` | ISO 8601 string | When the zone was last modified |

## Interpretation

### Zone usage

- **`POLICY`**: Referenced explicitly in sign-on policy rules via `conditions.network.include[]` or `conditions.network.exclude[]`. Users connecting from IPs in the zone are matched by those conditions.
- **`BLOCKLIST`**: Traffic from IPs in this zone is blocked at the perimeter — before any policy evaluation. No log event is generated for blocked traffic from blocklist zones.

### What to look for

- **Overlapping CIDR ranges**: Two IP zones covering the same range with different usages (one POLICY, one BLOCKLIST) — the blocklist wins but it can be confusing during audits.
- **Inactive zones still referenced in policies**: A zone with `status eq "INACTIVE"` that is still referenced in policy conditions will never match — effectively removing that network condition from the rule without deleting the reference.
- **DYNAMIC zones with `proxyType eq "TorAnonymizer"`**: Specifically targets Tor exit nodes. Presence of this zone in a BLOCKLIST usage means Tor connections are blocked org-wide.
- **Empty `gateways` array on an IP zone**: The zone exists but has no IP ranges configured — it will never match any client IP.

### Cross-skill references

- `id` → appears in `okta-policies get-rules` output as `conditions.network.include[].id` or `conditions.network.exclude[].id`; use `get <id>` to resolve the zone's IP ranges
- `gateways[].value` → compare against `client.ipAddress` in `okta-logs` events to determine whether a login came from a known/trusted network
- A login from an IP outside all known POLICY zones + `securityContext.isProxy eq true` → cross-reference with BLOCKLIST zones to understand why the login was allowed or denied
