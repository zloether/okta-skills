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

Before writing or modifying any skill, refresh the local copies of the Okta OpenAPI specs (gitignored, repo root):

```bash
python scripts/update-specs.py
```

This downloads the Management API spec and the Okta for AI Agents (`workload-principals`) spec; see `AGENTS.md` for sources. To see which GET operations no skill implements yet, run `uv run --with pyyaml scripts/diff-spec-coverage.py`.

Do not guess endpoint paths, parameters, or response shapes — verify against the spec.

## Adding a skill

Each skill lives under `skills/<name>/` and contains:

- `SKILL.md` — skill metadata, subcommand reference, output schema, and interpretation guidance
- `scripts/<name>.py` — the executable script (omit for documentation-only skills; see `okta-filters` for an example)

Scripts use `shared/okta_client.py` for authentication, pagination (`paginated_get`), and single-resource fetches (`get_resource`), and `shared/cli.py` (`run`) for argument dispatch, JSON output, error reporting, and the global `--select`/`--strip-links` flags — do not add your own `print(json.dumps(...))`/error handling. Follow the existing `list` / `get` / `search` / `get-<relation>` / `list-<relation>` subcommand pattern. All operations must be read-only.

When adding a skill, update `AGENTS.md` (skill inventory table and repository structure) and `README.md` (repository layout).

## Pull requests

- Ensure `pytest tests/ -v` and `ruff check .` both pass before opening a PR
- Include tests for new subcommands
- Update `SKILL.md` with output schema and interpretation guidance for any new or changed response fields
