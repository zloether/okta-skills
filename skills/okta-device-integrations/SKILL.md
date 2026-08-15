---
name: okta-device-integrations
description: Read Okta device integrations — the connectors that feed device trust/posture signals into Okta, such as CrowdStrike, Windows Security Center, Chrome Device Trust, OSQuery, and Android Device Trust. Use when asked which device integrations are configured, whether one is active, or which IdP/service account backs a given integration.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. Both `list` and `get` are Limited GA (`isGenerallyAvailable: false`).
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-device-integrations/scripts/device_integrations.py <command> [options]
```

### list / get
List all device integrations, or get one by ID. ⚠️ Limited GA.
```bash
uv run skills/okta-device-integrations/scripts/device_integrations.py list
uv run skills/okta-device-integrations/scripts/device_integrations.py get din9lzd33mvS9kjr60g4
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

### Device integration object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the integration — use with `get` |
| `name` | string | Namespace identifying the integration type, e.g. `com.crowdstrike.zta`, `com.google.dtc`, `com.okta.deviceidp`, `com.okta.device.osquery`, `com.okta.windowssecuritycenter`, `com.android.zero.trust`, `com.okta.workspaceone` |
| `displayName` | string | Human-readable name shown in the Admin Console |
| `status` | string | `ACTIVE` or `DEACTIVATED` |
| `platform` | string | `ANDROID`, `CHROMEOS`, `IOS`, `MACOS`, or `WINDOWS` |
| `metadata` | object | Present for some integration types — shape depends on `metadata.type` (see below) |
| `_links.self.href` | string | Link to this integration |
| `_links.activate.href` | string | Present only when `status` is `DEACTIVATED` |
| `_links.deactivate.href` | string | Present only when `status` is `ACTIVE` |

### `metadata` by type

| `metadata.type` | Used by | Fields |
|---|---|---|
| `CHROME` | Chrome Device Trust (`com.google.dtc`) | `serviceAccountName`, `serviceAccountEmail` — the GCP service account Okta uses to verify device signals |
| `DEVICE_IDP` | Device Posture Provider integrations (`com.okta.deviceidp`) | `idpId` — the identity provider this device posture signal is tied to |
| `WORKSPACE_ONE` | Workspace ONE (`com.okta.workspaceone`) | `provider`, `enrollmentUrl`, `idpId` |

Integrations that don't require external configuration (e.g. OSQuery, Windows Security Center, Android Device Trust) omit `metadata` entirely.

## Interpretation

### What to look for

- **`status: DEACTIVATED`**: the integration is configured but not currently producing device trust signals — any policy condition relying on it (device posture, device assurance) sees no signal from this source until reactivated. The presence of an `activate` link (vs. `deactivate`) is the reliable way to confirm this, since `status` and links are always kept in sync.
- **`metadata.idpId` on a `DEVICE_IDP` integration**: cross-reference against `okta-identity-providers get <idpId>` to confirm the linked IdP itself is active — a deactivated or misconfigured IdP silently breaks this integration even if its own `status` shows `ACTIVE`.
- **Duplicate integrations for the same `platform`**: e.g. both `com.okta.deviceidp` and `com.okta.windowssecuritycenter` active for `WINDOWS` — check which one actually backs the device assurance/posture policies in use, since overlapping sources can produce conflicting signals.

### Cross-skill references

- `metadata.idpId` → `okta-identity-providers get <idpId>` for the linked IdP's configuration and status
- Device trust/posture signals produced by these integrations are consumed by `okta-device-assurance` and `okta-device-posture` policy conditions — an integration being `DEACTIVATED` here explains a posture/assurance check that's silently never satisfied
- Enrolled devices themselves (independent of which integration reported them) are in `okta-devices`
