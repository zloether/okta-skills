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
│   ├── okta-logs/
│   └── okta-filters/              # SCIM filter/search syntax reference (no script)
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
| `OKTA_CLIENT_CABUNDLE` | No | Path to a CA bundle file or directory; use when behind a corporate proxy with a custom root CA. Takes precedence over `REQUESTS_CA_BUNDLE`. |
| `REQUESTS_CA_BUNDLE` | No | Standard `requests` library CA bundle variable; used as a fallback if `OKTA_CLIENT_CABUNDLE` is not set |

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

Clone the repo, then run the install script to create symlinks in your AI agent skill directories.

**macOS / Linux**

```bash
git clone https://github.com/zloether/okta-skills.git
cd okta-skills

# Install globally (all agents, current user)
bash install.sh --global

# Install into a specific project
bash install.sh --local /path/to/your/project

# Install for specific agents only
bash install.sh --global --claude --cursor
```

**Windows (PowerShell)**

> Requires Administrator privileges or Developer Mode (Settings → System → For developers).

```powershell
git clone https://github.com/zloether/okta-skills.git
cd okta-skills

# Install globally (all agents)
.\install.ps1 -Global

# Install into a specific project
.\install.ps1 -Local C:\path\to\your\project

# Install for specific agents only
.\install.ps1 -Global -Claude -Cursor
```

Available agent flags: `--claude`, `--cursor`, `--windsurf`, `--copilot`, `--gemini` (shell) / `-Claude`, `-Cursor`, `-Windsurf`, `-Copilot`, `-Gemini` (PowerShell). If none are specified, all agents are installed.

The scripts create symlinks for Claude Code, Cursor, Windsurf, GitHub Copilot, and Gemini. Updates to the repo are picked up automatically — no reinstall needed.

**Python dependencies**

The install script automatically sets up the Python runtime. If uv is already installed it will be detected and used; otherwise a `.venv` is created in the repo with the required packages.

To install uv manually (preferred):
```bash
# macOS
brew install uv          # if Homebrew is available
# or
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
winget install astral-sh.uv
```

Without uv, install dependencies into your Python environment directly:
```bash
pip install -r requirements.txt
```
`PyJWT` and `cryptography` are only needed for OAuth 2.0 / PrivateKey authentication.

## Usage

### Setting environment variables

The scripts read credentials from environment variables at runtime. These variables must be present in the shell environment **before you start your AI agent** — the agent does not and should not manage credentials itself.

**Option 1 — Add to your shell profile** (permanent, applies to all sessions):

```bash
# ~/.zshrc or ~/.bashrc
export OKTA_CLIENT_ORGURL=https://example.okta.com
export OKTA_CLIENT_TOKEN=your-api-token
```

**Option 2 — Source before launching** (per-session):

```bash
source /path/to/your/okta-env.sh
claude  # or cursor, etc.
```

**Option 3 — Set inline from within Claude Code** (using the `!` prefix to run in your shell):

```
! export OKTA_CLIENT_ORGURL=https://example.okta.com
! export OKTA_CLIENT_TOKEN=your-api-token
```

**Option 4 — Use a secrets manager at launch** (e.g. 1Password CLI):

```bash
op run --env-file=.okta.env -- claude
```

`environment.sh` in this repo is a template listing all supported variables — copy it, fill in your values, and source it using one of the methods above. Never commit a file containing real credentials.

### Asking your agent

Once your environment is set, ask your AI agent to use the Okta skills naturally. No special syntax required — just describe what you want.

**Users & accounts**
> "Who is john.doe@example.com and when did they last log in?"
> "Is jane@example.com's account active or suspended?"
> "Find all users whose accounts are currently locked out."
> "Show me the profile for the user with ID 00u1ab2cd3ef."

**Groups & access**
> "Which users are in the Admins group?"
> "What groups does bob@example.com belong to?"
> "Which apps does the Sales group have access to?"

**Applications**
> "Who has access to Salesforce?"
> "Show me all users and groups assigned to the GitHub app."
> "List all active application integrations in the org."

**Security investigations**
> "Show me all login failures for jane@example.com in the last 24 hours."
> "Were there any MFA factor enrollment events this week?"
> "Show me all admin actions taken in the last hour."
> "Did anyone access the org from an unexpected location yesterday?"

**Devices**
> "What devices does alice@example.com have enrolled?"
> "Show me all managed Windows devices in the org."
> "Which users are registered to device ID abc123?"

**Device compliance**
> "What device assurance policies require disk encryption?"
> "Show me all device posture checks and what signals they evaluate."
> "Which device assurance policy applies to macOS users?"

**Policies & network**
> "What MFA methods are required by our sign-on policies?"
> "What are the password requirements for the Default Policy?"
> "What IP ranges are defined in our trusted network zones?"
> "Are there any blocked IP ranges configured in Okta?"

Each `SKILL.md` describes the available subcommands and options. See [AGENTS.md](./AGENTS.md) for the full invocation reference.

## Security

To report a security vulnerability, please use [GitHub's private vulnerability reporting](https://github.com/zloether/okta-skills/security/advisories/new) rather than opening a public issue.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```
