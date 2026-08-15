---
name: okta-security
description: Read Okta ThreatInsight configuration, security events providers (Shared Signals Framework / SSF receivers), SSF stream status, and bot protection settings. Use when asked about suspicious IP handling, whether ThreatInsight blocks or audits requests, SSF/CAEP integrations for cross-app session signal sharing, or bot detection enforcement.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-security/scripts/security.py <command> [options]
```

### get-threat-insight-config
Get the org's ThreatInsight configuration — how Okta responds to authentication requests from suspicious IP addresses.
```bash
uv run skills/okta-security/scripts/security.py get-threat-insight-config
```

### list-security-events-providers / get-security-events-provider
List or get security events provider instances — SSF receivers configured to receive Security Event Tokens (SETs) from Okta. ⚠️ Limited GA.
```bash
uv run skills/okta-security/scripts/security.py list-security-events-providers
uv run skills/okta-security/scripts/security.py get-security-events-provider sse1qg25RpusjUP6m0g5
```

### get-ssf-streams
Get all SSF stream configurations, or a single one with `--stream-id`. A stream configuration is tied to the OAuth 2.0 client ID that created it. ⚠️ Limited GA.
```bash
uv run skills/okta-security/scripts/security.py get-ssf-streams
uv run skills/okta-security/scripts/security.py get-ssf-streams --stream-id esc1k235GIIztAuGK0g5
```

### get-ssf-stream-status
Get whether a specific SSF stream is actively transmitting events. ⚠️ Limited GA.
```bash
uv run skills/okta-security/scripts/security.py get-ssf-stream-status esc1k235GIIztAuGK0g5
```

### get-bot-protection-config
Get the org's bot protection (CAPTCHA-free bot detection) configuration. ⚠️ Limited GA.
```bash
uv run skills/okta-security/scripts/security.py get-bot-protection-config
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

JSON to stdout. `list`-prefixed commands return arrays. `get-ssf-streams` returns an array if `--stream-id` is omitted, or a single object if it's given — the underlying Okta endpoint (`getSsfStreams`) is polymorphic. All other `get`-prefixed commands return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### ThreatInsight configuration (`get-threat-insight-config`)

| Field | Type | Description |
|---|---|---|
| `action` | string | `none` (ThreatInsight disabled), `audit` (logs suspicious requests to System Log only), or `block` (logs and blocks) |
| `excludeZones` | string[] | Network Zone IDs excluded from ThreatInsight logging/blocking — traffic from these zones is never flagged, even if `action` is `block` |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Security events provider object (`list-security-events-providers` / `get-security-events-provider`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier — use with `get-security-events-provider` |
| `name` | string | Display name of the provider instance |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `type` | string | The app type of the provider, e.g. `okta` |
| `settings.well_known_url` | string | Present if configured via SSF well-known discovery URL |
| `settings.issuer` / `settings.jwks_url` | string | Present if configured directly via issuer + JWKS URL instead of a well-known URL |
| `_links.self.href` | string | Link to this provider |

### SSF stream configuration object (`get-ssf-streams`)

| Field | Type | Description |
|---|---|---|
| `stream_id` | string | Unique identifier for the stream — use with `get-ssf-stream-status` |
| `iss` | string | Issuer set on transmitted SETs (Okta's domain) |
| `aud` | string or string[] | Audience(s) set on transmitted SETs |
| `format` | string | Subject identifier format, always `iss_sub` |
| `delivery.method` | string | Delivery method URI, e.g. `https://schemas.openid.net/secevent/risc/delivery-method/push` |
| `delivery.endpoint_url` | string | Where Okta POSTs SETs to |
| `events_requested` | string[] | Event type URIs the receiver asked to receive |
| `events_supported` | string[] | Event type URIs Okta (the transmitter) supports |
| `events_delivered` | string[] | Event type URIs Okta actually delivers on this stream (subset of `events_requested` ∩ `events_supported`) |
| `min_verification_interval` | integer | Minimum seconds between verification requests |

### SSF stream status object (`get-ssf-stream-status`)

| Field | Type | Description |
|---|---|---|
| `stream_id` | string | The stream this status applies to |
| `status` | string | `enabled` (transmitter is actively sending events) or `disabled` (no events transmitted or held) |

### Bot protection configuration (`get-bot-protection-config`)

| Field | Type | Description |
|---|---|---|
| `mode` | string | `DISABLED`, `LOG_ONLY` (events logged but not enforced), or `ENFORCED` |
| `level` | string | Detection sensitivity: `LOW`, `MEDIUM`, `HIGH`, or `ANY` (flag everything regardless of confidence) |
| `enforcementType` | string | How a detected bot is challenged, currently only `OKTA_CHALLENGE` |
| `supportedFlows` | string[] | Which flows have bot protection enabled: `SIGN_IN`, `SSPR` (self-service password recovery), `SSR` (self-service registration) |

## Interpretation

### What to look for

- **`action: none` on ThreatInsight**: ThreatInsight is effectively off — suspicious IPs aren't logged or blocked at all. Combined with weak network zone restrictions, this is a gap worth flagging in a security review.
- **`action: audit` vs `block`**: `audit` only logs to the System Log (`okta-logs`) without stopping the request — don't assume suspicious traffic was actually blocked without checking `action` is `block`.
- **Large `excludeZones` list**: Every zone in this list is fully exempt from ThreatInsight, including block mode. Cross-reference each ID with `okta-network-zones get <id>` — an overly broad or stale exclusion (e.g. a zone with wide-open CIDR ranges) undermines ThreatInsight entirely.
- **`mode: LOG_ONLY` on bot protection**: Bot detection events are recorded but never enforced — no requests are actually challenged. Check `okta-logs` for bot-detection events to see what would have been blocked under `ENFORCED`.
- **`status: disabled` on an SSF stream that's supposed to be live**: The receiver won't get any security events (e.g. session-revoked, credential-change signals) until the stream is re-enabled — this can silently break downstream session-revocation integrations.
- **`events_delivered` narrower than `events_requested`**: The receiver asked for event types Okta doesn't actually support or deliver on this stream — cross-check against `events_supported` to see the gap.
- **Inactive security events providers**: A provider with `status: INACTIVE` in `list-security-events-providers` won't receive events even if its associated SSF stream shows `status: enabled`.

### Cross-skill references

- ThreatInsight `excludeZones[]` entries → `okta-network-zones get <id>` for the zone's IP ranges/type
- ThreatInsight `block`/`audit` outcomes → `okta-logs` events with `eventType eq "security.threat.detected"` or similar, filtered by `client.ipAddress`
- Bot protection detection events → `okta-logs`, filtered by flow (`user.authentication.auth_via_mfa`, `user.account.password_reset`, etc. depending on `supportedFlows`)
- SSF stream `delivery.endpoint_url` → cross-reference against `okta-identity-providers` or app configuration if the receiver is itself an Okta-integrated app
