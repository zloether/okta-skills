# okta-skills

AI agent skills for reading data from the Okta API. These skills provide read-only access to Okta resources and are intended as a functional replacement for the Okta MCP server.

## Important: API Spec

Do not guess or assume how the Okta API works. Always verify endpoint paths, HTTP methods, query parameters, and response schemas against the official OpenAPI spec before writing or modifying any code:

**Spec URL:** https://raw.githubusercontent.com/okta/okta-management-openapi-spec/refs/heads/master/dist/current/management-minimal.yaml

A local copy (`management-minimal.yaml`) may exist in the repo root for quick reference, but it is gitignored and may be stale. Before starting any work, fetch a fresh copy from the URL above and save it to `management-minimal.yaml`:

```bash
curl -sSL https://raw.githubusercontent.com/okta/okta-management-openapi-spec/refs/heads/master/dist/current/management-minimal.yaml -o management-minimal.yaml
```

## Repository Structure

```
okta-skills/
├── skills/                        # Agent skill definitions (agentskills.io format)
│   ├── okta-users/
│   │   ├── SKILL.md               # Skill metadata and instructions
│   │   └── scripts/users.py       # Executable script
│   ├── okta-groups/
│   ├── okta-apps/
│   ├── okta-policies/
│   ├── okta-devices/
│   ├── okta-network-zones/
│   ├── okta-device-assurance/
│   ├── okta-device-posture/
│   ├── okta-logs/
│   ├── okta-api-tokens/
│   ├── okta-sessions/
│   └── okta-filters/              # SCIM filter/search syntax reference (no script)
├── shared/
│   └── okta_client.py             # Shared HTTP session and pagination logic
├── tests/
│   └── conftest.py
├── requirements.txt
└── AGENTS.md
```

## Invoking Scripts

Prefer `uv run` when uv is available — it manages dependencies automatically with no venv activation required. Fall back to plain `python` otherwise (requires dependencies installed in the active environment or repo `.venv`).

```bash
# Preferred
uv run skills/okta-users/scripts/users.py get user@example.com
uv run skills/okta-logs/scripts/logs.py login-failures --user user@example.com

# Fallback
python skills/okta-users/scripts/users.py get user@example.com
python skills/okta-logs/scripts/logs.py login-failures --user user@example.com
```

Do not source credential files or attempt to inject environment variables at invocation time — credentials must already be present in the shell environment before the agent session starts. This is the user's responsibility, not the agent's.

If a script exits with an auth error (`OKTA_CLIENT_ORGURL is not set`, `OKTA_CLIENT_TOKEN is required`, etc.), do not attempt to fix it by sourcing files or constructing credential strings. Instead, tell the user which environment variables are missing and ask them to set them — they can use `! export VAR=value` in Claude Code to set variables in their shell without leaving the session.

## Environment Variables

`OKTA_CLIENT_ORGURL` is always required. Auth method is determined by `OKTA_CLIENT_AUTHORIZATIONMODE` if set; otherwise auto-detected (PrivateKey preferred if both sets of credentials are present).

### Common

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_ORGURL` | Yes | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_AUTHORIZATIONMODE` | No | `PrivateKey` or `SSWS`. If unset, PrivateKey is used when client ID + key are present, otherwise SSWS. |
| `OKTA_CLIENT_USERAGENT` | No | Replaces the default `User-Agent` header |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | No | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | No | Request/read timeout in seconds (default: 30) |
| `OKTA_CLIENT_CABUNDLE` | No | Path to a CA bundle file or directory; use when behind a corporate proxy with a custom root CA. Takes precedence over `REQUESTS_CA_BUNDLE`. |
| `REQUESTS_CA_BUNDLE` | No | Standard `requests` library CA bundle variable; used as a fallback if `OKTA_CLIENT_CABUNDLE` is not set |

### SSWS (API Token) Auth

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_TOKEN` | Yes | Okta API token (SSWS token) |

### PrivateKey (OAuth 2.0) Auth

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_CLIENTID` | Yes | OAuth 2.0 service app client ID |
| `OKTA_CLIENT_PRIVATEKEY` | Yes | Private key as a PEM string, JWK JSON string, or path to a PEM/JWK file |
| `OKTA_CLIENT_SCOPES` | Yes | Space-separated OAuth scopes, e.g. `okta.users.read okta.groups.read` |
| `OKTA_CLIENT_TOKEN_CACHE_PATH` | No | File path for caching the access token between invocations. If unset, a fresh token is fetched on every run. |

PrivateKey auth requires `PyJWT>=2.0` and `cryptography>=41.0` to be installed. Supported key types: RSA (RS256) and EC (ES256).

## Skill Inventory

| Skill | Directory | API Endpoint | Description |
|---|---|---|---|
| okta-users | `skills/okta-users/` | `/api/v1/users` | User profiles, status, attributes |
| okta-groups | `skills/okta-groups/` | `/api/v1/groups` | Groups and group memberships |
| okta-apps | `skills/okta-apps/` | `/api/v1/apps` | Application integrations and assignments |
| okta-policies | `skills/okta-policies/` | `/api/v1/policies` | Sign-on, MFA, password, and access policies |
| okta-devices | `skills/okta-devices/` | `/api/v1/devices` | Enrolled device records |
| okta-network-zones | `skills/okta-network-zones/` | `/api/v1/zones` | IP and dynamic network zones |
| okta-device-assurance | `skills/okta-device-assurance/` | `/api/v1/device-assurances` | Device compliance requirement policies |
| okta-device-posture | `skills/okta-device-posture/` | `/api/v1/device-posture-checks` | Real-time device health posture checks |
| okta-logs | `skills/okta-logs/` | `/api/v1/logs` | System log events and audit history |
| okta-api-tokens | `skills/okta-api-tokens/` | `/api/v1/api-tokens` | API token metadata |
| okta-sessions | `skills/okta-sessions/` | `/api/v1/sessions` | Session lookup by ID |
| okta-filters | `skills/okta-filters/` | — | SCIM filter/search syntax reference and skill-selection guide |

## Invoking Scripts

Each script accepts a subcommand and options. All output is JSON on stdout. Errors are JSON with an `error` key on stderr with exit code 1.

```bash
# Users
uv run skills/okta-users/scripts/users.py list
uv run skills/okta-users/scripts/users.py list --filter 'status eq "ACTIVE"'
uv run skills/okta-users/scripts/users.py get user@example.com
uv run skills/okta-users/scripts/users.py search "Jane Smith"
uv run skills/okta-users/scripts/users.py get-apps user@example.com
uv run skills/okta-users/scripts/users.py get-blocks user@example.com
uv run skills/okta-users/scripts/users.py get-groups user@example.com
uv run skills/okta-users/scripts/users.py get-idps user@example.com
uv run skills/okta-users/scripts/users.py get-linked-objects user@example.com manager
uv run skills/okta-users/scripts/users.py get-enrollments <userId>
uv run skills/okta-users/scripts/users.py get-classification <userId>
uv run skills/okta-users/scripts/users.py get-clients user@example.com
uv run skills/okta-users/scripts/users.py get-client-grants user@example.com <clientId>
uv run skills/okta-users/scripts/users.py get-client-tokens user@example.com <clientId>
uv run skills/okta-users/scripts/users.py get-client-token user@example.com <clientId> <tokenId>
uv run skills/okta-users/scripts/users.py get-devices <userId>
uv run skills/okta-users/scripts/users.py get-factors user@example.com
uv run skills/okta-users/scripts/users.py get-grants user@example.com
uv run skills/okta-users/scripts/users.py get-grant user@example.com <grantId>
uv run skills/okta-users/scripts/users.py get-risk <userId>
uv run skills/okta-users/scripts/users.py get-roles user@example.com
uv run skills/okta-users/scripts/users.py get-role user@example.com <roleAssignmentId>
uv run skills/okta-users/scripts/users.py get-subscriptions <userId>
uv run skills/okta-users/scripts/users.py get-subscription <userId> <notificationType>

# Groups
uv run skills/okta-groups/scripts/groups.py list
uv run skills/okta-groups/scripts/groups.py get <group_id>
uv run skills/okta-groups/scripts/groups.py get-members <group_id>
uv run skills/okta-groups/scripts/groups.py get-apps <group_id>
uv run skills/okta-groups/scripts/groups.py get-owners <group_id>
uv run skills/okta-groups/scripts/groups.py search "Admins"
uv run skills/okta-groups/scripts/groups.py list-rules
uv run skills/okta-groups/scripts/groups.py list-rules --search "Engineering"
uv run skills/okta-groups/scripts/groups.py get-rule <rule_id>
uv run skills/okta-groups/scripts/groups.py list-roles <group_id>
uv run skills/okta-groups/scripts/groups.py get-role <group_id> <role_assignment_id>
uv run skills/okta-groups/scripts/groups.py list-role-app-targets <group_id> <role_assignment_id>
uv run skills/okta-groups/scripts/groups.py list-role-group-targets <group_id> <role_assignment_id>

# Apps
uv run skills/okta-apps/scripts/apps.py list
uv run skills/okta-apps/scripts/apps.py get <app_id>
uv run skills/okta-apps/scripts/apps.py get-users <app_id>
uv run skills/okta-apps/scripts/apps.py get-user <app_id> <user_id>
uv run skills/okta-apps/scripts/apps.py get-groups <app_id>
uv run skills/okta-apps/scripts/apps.py get-group <app_id> <group_id>
uv run skills/okta-apps/scripts/apps.py get-connection <app_id>
uv run skills/okta-apps/scripts/apps.py get-connection-jwks <app_id>
uv run skills/okta-apps/scripts/apps.py list-csrs <app_id>
uv run skills/okta-apps/scripts/apps.py get-csr <app_id> <csr_id>
uv run skills/okta-apps/scripts/apps.py list-jwks <app_id>
uv run skills/okta-apps/scripts/apps.py get-jwk <app_id> <key_id>
uv run skills/okta-apps/scripts/apps.py list-keys <app_id>
uv run skills/okta-apps/scripts/apps.py get-key <app_id> <key_id>
uv run skills/okta-apps/scripts/apps.py list-secrets <app_id>
uv run skills/okta-apps/scripts/apps.py get-secret <app_id> <secret_id>
uv run skills/okta-apps/scripts/apps.py list-cwo-connections <app_id>
uv run skills/okta-apps/scripts/apps.py get-cwo-connection <app_id> <connection_id>
uv run skills/okta-apps/scripts/apps.py list-features <app_id>
uv run skills/okta-apps/scripts/apps.py get-feature <app_id> <feature_name>
uv run skills/okta-apps/scripts/apps.py list-federated-claims <app_id>
uv run skills/okta-apps/scripts/apps.py get-federated-claim <app_id> <claim_id>
uv run skills/okta-apps/scripts/apps.py list-grants <app_id>
uv run skills/okta-apps/scripts/apps.py get-grant <app_id> <grant_id>
uv run skills/okta-apps/scripts/apps.py list-group-push-mappings <app_id>
uv run skills/okta-apps/scripts/apps.py get-group-push-mapping <app_id> <mapping_id>
uv run skills/okta-apps/scripts/apps.py list-interclient-allowed-apps <app_id>
uv run skills/okta-apps/scripts/apps.py list-interclient-target-apps <app_id>
uv run skills/okta-apps/scripts/apps.py get-saml-metadata <app_id> --kid <key_id>
uv run skills/okta-apps/scripts/apps.py list-tokens <app_id>
uv run skills/okta-apps/scripts/apps.py get-token <app_id> <token_id>

# Policies
uv run skills/okta-policies/scripts/policies.py list
uv run skills/okta-policies/scripts/policies.py list --type OKTA_SIGN_ON
uv run skills/okta-policies/scripts/policies.py get <policy_id>
uv run skills/okta-policies/scripts/policies.py get-rules <policy_id>
uv run skills/okta-policies/scripts/policies.py get-rule <policy_id> <rule_id>
uv run skills/okta-policies/scripts/policies.py list-mappings <policy_id>
uv run skills/okta-policies/scripts/policies.py get-mapping <policy_id> <mapping_id>

# Devices
uv run skills/okta-devices/scripts/devices.py list
uv run skills/okta-devices/scripts/devices.py get <device_id>
uv run skills/okta-devices/scripts/devices.py get-users <device_id>

# Network Zones
uv run skills/okta-network-zones/scripts/network_zones.py list
uv run skills/okta-network-zones/scripts/network_zones.py get <zone_id>

# Device Assurance
uv run skills/okta-device-assurance/scripts/device_assurance.py list
uv run skills/okta-device-assurance/scripts/device_assurance.py get <policy_id>

# Device Posture
uv run skills/okta-device-posture/scripts/device_posture.py list
uv run skills/okta-device-posture/scripts/device_posture.py get <check_id>
uv run skills/okta-device-posture/scripts/device_posture.py list-defaults

# Logs
python skills/okta-logs/scripts/logs.py list
python skills/okta-logs/scripts/logs.py list --since 2024-01-01T00:00:00Z
python skills/okta-logs/scripts/logs.py list --filter 'eventType eq "user.session.start"' --limit 100
python skills/okta-logs/scripts/logs.py login-failures
python skills/okta-logs/scripts/logs.py login-failures --user user@example.com
python skills/okta-logs/scripts/logs.py list --filter 'outcome.result eq "FAILURE"'

# API Tokens
uv run skills/okta-api-tokens/scripts/api_tokens.py list
uv run skills/okta-api-tokens/scripts/api_tokens.py get <token_id>

# Sessions
uv run skills/okta-sessions/scripts/sessions.py get <session_id>
```

## Shared Library

`shared/okta_client.py` provides two functions used by all scripts:

- `get_session()` — returns a configured `(session, base_url)` tuple using environment variables
- `paginated_get(session, url, params, limit)` — follows Okta's `Link` header pagination and returns a complete list

Do not invoke `okta_client.py` directly. It is imported by each script via a `sys.path` insert pointing to the `shared/` directory.

## Conventions

- All operations are read-only. No write, update, or delete operations exist.
- Scripts follow the `list`, `get`, `search`, `get-<relation>` subcommand pattern.
- Pagination is handled automatically; results are always returned as a complete JSON array.
- Date/time parameters use ISO 8601 format: `2024-01-01T00:00:00Z`.
- Filter expressions use Okta's SCIM filter syntax where supported.

## Knowledge Base

Each skill's `SKILL.md` is the authoritative source for interpreting the data that skill returns. Because skills can be installed and invoked from any project, all interpretation guidance must live inside the skill itself — do not rely on any external file being present.

When adding or updating a skill, include the following in its `SKILL.md`:

- **Output Schema** — key fields an agent needs to understand the response, including nested fields, enum values, and what each means in plain terms
- **Interpretation** — how to read the data: what field combinations indicate a particular state, what values are actionable, what is normal vs. noteworthy
- **Cross-skill references** — when a field in this skill's output (e.g. `actor.id` in a log event) can be used as input to another skill (e.g. `okta-users get`), say so explicitly

Keep this guidance agent-facing: write it so an agent that has just received a JSON response can understand what it's looking at and what to do next.
