---
name: okta-behaviors
description: Read Okta behavior detection rules — the anomalous-location/IP/device/ASN and velocity checks used by risk-based sign-on and MFA policies. Use when asked what behavioral risk signals are configured, or to look up a specific rule's thresholds.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. GA.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-behaviors/scripts/behaviors.py <command> [options]
```

### list / get
List all behavior detection rules, or get one by ID.
```bash
uv run skills/okta-behaviors/scripts/behaviors.py list
uv run skills/okta-behaviors/scripts/behaviors.py get bhr1nd8PQhGcQtSxB0g4
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list` returns an array; `get` returns a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Output Schema

### Behavior detection rule object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the rule |
| `name` | string | Display name of the rule |
| `type` | string | `ANOMALOUS_LOCATION`, `ANOMALOUS_IP`, `ANOMALOUS_DEVICE`, `ANOMALOUS_ASN`, or `VELOCITY` |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `settings` | object | Threshold configuration; shape depends on `type` (see below) |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### `settings` by type

All history-based types (`ANOMALOUS_LOCATION`, `ANOMALOUS_IP`, `ANOMALOUS_DEVICE`, `ANOMALOUS_ASN`) share:

| Field | Type | Description |
|---|---|---|
| `maxEventsUsedForEvaluation` | integer | How many past login events form the user's baseline (1-100, default 20) |
| `minEventsNeededForEvaluation` | integer | Minimum baseline events required before the rule evaluates at all (0-10, default 0) |

Type-specific additions:

| Type | Field | Description |
|---|---|---|
| `ANOMALOUS_LOCATION` | `granularity` | Geofencing precision, e.g. country/subdivision/city/lat-long comparison |
| `ANOMALOUS_LOCATION` | `radiusKilometers` | Radius from coordinates, in km — only present when `granularity` is `LAT_LONG` |
| `ANOMALOUS_IP` | `maxEventsUsedForEvaluation` | Max 100, default 50 (overrides the shared default above) |
| `VELOCITY` | `velocityKph` | Speed threshold in km/h a user would need to exceed to be flagged (default 805 ≈ commercial flight speed) |

## Interpretation

### What to look for

- **Inactive rules give a false sense of coverage**: a rule appearing in `list` doesn't mean it's enforcing anything — check `status`. An `INACTIVE` `ANOMALOUS_LOCATION` rule means location-based risk signals aren't being generated at all, regardless of what sign-on policies reference it.
- **Low `minEventsNeededForEvaluation` means faster protection but noisier**: with the default of `0`, a brand-new user with no history is evaluated (and can trigger) from their very first login; a higher value delays protection until enough baseline data exists.
- **`VELOCITY` threshold too high is a silent gap**: the default `805` km/h only catches physically impossible travel (faster than commercial flight); a lower threshold catches more travel-based fraud but risks false positives for legitimate frequent travelers.
- **A rule with no consuming policy is inert**: this skill only shows the rule definitions, not which sign-on/MFA policies reference them — cross-check `okta-policies` to see if a rule is actually wired into an active policy condition.

### Cross-skill references

- Behavior rule `id` values are referenced by risk-based conditions in sign-on/MFA policy rules — cross-reference `okta-policies get-rule` to confirm a rule is actually consumed by an active policy
- Behavior detection triggering surfaces in `okta-logs` as `security.behaviors.behavior` events with a `debugContext` listing which behaviors (by type) fired for a given authentication — filter with `eventType eq "security.behaviors.behavior"`
