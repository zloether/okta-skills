---
name: okta-device-posture
description: Read Okta device posture checks that evaluate real-time device health signals from endpoint management integrations, and draft/validate custom osquery-based Advanced Posture Checks locally. Use when asked about device posture checks, device health signals, real-time compliance signals from tools like CrowdStrike, Carbon Black, or Microsoft Intune, or about writing a custom osquery check for Okta.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. `list`, `list-defaults`, and `get` are all Limited GA (`isGenerallyAvailable: false`). The org must have the relevant feature enabled for these Limited GA endpoints.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-device-posture/scripts/device_posture.py <command> [options]
```

### list
List all device posture checks. Limited GA (`lifecycle: LIMITED_GA`).
```bash
uv run skills/okta-device-posture/scripts/device_posture.py list
```

### get
Get a single device posture check by ID. Limited GA (`lifecycle: LIMITED_GA`, `isGenerallyAvailable: false`).
```bash
uv run skills/okta-device-posture/scripts/device_posture.py get dpc1ab2cd3EF4GH5IJ6K
```

### list-defaults
List Okta's built-in (`BUILTIN`) default device posture checks, separate from any org-authored custom checks returned by `list`. Limited GA (`isGenerallyAvailable: false`) — may 403/404 in orgs where the rest of this API is enabled but this specific endpoint isn't yet rolled out.
```bash
uv run skills/okta-device-posture/scripts/device_posture.py list-defaults
```

## Advanced Posture Checks (custom osquery)

Advanced Posture Checks are a **different feature** from the device posture checks above: Okta
Verify runs an admin-authored [osquery](https://osquery.io/) SQL query on the device and reports
the result to a device assurance policy. Okta has no public API to create these — they're pasted
into the Admin Console by hand under **Security > Device Integrations > Device posture > Advanced
posture checks**. This skill only helps **draft and validate the check locally**; it never creates
anything in Okta.

```bash
uv run skills/okta-device-posture/scripts/osquery_check.py new \
  --title "Suspicious launch agent" --description "Detects a known malicious launchd entry." \
  --platform macOS --author you@example.com --reference https://example.com/threat-report \
  --out /tmp/check.yml

uv run skills/okta-device-posture/scripts/osquery_check.py validate /tmp/check.yml
```

`new` writes a YAML skeleton (repeat `--platform`/`--author`/`--reference` for multiple values;
pass `--query-file` once you have a finished query, otherwise it writes a commented TODO
placeholder). `validate` structurally checks an existing file — required fields, allowed platform
values, and whether the query looks like it follows one of the two patterns below — but it never
executes the query; only `osqueryi` (or Okta itself) can tell you if the SQL is actually valid.

### YAML format

Based on [Okta's sample osquery checks](https://github.com/okta/customer-detections/tree/master/sample_osquery_checks):

```yaml
title: <Human-readable name>
id: <32-char lowercase hex identifier, e.g. uuid4().hex>
description: <What the check detects and why it matters>
references:
  - <Links to threat intel or vendor documentation>
author:
  - <Author email>
platform: macOS                # or a list: [macOS, Windows, Linux]
query: |
  <osquery SQL query>
```

### Query patterns

Queries must return a **non-empty result set when the threat indicator is present** and an
**empty result set when the device is clean** — or, for the scored pattern, always return one row
with an explicit flag:

1. **Presence check** — simplest, best for a single strong indicator:
   ```sql
   SELECT 1 AS result FROM (
     SELECT path FROM file WHERE path LIKE '/path/to/indicator' LIMIT 1
   );
   ```
2. **Weighted/scored check** — combine several weak signals to cut down false positives, always
   returning exactly one row with a 0/1 flag:
   ```sql
   WITH indicator_a AS (SELECT COALESCE(COUNT(*), 0) AS total FROM processes WHERE name LIKE '%x%'),
        indicator_b AS (SELECT COALESCE(COUNT(*), 0) AS total FROM file WHERE path LIKE '%x%')
   SELECT CASE WHEN (indicator_a.total + indicator_b.total) > 1 THEN 1 ELSE 0 END AS detected
   FROM indicator_a, indicator_b;
   ```

Useful tables by platform: macOS — `launchd`, `file`, `processes`, `homebrew_packages`,
`npm_packages`, `listening_ports`, `apps`, `docker_images`, `docker_containers`; Windows —
`startup_items`, `file`, `processes`, `prefetch`, `chocolatey_packages`, `npm_packages`,
`listening_ports`, `programs`, `process_open_sockets`; cross-platform checks often join
`process_open_sockets` to `processes` on `pid`.

### Testing locally before deploying

Install [osquery](https://osquery.io/downloads) and run the query interactively before pasting it
into the Admin Console:
```bash
osqueryi --line "<query>"
```
Confirm it returns an empty result (or a `0` flag) on a clean machine, and a non-empty result (or
a `1` flag) when the indicator is artificially introduced, before trusting the check in a policy.

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

OAuth 2.0 private-key JWT auth is also supported as an alternative to `OKTA_CLIENT_TOKEN` — see [AGENTS.md](../../AGENTS.md#environment-variables) for the full variable list.

## Output

JSON to stdout. `list` and `list-defaults` return arrays of device posture check objects; `get` returns a single check. Errors are JSON with an `error` key on stderr; exit code 1.

## Notes

Device posture checks are distinct from device assurance policies. Assurance policies define static requirements (OS version, disk encryption); posture checks evaluate dynamic signals from integrated endpoint security tools at authentication time. Both can be used together in access policies.

The device posture checks API requires an Okta Adaptive MFA license.

## Output Schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Device posture check ID (e.g. `dpc1ab2cd3EF4GH5IJ6K`) |
| `name` | string | Human-readable check name |
| `type` | string | Integration type — see Integration Types below |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `created` | ISO 8601 string | When the check was created |
| `lastUpdated` | ISO 8601 string | When the check was last modified |
| `configuration` | object | Integration-specific configuration; structure varies by `type` |

### Integration types

| Type | Provider | What it checks |
|---|---|---|
| `CROWDSTRIKE` | CrowdStrike Falcon | Agent state, prevention policy score, OS vulnerability score |
| `CARBON_BLACK` | VMware Carbon Black | Agent state, sensor version, device policy |
| `WINDOWS_DEFENDER_ATP` | Microsoft Defender for Endpoint | Risk score, compliance state |
| `INTUNE` | Microsoft Intune | Compliance policy state, managed status |
| `CHROME_BROWSER_CLOUD_MGMT` | Google Chrome Browser Cloud Management | Browser version, extension policy |
| `WORKSPACE_ONE` | VMware Workspace ONE | Compliance state |

### Common configuration fields

Structure varies by integration. Representative fields:

- `configuration.agentStatus` — required agent state (e.g. `RUNNING`)
- `configuration.minimumScore` — minimum risk/health score threshold
- `configuration.complianceState` — required compliance status from the MDM (`COMPLIANT`)
- `configuration.crowdStrikeAgentId` / `crowdStrikeCustomerId` — CrowdStrike tenant binding

## Interpretation

### Device assurance vs. device posture

| Aspect | Device Assurance | Device Posture |
|---|---|---|
| Signal source | Okta device record (self-reported by device) | Third-party EDR / MDM in real time |
| When evaluated | At each authentication attempt | At each authentication attempt |
| License required | No (included in OIE) | Yes (Adaptive MFA) |
| Checks | OS version, disk encryption, screen lock | Agent health, risk score, compliance state |

Use posture checks when you need assurance from a trusted third-party tool (e.g. CrowdStrike confirms no active threats) rather than relying solely on what the device reports about itself.

### What to look for

- **Inactive posture checks referenced in policies**: An `INACTIVE` check is skipped at evaluation time — users who should be blocked by it will pass. Verify via `okta-policies get-rules` to see if the check is still referenced.
- **Missing or misconfigured `configuration`**: If `configuration` is empty or missing required fields (e.g. no `minimumScore` for a CrowdStrike check), the check may be evaluating as always-pass.
- **Integration outages**: If the third-party provider's API is unreachable, Okta's behavior depends on the policy's failure mode setting. Authentication failures from this cause will appear in logs with `outcome.reason` referencing the integration.
- **Multiple checks of the same type**: An org may have separate posture checks for different platforms or risk levels. List all checks to understand the full set of requirements in play.
- **BUILTIN vs. custom checks**: `list-defaults` returns Okta-authored checks available out of the box; `list` returns checks the org has actually configured (which may reference or extend a default). If a policy references a check ID not present in `list`, check `list-defaults` before assuming it's misconfigured.

### Cross-skill references

- `id` → appears in `okta-policies get-rules` output alongside device assurance conditions; use `get <id>` to read what third-party signal is being evaluated
- Posture-related authentication failures surface in `okta-logs` as `policy.evaluate_sign_on` events with `outcome.result eq "DENY"`; `outcome.reason` will indicate the device posture check
- `type eq "CROWDSTRIKE"` or `type eq "INTUNE"` → cross-reference `okta-device-assurance list` to see if overlapping platform-level requirements are also set (both can apply simultaneously)
