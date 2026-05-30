# okta-skills

AI agent skills for reading data from the Okta API. Provides read-only access to core Okta resources and is intended as a functional replacement for the Okta MCP server.

## Repository Layout

```
okta-skills/
├── skills/                        # Agent skill definitions (agentskills.io format)
│   ├── okta-users/
│   │   ├── SKILL.md               # Skill metadata and usage instructions
│   │   └── scripts/users.py       # Executable script
│   ├── okta-groups/
│   ├── okta-apps/
│   ├── okta-policies/
│   ├── okta-devices/
│   ├── okta-network-zones/
│   ├── okta-device-assurance/
│   ├── okta-device-posture/
│   └── okta-logs/
├── shared/
│   └── okta_client.py             # Shared HTTP session, auth, and pagination
├── tests/
├── requirements.txt
└── AGENTS.md                      # Full API reference and invocation guide
```

## Environment Variables

`OKTA_CLIENT_ORGURL` is always required.

### Common

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_ORGURL` | Yes | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_AUTHORIZATIONMODE` | No | `PrivateKey` or `SSWS`. If unset, PrivateKey is preferred when both sets of credentials are present. |
| `OKTA_CLIENT_USERAGENT` | No | Replaces the default `User-Agent` header |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | No | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | No | Request/read timeout in seconds (default: 30) |

### SSWS (API Token)

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_TOKEN` | Yes | Okta API token |

### OAuth 2.0 Private Key JWT

| Variable | Required | Description |
|---|---|---|
| `OKTA_CLIENT_CLIENTID` | Yes | OAuth 2.0 service app client ID |
| `OKTA_CLIENT_PRIVATEKEY` | Yes | Private key as a PEM string, JWK JSON string, or path to a PEM/JWK file |
| `OKTA_CLIENT_SCOPES` | Yes | Space-separated OAuth scopes, e.g. `okta.users.read okta.groups.read` |
| `OKTA_CLIENT_TOKEN_CACHE_PATH` | No | File path for caching the access token between invocations |

## Installation

```bash
pip install -r requirements.txt
```

`PyJWT` and `cryptography` are only required for OAuth 2.0 / PrivateKey authentication.

## Usage

Set the required environment variables, then invoke any skill script directly or let your AI agent call it based on natural language input. Each `SKILL.md` describes the available subcommands and options. See [AGENTS.md](./AGENTS.md) for the full invocation reference.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```
