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
List all network zones, optionally filtered by usage or system flag (mutually exclusive).
```bash
uv run skills/okta-network-zones/scripts/network_zones.py list
uv run skills/okta-network-zones/scripts/network_zones.py list --usage POLICY --limit 50
uv run skills/okta-network-zones/scripts/network_zones.py list --page-size 100
uv run skills/okta-network-zones/scripts/network_zones.py list --system true
```
For IP matching, `--cidrs` returns only IP zones as `{id, name, usage, status, gateways, proxies}`, with every entry normalized to CIDR (a single host becomes `/32`, a RANGE is split into the CIDR blocks that cover it exactly):
```bash
uv run skills/okta-network-zones/scripts/network_zones.py list --cidrs
uv run skills/okta-network-zones/scripts/network_zones.py list --usage BLOCKLIST --cidrs
```
A CIDR entry with host bits set comes back as its network address (`10.0.0.77/24` → `10.0.0.0/24`). That is the same address range, so lookups give the same result, but the string differs from the raw zone. Entries that cannot be parsed are listed in that zone's `unparsed` object, under `gateways` or `proxies`, instead of failing the run. With `--cidrs`, `--limit` counts IP zones only, so every zone is fetched first. For a compact overview of every zone type, use `list --select id,name,type,usage,status`.

`--usage` (`POLICY`/`BLOCKLIST`) and `--system` (`true`/`false`) are mutually exclusive; the Okta API only supports filtering zones by `id`, `usage`, and `system` — there's no server-side filter by `type` (filter client-side on the returned `type`; `--select` can trim output). `--limit` caps total results and is also sent as the API `limit` (page size) when `--page-size` isn't given; `--page-size 1-200` sets items per request. The spec defines `limit` (default -1) but no maximum — the 200 cap here is this CLI's own; the live API accepted `limit=500` on a small org, so behavior above 200 is unverified.

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

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

**Required OAuth scope** (`OKTA_CLIENT_SCOPES`): `okta.networkZones.read`. A `401`/`403` usually means the scope was not granted to the OAuth app.

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
| `system` | boolean | `true` for Okta's default system zones (`LegacyIpZone`, `BlockedIpZone`, `DefaultEnhancedDynamicZone`, `DefaultExemptIpZone`); `false` for custom zones |
| `usage` | string | `POLICY` (used in policy conditions) or `BLOCKLIST` (traffic is always blocked) |
| `gateways` | array or null | **IP zones only** — list of `{type, value}` entries where `type` is `CIDR` or `RANGE` and `value` is the IP or range. Observed forms: `CIDR` `"10.0.0.0/24"` or a bare IP with no mask, and `RANGE` `"a.b.c.d-e.f.g.h"` (a single host can be `"x-x"`). `null` when empty. Use `list --cidrs` to normalize |
| `proxies` | array or null | **IP zones only** — same structure as `gateways`; IPs (range/CIDR) allowed to forward requests from the gateway addresses, trusted by ThreatInsight to identify the client IP |
| `asns` | array / object | **DYNAMIC zones** — array of ASN strings (e.g. `"AS12345"`). **DYNAMIC_V2 zones** — object `{include: [...], exclude: [...]}` |
| `locations` | array / object | **DYNAMIC zones** — array of `{country, region}` objects (ISO 3166-1 country, optional ISO 3166-2 region, may be `null`). **DYNAMIC_V2 zones** — object `{include: [...], exclude: [...]}` of the same `{country, region}` items |
| `ipServiceCategories` | object | **DYNAMIC_V2 zones only** — `{include: [...], exclude: [...]}` of IP service categories (e.g. proxy/VPN services) |
| `proxyType` | string | **DYNAMIC zones** — `Any`, `Tor`, `NotTorAnonymizer`, or null/`""` for no proxy condition |
| `created` | ISO 8601 string | When the zone was created |
| `lastUpdated` | ISO 8601 string | When the zone was last modified |
| `_links.self.href` | string | Self link (`activate` / `deactivate` links also present depending on status) |

## Interpretation

### Zone usage

- **`POLICY`**: Referenced explicitly in sign-on policy rules via `conditions.network.include[]` or `conditions.network.exclude[]`. Users connecting from IPs in the zone are matched by those conditions.
- **`BLOCKLIST`**: Traffic from IPs in this zone is blocked at the perimeter — before any policy evaluation. Whether a log event is generated for blocked traffic is unverified.

### What to look for

- **Overlapping CIDR ranges**: Two IP zones covering the same range with different usages (one POLICY, one BLOCKLIST) — precedence between them is unverified; flag the overlap for review.
- **Inactive zones still referenced in policies**: A zone with `status eq "INACTIVE"` that is still referenced in policy conditions will never match — effectively removing that network condition from the rule without deleting the reference.
- **DYNAMIC zones with `proxyType eq "Tor"`**: Specifically targets Tor exit nodes. Presence of this zone in a BLOCKLIST usage means Tor connections are blocked org-wide.
- **System zones** (`system: true`): `BlockedIpZone` is the default blocklist; admins can rename system zones and add up to 5000 gateway/proxy entries. Check these first when asked "what is blocked".
- **Empty `gateways` array on an IP zone**: The zone exists but has no IP ranges configured — it will never match any client IP.

### Cross-skill references

- `id` → appears in `okta-policies get-rules` output as `conditions.network.include[].id` or `conditions.network.exclude[].id`; use `get <id>` to resolve the zone's IP ranges
- `gateways[].value` → compare against `client.ipAddress` in `okta-logs` events to determine whether a login came from a known/trusted network
- A login from an IP outside all known POLICY zones + `securityContext.isProxy eq true` → cross-reference with BLOCKLIST zones to understand why the login was allowed or denied
