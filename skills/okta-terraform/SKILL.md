---
name: okta-terraform
description: Write and edit Terraform configuration for Okta resources using the official okta/okta provider, and find Okta resources that exist in the org but aren't yet managed in Terraform so they can be imported. Use when asked to define Okta resources as Terraform, change existing .tf files to match a described change, or reconcile a Terraform project against the live org.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.11+ and uv (preferred) or the requests library — the discovery script shells out to other skills' scripts, which need the same environment they normally do. Requires the Terraform CLI (>=1.5, for `import` blocks) on PATH for validation and discovery. Requires OKTA_CLIENT_ORGURL and auth environment variables (see AGENTS.md) for any workflow that reads live Okta resources.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

## Scope and boundaries

- This skill authors and edits Terraform configuration. Unlike every other skill in this repo, its job is to produce files that describe infrastructure, not just read live data.
- **It never runs `terraform apply`, `terraform import`, `terraform destroy`, or any state-mutating `terraform state` subcommand (`mv`, `rm`, ...) — under any circumstance, even if the user asks for it directly.** It generates `resource` blocks and `import` blocks (Terraform ≥1.5 syntax) for a human to review. Actually applying a change or importing a resource into state is the user's explicit action, run by them outside this skill.
- **Never run the raw `terraform` binary via Bash.** Always go through `scripts/safe_terraform.py`, which mirrors the real CLI's arguments but refuses anything outside `plan`, `validate`, `fmt`, `show`, `init`, and `state list`/`state show`:
  ```bash
  uv run skills/okta-terraform/scripts/safe_terraform.py plan -chdir=path/to/dir
  uv run skills/okta-terraform/scripts/safe_terraform.py validate -chdir=path/to/dir
  ```
  This is a guardrail against a misread instruction or a prompt injection embedded in a `.tf` file or `README` read mid-task reaching a mutating command through this skill's own tooling — not a hard sandbox, since Bash itself is otherwise unrestricted for this skill (see `compatibility`/`allowed-tools` above).
- Never write real credentials or secrets into `.tf` files as literals. Reference them via variables (`var.x`) or environment-backed inputs.

## Workflow 0: Set up a new multi-state project layout

Okta doesn't publish a recommended Terraform repo layout. Left to a single flat directory, a project ends up with one monolithic state where every `plan`/`apply` walks every resource type together — slow, and Okta's API enforces separate rate-limit buckets per endpoint, so a large `okta_app`/`okta_group` population can make an unrelated `okta_network_zone` change take far longer than it should (see developer.okta.com/docs/reference/rate-limits/ for how Okta buckets these). The fix is splitting the project into several independent Terraform states along resource-type boundaries, plus a prod/non-prod split and count-balanced sharding for the two highest-cardinality types (apps, groups).

Use this workflow when a request is about the project's *structure* — "help me set up a Terraform repo for Okta," "how should I organize this," "review our layout," "our apply is too slow/hitting rate limits" — not when the request is to write or edit a specific resource (that's Workflow 3/4 below).

0. If a Terraform project already exists, audit it before proposing anything new — don't assume it needs restructuring, and don't jump straight to `init`:
   ```bash
   uv run skills/okta-terraform/scripts/scaffold_project.py review --dir path/to/project
   ```
   `review` inspects every `.tf`-containing directory (read-only, via `locate_root_module.py` — it never runs `terraform init`/`plan`) and flags, per state: isolation-group mixing (`blast-radius`), a high-cardinality type over the shard threshold (`efficiency`), and a missing remote backend or a single state holding every app with no prod/non-prod split (`testing`). Use `findings` to decide which of steps 1-3 below actually apply to *this* project — a well-organized layout may need none of them. `review` never migrates anything: splitting a flagged state means creating new sibling directories (step 3) and moving the affected resource blocks plus running `terraform state mv` by hand — this skill never runs `terraform state mv` itself.
1. See the recommended isolation groups (no API calls, just registry metadata):
   ```bash
   uv run skills/okta-terraform/scripts/scaffold_project.py list-groups
   ```
   Each entry is a resource-type cluster (e.g. `network_zones`, `auth_policies`, `identity_providers`) with a `rationale` for why it gets its own state. Apps and groups aren't in this list — they're handled separately in the next step because of their cardinality.
2. For apps and groups, get an org-specific shard recommendation instead of guessing letter ranges (name clustering, e.g. many vendor names starting with the same letter, makes fixed A-F/G-M splits uneven in practice):
   ```bash
   uv run skills/okta-terraform/scripts/scaffold_project.py recommend-groups --max-per-shard 60
   uv run skills/okta-terraform/scripts/scaffold_project.py recommend-apps --max-per-shard 60
   ```
   Okta has no built-in prod/non-prod field on apps, so `recommend-apps` without `--prod-pattern` returns every app unclassified with a note. Ask the user how their org distinguishes prod from non-prod apps (a label suffix/prefix is common, e.g. `prod$`), then re-run with `--prod-pattern` to get a real prod/non-prod split — always keep these in separate states so a provider version upgrade can be tested against non-prod first.
3. Confirm which isolation groups and shard counts the user actually wants (present the recommendation, don't assume every group applies — a small org may not need auth_policies split from device_assurance, for instance), then scaffold the skeleton:
   ```bash
   uv run skills/okta-terraform/scripts/scaffold_project.py init --dir path/to/project \
     --groups network_zones,authenticators,auth_policies \
     --apps-prod --apps-nonprod-shards 3 --group-shards 2
   ```
   This only writes a `versions.tf` (required_providers block, with `TODO` markers for the version pin and remote backend — both org-specific) and a `README.md` (explaining the isolation rationale) per directory. It never runs `terraform init` and never writes real resource blocks — populate each state via Workflow 1/2 once it exists. Existing directories are left untouched (skipped, not overwritten).

## Workflow 2: Help the user discover what's checkable

Some users won't know which Okta settings are even manageable in Terraform, so they won't know what category to name. When a request is this open-ended — "what can you check against Terraform?", "help me find what's not managed yet" with no specific type or object named — don't guess a category and don't run a blanket scan across every registered type. Instead:

1. Run `list-types` (no API calls, just registry metadata):
   ```bash
   uv run skills/okta-terraform/scripts/discover_unmanaged.py list-types
   ```
   It returns three groups: `auto_discoverable` (types `get`/`find` can check directly — each with a short `description` and a `high_cardinality` flag), `manual_only` (categories that are Terraform-manageable but need per-object type-branching handled by hand via Workflow 3/4, each with a `reason`), and `not_terraform_manageable` (Okta concepts with no `okta_*` resource at all, listed so the user isn't left wondering why they're missing).
2. Present the `auto_discoverable` and `manual_only` entries to the user as a multi-select choice (e.g. `AskUserQuestion` if available, otherwise a numbered list they can reply to) so they pick one or more categories themselves. Don't pre-select anything, and call out `high_cardinality` types in the prompt so the user knows those checks are more expensive before they pick them.
3. For each `auto_discoverable` category selected, proceed to Workflow 5 Mode B (`find`) — the user's selection from this menu *is* the explicit ask Mode B requires, so no further confirmation is needed beyond what the menu already disclosed for `high_cardinality` types.
4. For each `manual_only` category selected, explain that discovery isn't automated for it and offer to start Workflow 3/4 by hand (e.g. ask which specific app or policy they want defined).

## Before writing or editing any resource type

### Locate the right root module

Terraform projects are organized in wildly different ways: a single flat directory, per-environment directories (`environments/prod`, `environments/staging`), or a root module that composes reusable child modules from `modules/`. Never assume the first `.tf` file or `main.tf` you find is the right place — a `resource "okta_*"` block can legally live inside a child module that isn't meant to be edited directly, and a repo can have several independent root modules for different environments.

Use `scripts/locate_root_module.py` to rank candidate directories instead of guessing:

```bash
uv run skills/okta-terraform/scripts/locate_root_module.py list-root-modules --dir . --resource-type okta_group
```

This walks every directory containing `.tf` files and ranks them by: whether the directory declares its own `provider "okta" { ... }` block (a root-module signal — child modules normally inherit providers rather than declaring them), whether the directory is referenced as another file's `module "..." { source = "./..." }` target (a child-module signal, ranked lower), and, if `--resource-type` is given, whether that resource type is already defined there.

If more than one plausible root module remains after ranking (e.g. multiple environments, or the resource type doesn't exist yet anywhere), **ask the user** which one this belongs to — don't guess based on whichever directory was found first.

### Pin docs to the applicable provider version

Don't guess the provider's argument names, required/optional fields, or import ID format — the provider changes these between major versions, and the docs on `master` may not match what a project actually has pinned. Once you know the root module, resolve its version:

```bash
uv run skills/okta-terraform/scripts/locate_root_module.py resolve-version --dir path/to/root-module
```

This checks `.terraform.lock.hcl` first (the exact resolved version, no constraint math needed). If there's no lock file but a `required_providers` constraint exists (e.g. `~> 4.0`), it returns that constraint and a note to run `terraform init` there to resolve it — this skill does not reimplement Terraform's version-constraint solving. If neither exists (a brand-new root module with no provider pin yet), it returns a note to check the latest release instead.

Then fetch the doc for the specific resource(s) you're touching, pinned to that resolved version (fall back to `master` only when no version could be resolved):

```bash
curl -sSL https://raw.githubusercontent.com/okta/terraform-provider-okta/v<version>/docs/resources/<resource>.md
```

The `<resource>` filename is the `okta_` resource name with that prefix stripped, e.g. `okta_group_rule` → `group_rule.md`. Read the doc's **Import** section before generating an `import` block — some resources take a bare object ID, others take a composite `a/b` ID.

## Workflow 3: Write new Terraform from a description

1. Identify the Okta resource type(s) the request implies.
2. Locate the right root module and resolve its provider version (see above).
3. Fetch the doc(s) for those resource types, pinned to that version.
4. Read the existing `.tf` files in the target directory (`Glob '*.tf'`, `Read`) to match house conventions: provider block location, variable/locals naming, one-resource-per-file vs. grouped, quoting style.
5. Write the resource block(s), using variables for anything sensitive or environment-specific.
6. If Terraform is installed, run `safe_terraform.py validate` (and `safe_terraform.py fmt`) in that directory to catch syntax errors before handing the result back.

## Workflow 4: Edit existing Terraform to match a described change

1. Locate the relevant resource block(s) with `Grep`/`Read` — if the request doesn't already point at a specific file, use `locate_root_module.py list-root-modules --resource-type <type>` to find which root module actually defines it, especially if the repo has more than one.
2. Resolve that root module's provider version and fetch the current doc for that resource type to confirm the attribute you're changing still has the name/shape you expect.
3. Edit in place with `Edit`, preserving the file's existing formatting and attribute order.
4. Re-run `safe_terraform.py validate`/`safe_terraform.py plan` if available, and report the plan's summary (adds/changes/destroys) back to the user — flag any unexpected destroy.

## Workflow 5: Find and import unmanaged resources

A live Okta resource isn't Terraform-managed just because a read-skill can see it. `scripts/discover_unmanaged.py` has two modes — use the one that matches what was actually asked for. **Never decide on your own to sweep a whole category "while you're at it."** Many object types (users, groups, apps, and more) exist in an org by the hundreds or thousands and are frequently *not* meant to be Terraform-managed by design; listing all of them is an API-heavy operation a human should ask for explicitly, not something this skill infers from a vaguer request like "check what's missing from Terraform."

### Mode A: A specific resource the user already has an ID or URL for

This is the common case — a user names one object ("import this network zone", pastes an admin console URL or an API URL) and wants Terraform for just that one thing. No listing involved:

```bash
uv run skills/okta-terraform/scripts/discover_unmanaged.py get network_zone --id https://example.okta.com/admin/access/network/zone/nzoABC123 --tf-dir path/to/terraform
```

`get` resolves the ID out of a URL if one was given, fetches only that one object via the read-skill's `get` command, and reports whether it's already managed or, if not, its label, `okta_*` resource type, and a ready-to-place `import` block.

### Mode B: A whole category, only when explicitly asked

Only invoke this when the user names a specific category to reconcile (e.g. "find every network zone that isn't in Terraform yet" or "reconcile authenticators against this repo") or selects one from the Workflow 2 menu — not as a default first step, and not for every registered type in sequence:

```bash
uv run skills/okta-terraform/scripts/discover_unmanaged.py find network_zone --tf-dir path/to/terraform
```

`find` runs the corresponding read-skill's `list` command — every live object of that type in the org — reads `terraform show -json` from `--tf-dir` (default: current directory), and returns each live object with no matching managed resource. For high-cardinality types (`user`, `group`), confirm with the user before running `find` even if they named the category, since the result set and API cost can be large; Mode A is almost always the better fit for a handful of specific objects.

Both modes need the okta/okta provider plugin already downloaded to decode `terraform show -json` output — if `--tf-dir` hasn't been `terraform init`-ed yet, the command fails with a "Failed to load plugin schemas" error; run `safe_terraform.py init` there first.

For each unmanaged object returned by either mode:
1. Fetch the resource's doc (pinned to the resolved provider version — see above) and write a matching `resource "okta_x" "name" { ... }` block with arguments read from the live object (use the read-skill's `get` command for full detail).
2. Place the `resource` block and the generated `import` block in the target `.tf` file.
3. Run `safe_terraform.py plan` — a correctly-filled resource block plus its `import` block should plan a clean import with zero changes. Any planned diff means an argument doesn't match the live object; fix it and re-plan.
4. Report the plan output back to the user. Do not run `terraform apply` or `terraform import` yourself — and `safe_terraform.py` refuses to run them for you even if asked.

### Registry coverage

`discover_unmanaged.py`'s registry (`get`/`find`-capable) only covers resource types with a single, non-branching mapping to one `okta_*` resource. Run `list-types` (see Workflow 2) for the authoritative, current list of what's in the registry, what's Terraform-manageable but handled by hand (`manual_only` — apps, policies, device assurance policies, identity providers, schemas/org settings/etc.), and what has no Terraform representation at all (`not_terraform_manageable`) — don't hardcode or re-derive this list elsewhere, since the script is the single source of truth for it.

## Output Schema

All scripts print JSON to stdout; errors are `{"error": "..."}` on stderr with exit code 1.

### discover_unmanaged.py

| Command | Field | Type | Description |
|---|---|---|---|
| `get`/`find` (unmanaged) | `id` | string | Live Okta object ID |
| | `label` | string or null | Human-readable name (null if the live object has no label field populated) |
| | `tf_resource_type` | string | The `okta_*` resource type this object maps to |
| | `import_block` | string | Ready-to-paste Terraform `import { to = ...; id = "..." }` block, Terraform ≥1.5 syntax |
| `get` (already managed) | `already_managed` | `true` | Present only when the object is already in Terraform state; `label`/`import_block` are omitted |
| `list-types` | `auto_discoverable` | object | `get`/`find`-capable types: `tf_resource_type`, `description`, `high_cardinality` |
| | `manual_only` | object | Terraform-manageable but type-branching categories, each with a `reason` |
| | `not_terraform_manageable` | array | Okta concepts with no `okta_*` resource at all |

### locate_root_module.py

| Command | Field | Type | Description |
|---|---|---|---|
| `list-root-modules` | `dir` | string | Candidate root module directory, ranked most-likely first |
| | `has_provider_block` | bool | Declares its own `provider "okta" {}` — a root-module signal |
| | `has_backend_block` | bool | Declares a remote `backend "..." {}` block |
| | `referenced_as_child_module` | bool | Another directory's local `module { source = "./..." }` points here — a child-module signal, ranked lower |
| | `okta_resource_counts` | object | `okta_*` type → count, aggregated recursively through any local child modules this directory composes |
| | `matches_resource_type` | bool or null | Whether `--resource-type` (if given) already appears here |
| `resolve-version` | `source` | string | `lock` (exact, from `.terraform.lock.hcl`), `constraint` (unresolved, from `required_providers`), or `none` |
| | `version` | string or null | Exact resolved version when `source: lock` |
| | `constraint`/`note` | string | Present when `source` isn't `lock` — what to do next (run `safe_terraform.py init`, or check the latest release) |

### scaffold_project.py

| Command | Field | Type | Description |
|---|---|---|---|
| `list-groups` | *(top-level)* | object | Isolation group name → `description`, `resource_types`, `rationale` |
| `recommend-apps`/`recommend-groups` | `total` | int | Live object count |
| | `prod`/`unclassified_shards`/`nonprod_shards`/`shards` | object/array | Depends on whether `--prod-pattern` was given (apps) — see Workflow 0 step 2 |
| `review` | `states_reviewed` | int | Directories treated as independent Terraform states |
| | `total_resource_counts` | object | `okta_*` type → count, summed across all reviewed states |
| | `findings[].category` | string | `blast-radius` (mixed isolation groups in one state), `efficiency` (over the shard threshold), or `testing` (no remote backend / no prod-nonprod split) |
| | `findings[].dir`/`issue`/`recommendation` | string | Which state, what's wrong, and the suggested fix |
| `init` | `created`/`skipped` | array | Isolation-group directories written vs. left alone because they already existed |

## Interpretation

- **`already_managed: true` from `get`**: nothing to do — the object is already tracked. Don't generate an import block for it.
- **A `find` result with many entries of the same `tf_resource_type`**: confirm with the user before writing resource blocks for all of them one by one — Workflow 5 exists precisely so this isn't done unprompted for a whole category.
- **`review`'s `blast-radius` findings**: the most urgent category — a mixed state means an unrelated apply can be blocked by, or accidentally bundled with, a high-risk change (auth policies, IdPs). Prioritize splitting these before `efficiency`/`testing` findings.
- **`resolve-version` returning `source: none`**: don't guess a provider version or resource argument shape — fetch the latest release first (the `note` field has the exact command) before writing any `.tf`.
- **`list-root-modules` with more than one plausible candidate**: per "Locate the right root module" above, ask the user rather than picking the top-ranked one automatically when the ranking doesn't clearly separate a winner (e.g. two directories both have `has_provider_block: true`).

## Cross-skill references

- `discover_unmanaged.py`'s `list_script`/`get_args`/`list_args` in `RESOURCE_TYPES` point directly at other skills' read scripts (`okta-groups`, `okta-network-zones`, etc.) — a change to one of those scripts' `list`/`get` output shape affects what this skill can diff.
- `scaffold_project.py recommend-apps`/`recommend-groups` call `okta-apps`/`okta-groups`' `list` commands directly; their `label`/`profile.name` fields are what gets sharded.
- The generated `import` block's `id =` value is exactly what the corresponding read-skill's `get <id>` returned — use that skill's own `get` output to fill in the resource block's other arguments.

To add a resource type to the registry: confirm its doc's Import section says a bare Okta object ID is the entire `terraform import` argument (no composite ID, no type-branching), then add an entry to `RESOURCE_TYPES` in `scripts/discover_unmanaged.py` pointing at the existing read-skill script and subcommand that lists and gets it.
