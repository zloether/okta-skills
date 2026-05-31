# Contributing

## Development setup

1. Clone the repo
2. Install dev dependencies: `pip install -r requirements-dev.txt`
3. Copy `environment.sh` (or `environment.ps1`) to `environment.local.sh` (or `environment.local.ps1`), fill in your Okta credentials, and source it before running scripts

## Running tests

```bash
pytest tests/ -v
ruff check .
```

Tests mock the Okta API — no live credentials required.

## Okta API reference

Before writing or modifying any skill, fetch a fresh copy of the Okta OpenAPI spec:

```bash
curl -sSL https://raw.githubusercontent.com/okta/okta-management-openapi-spec/refs/heads/master/dist/current/management-minimal.yaml -o management-minimal.yaml
```

Do not guess endpoint paths, parameters, or response shapes — verify against the spec.

## Adding a skill

Each skill lives under `skills/<name>/` and contains:

- `SKILL.md` — skill metadata, subcommand reference, output schema, and interpretation guidance
- `scripts/<name>.py` — the executable script

Scripts use `shared/okta_client.py` for authentication and pagination. Follow the existing `list` / `get` / `search` / `get-<relation>` subcommand pattern. All operations must be read-only.

When adding a skill, update `AGENTS.md` (skill inventory table) and `README.md` (example queries section).

## Pull requests

- Ensure `pytest tests/ -v` and `ruff check .` both pass before opening a PR
- Include tests for new subcommands
- Update `SKILL.md` with output schema and interpretation guidance for any new or changed response fields
