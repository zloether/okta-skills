---
name: okta-device-posture
description: Read Okta device posture checks (osquery-based checks run by Okta Verify on the device and referenced by device assurance policies), and draft/validate custom osquery Advanced Posture Checks locally. Use when asked about device posture checks, custom osquery checks, the built-in default posture checks, or about writing a custom osquery check for Okta.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. `list`, `list-defaults`, and `get` are all non-GA in the spec (`isGenerallyAvailable: false`; `list` is LIMITED_GA, `list-defaults` is GA-flagged but not generally available). The org must have the relevant feature enabled.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-device-posture/scripts/device_posture.py <command> [options]
```

### list
List all device posture checks (custom, org-authored). Limited GA (`lifecycle: LIMITED_GA`). The endpoint has no pagination or filter params.
```bash
uv run skills/okta-device-posture/scripts/device_posture.py list
```

### get
Get a single device posture check by ID. Limited GA (`lifecycle: LIMITED_GA`, `isGenerallyAvailable: false`).
```bash
uv run skills/okta-device-posture/scripts/device_posture.py get dpc1ab2cd3EF4GH5IJ6K
```

### list-defaults
List Okta's built-in (`BUILTIN`) default device posture checks, separate from any org-authored custom checks returned by `list`. Not generally available (`isGenerallyAvailable: false`) — may 403/404 in orgs where the rest of this API is enabled but this specific endpoint isn't yet rolled out.
```bash
uv run skills/okta-device-posture/scripts/device_posture.py list-defaults
```

## Advanced Posture Checks (custom osquery)

Advanced Posture Checks are the same kind of object the commands above return as `type: CUSTOM`:
Okta Verify runs an admin-authored [osquery](https://osquery.io/) SQL query on the device and
reports the result to a device assurance policy. The spec has a create endpoint, but this skill is
read-only: it only helps **draft and validate the check YAML locally** (the YAML format below is
the Admin Console's paste-in format, under **Security > Device Integrations > Device posture >
Advanced posture checks**) and never creates anything in Okta. Use `list` to see checks already
created.

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

Result semantics (per [Okta's write-up on detecting shadow AI agents](https://www.okta.com/blog/threat-intelligence/detecting_shadow_ai_agents_with_advanced_posture_checks/)):
an **empty result or `0` means the device is clean**, and a **non-empty result or `1` means the
detection fired**. That result is what the device assurance policy evaluates. A query must therefore
return rows only when the indicator is present — or, for the scored pattern, always return exactly
one row with an explicit 0/1 flag.

Prefer the scored pattern. A single stray file or a process whose name merely contains a keyword is
weak evidence, so requiring two or more independent signals cuts false positives sharply. Use the
presence check only when one indicator is conclusive on its own.

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

### Building a check, step by step

This walks through detecting a hypothetical unsanctioned AI coding tool, `exampleagent`, on macOS.
Replace every `exampleagent` value with the real tool's bundle ID, paths, process name and port.

**1. Gather indicators of the tool, one per artifact type.** Install it on a test machine and note
what it leaves behind:

| Artifact type | Table | Example indicator |
|---|---|---|
| Installed app | `apps` | `bundle_identifier = 'com.exampleagent.app'` |
| Files and config | `file` | `/Applications/ExampleAgent.app`, `/Users/%/.exampleagent/config.json` |
| Running process | `processes` | `name = 'exampleagent'` |
| Network listener | `listening_ports` | `port = 8765` (local servers, MCP endpoints) |
| Login item / daemon | `launchd` | `name LIKE 'com.exampleagent.%'` |

**2. Write one CTE per artifact type and sum them.** Each CTE counts matches; the final `SELECT`
turns the total into a single 0/1 flag:

```sql
WITH app_hits AS (
  SELECT COUNT(*) AS total FROM apps WHERE bundle_identifier = 'com.exampleagent.app'
),
file_hits AS (
  SELECT COUNT(*) AS total FROM file
  WHERE path = '/Applications/ExampleAgent.app'
     OR path LIKE '/Users/%/.exampleagent/config.json'
),
process_hits AS (
  SELECT COUNT(*) AS total FROM processes
  WHERE name = 'exampleagent' AND path NOT LIKE '/System/%'
),
port_hits AS (
  SELECT COUNT(*) AS total FROM listening_ports WHERE port = 8765
)
SELECT CASE
  WHEN app_hits.total + file_hits.total + process_hits.total + port_hits.total > 1 THEN 1 ELSE 0
END AS exampleagent_detected
FROM app_hits, file_hits, process_hits, port_hits;
```

`COUNT(*)` always returns a row (0 when nothing matches), so each CTE is safe to join and the check
always yields exactly one row. The `> 1` threshold means two independent indicators are required.

**3. Scaffold, validate, and test.**

```bash
# save the query above to /tmp/query.sql, then:
uv run skills/okta-device-posture/scripts/osquery_check.py new \
  --title "ExampleAgent installed" --description "Detects the unsanctioned ExampleAgent AI coding tool." \
  --platform macOS --author you@example.com --query-file /tmp/query.sql --out /tmp/check.yml

uv run skills/okta-device-posture/scripts/osquery_check.py validate /tmp/check.yml
osqueryi --line "$(cat /tmp/query.sql)"   # expect exampleagent_detected = 0 on a clean machine
```

Install the tool on a test machine and re-run: you should see `exampleagent_detected = 1`. Then
uninstall it normally and re-run, since leftover config files can keep the score above the
threshold (see the uninstall pitfall below).

**4. Adapt for Windows.** Keep the same CTE-plus-threshold structure and swap in Windows tables and
paths: `programs` instead of `apps`, `startup_items` instead of `launchd`, and Windows file paths.
List `platform: [macOS, Windows]` only if one query is valid on both; otherwise create a separate
check per platform, since a table that is missing on one OS makes the whole query fail there.

### Pitfalls

- **Empty vs. non-empty is the signal.** A query that always returns a row (for example a bare
  `SELECT COUNT(*) ...`) looks "positive" on every device. Wrap counts in the scored pattern's
  `CASE WHEN ... THEN 1 ELSE 0` flag, or filter with `WHERE`/`LIMIT 1` for the presence pattern.
- **Constrain `file` queries.** osquery's `file` table needs a `path` or `directory` constraint,
  and a broad wildcard (for example `path LIKE '/Users/%/%'`) can walk a huge tree. Anchor the
  path as tightly as you can.
- **Schemas differ by platform and osquery version.** A table or column that exists on macOS may
  not exist on Windows, and a column added in a newer osquery release may be missing on the
  version bundled with Okta Verify. Run `.schema <table>` in `osqueryi` and test on the oldest
  OS and Okta Verify build in your fleet. For a multi-platform check, make sure the query is
  valid on every listed platform.
- **`LIKE` is case-insensitive and `%` matches anything**, so `LIKE '%x%'` over-matches. Prefer
  `=` for exact values such as bundle identifiers, and escape literal `_` and `%` if you need them.
- **Quote carefully in YAML.** The query goes in a `|` block scalar. Keep the SQL's own quotes as
  single quotes, and let `new --query-file` write the file rather than hand-editing indentation.
- **`validate` is structural only.** It cannot catch invalid SQL, a missing table, a slow query,
  or inverted logic. `osqueryi` testing on a clean and an affected machine is the real check.
- **Uninstall residue causes false positives.** Removing an app often leaves config directories
  behind. Test after a normal uninstall, and decide whether leftovers alone should still trip the
  check (usually they should not; raise the threshold or drop that indicator).
- **Substring matching on process names over-matches.** `name LIKE '%agent%'` hits unrelated
  software. Use exact names where you can, and exclude system locations such as `/System/%` and
  `/Library/%` paths, or `com.apple.%` bundle IDs.
- **Include a port check for tools that run servers.** A listening port catches a network-exposed
  or renamed instance that file and app checks miss.
- **Track renames and migrations.** If a tool changed names or config directories between
  versions, include the old paths too, or older installs slip through.
- **Pick the threshold per tool.** `> 1` is a reasonable default. A tool with few detectable
  artifacts (say two) is easy to miss at `> 1` and easy to over-trigger at `> 0`; one with many
  can tolerate a higher bar. Tune it against real fleet data.
- **Not verified here:** Okta's limits on query runtime or result size, which the Okta article
  above does not cover either. Check Okta's documentation for current limits before deploying
  anything heavy.

### Rolling out safely

Per Okta's guidance, don't go straight to enforcement:

1. Validate each query locally with `osqueryi` on a clean machine and an affected one.
2. Attach the check to a device assurance policy in report-only/monitoring mode first.
3. Review the hit rate on a representative sample of your fleet. Confirm the positives are real
   installs and not uninstall leftovers.
4. Only then switch the policy to enforcement, so developers are not locked out by false positives
   and your help desk is not flooded.

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

**Required OAuth scope** (`OKTA_CLIENT_SCOPES`): `okta.devicePostureChecks.read`. A `401`/`403` usually means the scope was not granted to the OAuth app.

## Output

JSON to stdout. `list` and `list-defaults` return arrays of device posture check objects; `get` returns a single check. Errors are JSON with an `error` key on stderr; exit code 1.

## Notes

A device posture check is an osquery query that Okta Verify runs on the device (macOS or Windows for custom checks). Device assurance policies reference a check by its `variableName` (shown on the assurance policy as `devicePostureChecks.include[]`, behavior observed live, not in the spec) and require its result. The posture-check objects themselves contain no EDR/MDM integration settings — those live in `okta-device-integrations` and in a device assurance policy's `thirdPartySignalProviders`.

## Output Schema

| Field | Type | Description |
|---|---|---|
| `id` | string | Device posture check ID (e.g. `dpc1ab2cd3EF4GH5IJ6K`). Observed absent on `BUILTIN` checks from `list-defaults` |
| `name` | string | Display name (for `BUILTIN` checks this is an i18n key such as `device_assurance.remediation.android.upgrade_os_version.display.name`) |
| `description` | string | What the check does |
| `variableName` | string | Unique name of the check; the key a device assurance policy uses to reference it |
| `platform` | string | `MACOS` or `WINDOWS` per the spec. `list-defaults` was also observed returning `ANDROID`, `CHROMEOS`, `IOS`, `MACOS` and `WINDOWS` for built-in checks |
| `type` | string | `BUILTIN` (Okta-defined) or `CUSTOM` (org-authored osquery) |
| `mappingType` | string | `CHECKBOX` or `TEXTBOX` — how the check is rendered in device assurance policies (per-value semantics unverified) |
| `query` | string | The osquery SQL. Empty string on `BUILTIN` checks |
| `remediationSettings.message.customText` / `.defaultI18nKey` | string | Remediation text shown to the end user on failure (`defaultI18nKey` only applies to `BUILTIN`) |
| `remediationSettings.link.customUrl` / `.defaultUrl` | string | Remediation link shown to the end user (`defaultUrl` only applies to `BUILTIN`) |
| `createdDate` / `lastUpdate` (live `list` returns `lastUpdated`) | ISO 8601 string | When the check was created / last modified |
| `createdBy` / `lastUpdatedBy` | string | ID of the user who created / last modified the check |
| `_links.self.href` | string | Self link |

There is no `status` field: a posture check cannot be deactivated, only deleted.

### osquery_check.py output

`new` and `validate` are local-only — nothing here corresponds to an Okta API object.

| Command | Field | Type | Description |
|---|---|---|---|
| `new` | `written` | string | Path the check YAML was written to |
| `new` | `id` | string | The generated 32-char hex check ID embedded in the YAML |
| `validate` | `valid` | boolean | `true` iff `errors` is empty |
| `validate` | `errors` | array of strings | Structural problems (missing fields, bad platform values) — must be fixed before pasting into the Admin Console |
| `validate` | `warnings` | array of strings | Non-fatal concerns (e.g. query doesn't match either established pattern) — review, don't necessarily block on |

## Interpretation

### Device assurance vs. device posture

| Aspect | Device Assurance | Device Posture |
|---|---|---|
| What it is | The policy: static requirements (OS version, disk encryption, screen lock, third-party signals) | A reusable osquery check a policy can require |
| Signal source | Okta device record / integrations | Query result reported by Okta Verify on the device |
| Referenced by | Access policy rules (`conditions.device.assurance.include[]`) | Device assurance policies (via `variableName`) |

A posture check does nothing until a device assurance policy requires it.

### What to look for

- **`type: CUSTOM` with an empty or trivial `query`**: nothing meaningful is being evaluated.
- **`query` shape**: a good check returns a single row with a 0/1 flag or a non-empty result only when the condition is met — see the query patterns above. Read the SQL before judging the check.
- **`mappingType` mismatch**: a `CHECKBOX` check is expected to return a boolean-style flag; check that the query's output matches how the assurance policy consumes it (exact semantics unverified).
- **Missing `remediationSettings.message.customText`** on a `CUSTOM` check: users denied by it get no explanation of how to fix the device.
- **BUILTIN vs. custom checks**: `list-defaults` returns Okta-authored checks (empty `query`, i18n-key `name`); `list` returns only checks the org authored. If an assurance policy's `devicePostureChecks.include[].variableName` is not in `list`, look in `list-defaults` before assuming it is misconfigured.
- **`validate` warnings on an osquery check**: a non-empty `warnings` array doesn't mean the check is broken — it means the query's shape couldn't be confirmed to match either established pattern (presence or weighted/scored). Read the query yourself before dismissing the warning; `validate` never executes SQL, so it can't tell a genuinely non-conforming query from an unusual-but-correct one.

### Cross-skill references

- `variableName` → appears as `devicePostureChecks.include[].variableName` on `okta-device-assurance` policies (observed live; not in the spec); search `okta-device-assurance list` output for it to find which policies require the check, then `okta-policies get-rules` (`conditions.device.assurance.include[]`) for which rules use those policies
- Posture-related authentication failures surface in `okta-logs` as `policy.evaluate_sign_on` events with `outcome.result eq "DENY"`; `outcome.reason` will indicate the device assurance/posture failure
- EDR/MDM signal sources are not posture checks — see `okta-device-integrations` and `thirdPartySignalProviders` on `okta-device-assurance` policies
