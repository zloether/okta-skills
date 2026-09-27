#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read-only wrapper around the `terraform` CLI, for this skill's own direct use of it.

discover_unmanaged.py and locate_root_module.py already call `terraform show -json`
themselves via subprocess for internal reads. This wrapper is what SKILL.md tells the
*agent* to invoke directly (to plan, validate, or fmt generated configuration) — the one
place where this skill's "never apply/import" boundary otherwise depended entirely on the
agent reading and obeying SKILL.md's prose, despite having unrestricted Bash. A misread
instruction, a prompt injection embedded in a .tf file or README read mid-task, or a model
error can no longer reach `terraform apply`/`import`/`destroy` through this skill's own
tooling. It's not a hard sandbox — the agent's Bash access is still unrestricted outside
this wrapper — but SKILL.md always routes through it for exactly this reason.

Usage mirrors the real CLI: pass the subcommand and its normal arguments.
    uv run scripts/safe_terraform.py plan -chdir=path/to/dir
    uv run scripts/safe_terraform.py validate -chdir=path/to/dir
    uv run scripts/safe_terraform.py state list -chdir=path/to/dir
"""
import subprocess
import sys

# Every one of these is read-only with respect to a live Okta org and to Terraform state's
# resource tracking. `init` is included because it only downloads providers/modules and can
# set up a backend — it doesn't apply, import, or otherwise change what's actually managed.
ALLOWED_SUBCOMMANDS = {'plan', 'validate', 'fmt', 'show', 'init'}
ALLOWED_STATE_SUBCOMMANDS = {'list', 'show'}


def _first_positional(args):
    """The first non-flag argument, skipping global flags like -chdir=./x."""
    for arg in args:
        if not arg.startswith('-'):
            return arg
    return None


def check_allowed(args):
    """Raise ValueError if args would run anything other than a read-only terraform operation."""
    subcommand = _first_positional(args)
    if subcommand is None:
        raise ValueError('no terraform subcommand given')
    if subcommand == 'state':
        remaining = args[args.index('state') + 1:]
        sub_subcommand = _first_positional(remaining)
        if sub_subcommand not in ALLOWED_STATE_SUBCOMMANDS:
            raise ValueError(
                f'"terraform state {sub_subcommand}" is not allowed by this skill\'s tooling — only '
                f'{sorted(ALLOWED_STATE_SUBCOMMANDS)} are read-only. Mutating state (mv, rm, etc.) is '
                f"the user's explicit action, run by them outside this skill."
            )
        return
    if subcommand not in ALLOWED_SUBCOMMANDS:
        raise ValueError(
            f'"terraform {subcommand}" is not allowed by this skill\'s tooling — only read-only '
            f'operations ({sorted(ALLOWED_SUBCOMMANDS)}, or "state list"/"state show") are permitted. '
            f"Applying, importing, or otherwise mutating a live Okta org is the user's explicit "
            f'action, run by them outside this skill.'
        )


def main():
    args = sys.argv[1:]
    try:
        check_allowed(args)
    except ValueError as e:
        print(f'error: {e}', file=sys.stderr)
        sys.exit(1)
    proc = subprocess.run(['terraform', *args], check=False, timeout=300)
    sys.exit(proc.returncode)


if __name__ == '__main__':
    main()
