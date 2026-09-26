#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Scaffold a multi-state Terraform project layout for managing Okta.

Okta doesn't publish a recommended repo layout, and Okta's API enforces
per-endpoint rate-limit buckets (see developer.okta.com/docs/reference/rate-limits/)
that vary by subscription — a single monolithic state means every plan/apply
walks every resource type together, and one slow or throttled type blocks the
rest. This script proposes and can scaffold a project split into one Terraform
state per isolation group, so day-to-day changes to (say) network zones don't
have to touch the entire app population, and prod apps can be tested against a
new provider version independently of non-prod.

Two things this deliberately does NOT do: run `terraform init`, and guess your
backend (S3/TFC/etc.) or your prod/non-prod naming convention — those are
org-specific, so the generated files leave clear TODO markers for a human.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / 'shared'))
from subprocess_json import run_script_json

# One Terraform state per entry here is the baseline recommendation for any
# project. Each is small enough to plan quickly on its own, and high-blast-
# radius resources (auth policies, IdPs) are isolated so an apply there can't
# get queued behind, or accidentally bundled with, a routine apps/groups apply.
ISOLATION_GROUPS = {
    'network_zones': {
        'description': 'Network zones',
        'resource_types': ['okta_network_zone'],
        'rationale': 'Small and low-churn; isolating it keeps its plans fast and unaffected by unrelated changes.',
    },
    'authenticators': {
        'description': 'Authenticators (factor types)',
        'resource_types': ['okta_authenticator'],
        'rationale': (
            'Org-wide MFA configuration with high blast radius; isolate so it never rides '
            'along with a routine app/group apply.'
        ),
    },
    'behaviors': {
        'description': 'Behavior detection rules',
        'resource_types': ['okta_behavior'],
        'rationale': 'Small, low-churn set feeding risk-based policies.',
    },
    'auth_servers': {
        'description': 'Custom authorization servers',
        'resource_types': ['okta_auth_server'],
        'rationale': 'Changes here affect every client relying on the server; keep its plan/apply cadence independent.',
    },
    'iam': {
        'description': 'Custom admin roles and IAM resource sets',
        'resource_types': ['okta_admin_role_custom', 'okta_resource_set'],
        'rationale': 'Admin-access configuration; isolate for tighter review/approval than routine resources.',
    },
    'auth_policies': {
        'description': 'Authentication, password, MFA, and other policies',
        'resource_types': [
            'okta_policy_signon', 'okta_policy_password', 'okta_policy_mfa',
            'okta_policy_profile_enrollment', 'okta_policy_idp_discovery',
        ],
        'rationale': (
            'High blast radius (a bad sign-on policy can lock users out); keep this state small '
            'and reviewed on its own, separate from apps/groups churn.'
        ),
    },
    'device_assurance': {
        'description': 'Device assurance policies',
        'resource_types': [
            'okta_policy_device_assurance_android', 'okta_policy_device_assurance_ios',
            'okta_policy_device_assurance_chromeos', 'okta_policy_device_assurance_windows',
            'okta_policy_device_assurance_macos',
        ],
        'rationale': 'Feeds into sign-on policy conditions; isolate from the policies themselves so either can be planned alone.',
    },
    'identity_providers': {
        'description': 'Identity providers (SAML/OIDC/social)',
        'resource_types': ['okta_idp_saml', 'okta_idp_oidc', 'okta_idp_social'],
        'rationale': 'Federation config with high blast radius and infrequent changes; isolate from high-churn states.',
    },
}

# Apps and groups are handled separately from ISOLATION_GROUPS: they're the two
# object types with enough cardinality in a typical org to warrant sharding, and
# apps additionally need a prod/non-prod split (see recommend_apps).
DEFAULT_MAX_PER_SHARD = 60


def describe_isolation_groups():
    return dict(ISOLATION_GROUPS)


def run_read_script(script, args):
    """Invoke a read-skill's `list` subcommand and return its parsed JSON stdout."""
    return run_script_json(REPO_ROOT / 'skills' / script, args)


def run_locate_root_module(repo_dir):
    """Inventory every .tf-containing directory under repo_dir via locate_root_module.py."""
    script_path = Path(__file__).resolve().parent / 'locate_root_module.py'
    return run_script_json(script_path, ['list-root-modules', '--dir', str(repo_dir)])


def shard_by_count(labels, max_per_shard):
    """Split labels into balanced shards of at most max_per_shard each.

    Balances shard *count*, not letter ranges — a fixed A-F/G-M split can be
    wildly uneven in practice (app names cluster around vendor names), so this
    divides the sorted list into evenly-sized chunks instead and reports the
    label range each chunk actually covers.
    """
    if max_per_shard <= 0:
        raise ValueError('max_per_shard must be positive')
    sorted_labels = sorted(labels)
    n = len(sorted_labels)
    if n == 0:
        return []
    shard_count = -(-n // max_per_shard)  # ceil division
    base, extra = divmod(n, shard_count)
    shards = []
    start = 0
    for i in range(shard_count):
        size = base + (1 if i < extra else 0)
        chunk = sorted_labels[start:start + size]
        shards.append({'shard': i + 1, 'count': len(chunk), 'first': chunk[0], 'last': chunk[-1], 'labels': chunk})
        start += size
    return shards


def recommend_apps(max_per_shard=DEFAULT_MAX_PER_SHARD, prod_pattern=None):
    """Recommend a prod/non-prod split and shard layout for the org's apps.

    Okta has no built-in "environment" field on apps, so prod/non-prod can only
    be classified if the caller supplies a naming convention (prod_pattern,
    matched case-insensitively against the app label). Without one, every app
    comes back unclassified with a note asking how the org distinguishes them.
    """
    apps = run_read_script('okta-apps/scripts/apps.py', ['list'])
    labels = [a.get('label') or a.get('id') for a in apps]
    if prod_pattern is None:
        return {
            'total': len(labels),
            'note': (
                'Okta has no built-in prod/non-prod field for apps. Provide --prod-pattern '
                '(a regex matched against each app label) so prod apps can be split into their '
                'own state — recommended so a provider upgrade can be tested on non-prod first.'
            ),
            'unclassified_shards': shard_by_count(labels, max_per_shard),
        }
    pattern = re.compile(prod_pattern, re.IGNORECASE)
    prod = sorted(label for label in labels if pattern.search(label))
    nonprod = [label for label in labels if not pattern.search(label)]
    return {
        'total': len(labels),
        'prod': {'count': len(prod), 'labels': prod},
        'nonprod_shards': shard_by_count(nonprod, max_per_shard),
    }


def recommend_groups(max_per_shard=DEFAULT_MAX_PER_SHARD):
    groups = run_read_script('okta-groups/scripts/groups.py', ['list'])
    labels = [g.get('profile', {}).get('name') or g.get('id') for g in groups]
    return {'total': len(labels), 'shards': shard_by_count(labels, max_per_shard)}


def _resource_type_to_group():
    """Reverse index: okta_* resource type -> the ISOLATION_GROUPS key that covers it."""
    return {rt: name for name, spec in ISOLATION_GROUPS.items() for rt in spec['resource_types']}


def classify_resource_type(resource_type):
    """Bucket a live `okta_*` resource type for the review: its isolation group, or a
    dedicated 'apps'/'groups'/'users' bucket for the high-cardinality types that are
    sharded rather than grouped. Anything not covered by ISOLATION_GROUPS falls into
    'other' — a coarse catch-all, so treat 'other' mixing with something else as a
    weaker signal than a mix of two named groups."""
    if resource_type.startswith('okta_app_'):
        return 'apps'
    if resource_type == 'okta_group':
        return 'groups'
    if resource_type == 'okta_user':
        return 'users'
    return _resource_type_to_group().get(resource_type, 'other')


def review_layout(repo_dir, max_per_shard=DEFAULT_MAX_PER_SHARD):
    """Audit an existing Terraform project's directory/state layout against the isolation-group
    model recommended by `list-groups`/`init`, and flag concrete efficiency, blast-radius, and
    testing issues. Read-only — inspects .tf files via locate_root_module.py, never runs terraform.

    Does not propose or perform any migration: splitting a flagged state means creating new
    directories (via `init`) and moving the affected resource blocks + `terraform state mv` by
    hand — this skill never runs `terraform state mv` itself.
    """
    modules = run_locate_root_module(repo_dir)
    states = [m for m in modules if m['has_provider_block']] or modules

    findings = []
    total_counts = {}
    app_dirs_with_resources = 0

    for state in states:
        counts = state['okta_resource_counts']
        if not counts:
            continue
        for rt, n in counts.items():
            total_counts[rt] = total_counts.get(rt, 0) + n

        groups_here = {classify_resource_type(rt) for rt in counts}
        if len(groups_here) > 1:
            findings.append({
                'dir': state['dir'],
                'category': 'blast-radius',
                'issue': f'Mixes {", ".join(sorted(groups_here))} in one state.',
                'recommendation': (
                    'Split into one state per isolation group so a change to one type cannot '
                    "block, or get bundled with, an apply for another — see `list-groups`/`init`."
                ),
            })

        app_count = sum(n for rt, n in counts.items() if rt.startswith('okta_app_'))
        if app_count > 0:
            app_dirs_with_resources += 1
        if app_count > max_per_shard:
            findings.append({
                'dir': state['dir'],
                'category': 'efficiency',
                'issue': f'{app_count} app resources in one state (over the {max_per_shard}-per-shard guideline).',
                'recommendation': 'Shard apps across multiple states — see `recommend-apps` for a balanced split.',
            })

        group_count = counts.get('okta_group', 0)
        if group_count > max_per_shard:
            findings.append({
                'dir': state['dir'],
                'category': 'efficiency',
                'issue': f'{group_count} okta_group resources in one state (over the {max_per_shard}-per-shard guideline).',
                'recommendation': 'Shard groups across multiple states — see `recommend-groups` for a balanced split.',
            })

        if not state['has_backend_block']:
            findings.append({
                'dir': state['dir'],
                'category': 'testing',
                'issue': 'No remote backend configured (state is local-only).',
                'recommendation': (
                    'Configure a remote backend (S3, Terraform Cloud, etc.) so state is shared, '
                    'locked, and safe to plan/apply from CI.'
                ),
            })

    if app_dirs_with_resources == 1:
        app_state = next(s for s in states if any(rt.startswith('okta_app_') for rt in s['okta_resource_counts']))
        findings.append({
            'dir': app_state['dir'],
            'category': 'testing',
            'issue': 'All apps live in a single state with no prod/non-prod split.',
            'recommendation': (
                'Separate prod and non-prod apps into their own states (see `recommend-apps '
                '--prod-pattern`) so a provider upgrade can be validated against non-prod before '
                'touching production sign-in.'
            ),
        })

    return {'states_reviewed': len(states), 'total_resource_counts': total_counts, 'findings': findings}


_VERSIONS_TF_TEMPLATE = """terraform {{
  required_providers {{
    okta = {{
      source  = "okta/okta"
      version = "~> X.Y"  # TODO: pin — see locate_root_module.py resolve-version, or the latest release
    }}
  }}

  # TODO: configure a remote backend so this state isn't local-only, e.g.:
  # backend "s3" {{
  #   bucket = "..."
  #   key    = "okta/{name}/terraform.tfstate"
  #   region = "..."
  # }}
}}

provider "okta" {{}}
"""

_README_TEMPLATE = """# {description}

Isolation group: `{name}`

**Why this is its own state:** {rationale}

This directory is a separate Terraform root module and state, deliberately
isolated from the rest of the project — see `skills/okta-terraform/SKILL.md`
for how to add resources here and how to reconcile it against the live org.
"""


def init_layout(dest_dir, groups, apps_prod=False, apps_nonprod_shards=0, group_shards=0):
    """Create a skeleton directory (versions.tf + README.md, no init/apply) per selected isolation group.

    Skips any directory that already exists, mirroring install.sh's caution
    around not clobbering a user's in-progress work.
    """
    dest = Path(dest_dir)
    created, skipped = [], []

    def write_group(name, description, rationale):
        group_dir = dest / name
        if group_dir.exists():
            skipped.append(name)
            return
        group_dir.mkdir(parents=True)
        (group_dir / 'versions.tf').write_text(_VERSIONS_TF_TEMPLATE.format(name=name))
        (group_dir / 'README.md').write_text(
            _README_TEMPLATE.format(name=name, description=description, rationale=rationale)
        )
        created.append(name)

    for name in groups:
        if name not in ISOLATION_GROUPS:
            raise ValueError(f'unknown isolation group: {name}')
        spec = ISOLATION_GROUPS[name]
        write_group(name, spec['description'], spec['rationale'])

    if apps_prod:
        write_group(
            'apps-prod', 'Production applications',
            'Kept out of every non-prod apply so a provider upgrade or bulk app change can be '
            'validated on non-prod first, without risking production sign-in.',
        )
    for i in range(1, apps_nonprod_shards + 1):
        write_group(
            f'apps-nonprod-shard-{i}', f'Non-production applications, shard {i}',
            'Sharded by name to keep each apply well under the apps API rate-limit bucket and to '
            'bound blast radius — see `scaffold_project.py recommend-apps` for which apps belong here.',
        )
    for i in range(1, group_shards + 1):
        write_group(
            f'groups-shard-{i}', f'Groups, shard {i}',
            'Sharded by name to keep each apply well under the groups API rate-limit bucket — '
            'see `scaffold_project.py recommend-groups` for which groups belong here.',
        )

    return {'created': created, 'skipped': skipped}


def main():
    parser = argparse.ArgumentParser(description='Scaffold a multi-state Terraform project layout for Okta')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list-groups', help='List the recommended isolation groups and why each is separated')

    p_apps = sub.add_parser(
        'recommend-apps', help="Recommend a prod/non-prod split and shard layout for the org's apps"
    )
    p_apps.add_argument('--max-per-shard', type=int, default=DEFAULT_MAX_PER_SHARD)
    p_apps.add_argument('--prod-pattern', help='Regex matched (case-insensitively) against app labels to classify prod apps')

    p_groups = sub.add_parser('recommend-groups', help="Recommend a shard layout for the org's groups")
    p_groups.add_argument('--max-per-shard', type=int, default=DEFAULT_MAX_PER_SHARD)

    p_review = sub.add_parser(
        'review',
        help='Audit an existing Terraform project layout: blast-radius, efficiency, and testing '
             'findings — read-only, never runs terraform',
    )
    p_review.add_argument('--dir', required=True, help='Terraform project directory to audit')
    p_review.add_argument('--max-per-shard', type=int, default=DEFAULT_MAX_PER_SHARD)

    p_init = sub.add_parser(
        'init',
        help='Create skeleton directories (versions.tf + README.md) for selected isolation groups — '
             'no terraform init/apply',
    )
    p_init.add_argument('--dir', required=True, help='Destination directory for the project layout')
    p_init.add_argument(
        '--groups', default='',
        help=f'Comma-separated isolation groups to scaffold: {", ".join(sorted(ISOLATION_GROUPS))}',
    )
    p_init.add_argument('--apps-prod', action='store_true', help='Also scaffold an apps-prod/ state')
    p_init.add_argument('--apps-nonprod-shards', type=int, default=0, help='Number of apps-nonprod-shard-N/ states to scaffold')
    p_init.add_argument('--group-shards', type=int, default=0, help='Number of groups-shard-N/ states to scaffold')

    args = parser.parse_args()
    try:
        if args.command == 'list-groups':
            result = describe_isolation_groups()
        elif args.command == 'recommend-apps':
            result = recommend_apps(args.max_per_shard, args.prod_pattern)
        elif args.command == 'recommend-groups':
            result = recommend_groups(args.max_per_shard)
        elif args.command == 'review':
            result = review_layout(args.dir, args.max_per_shard)
        else:
            groups = [g for g in args.groups.split(',') if g]
            result = init_layout(args.dir, groups, args.apps_prod, args.apps_nonprod_shards, args.group_shards)
        print(json.dumps(result, indent=2))
    except Exception as e:  # noqa: BLE001 — top-level handler must turn any failure into a JSON error, not a traceback
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
