#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Diff live Okta resources against a Terraform project's state to find unmanaged ones.

Delegates reading live resources to the existing read-skills (via subprocess)
rather than calling the Okta API directly, so pagination/auth/error-handling
stays in one place. Only covers resource types with a single, non-branching
okta_* mapping — see SKILL.md's "Registry coverage" section for what's
deliberately left out and why.

Three distinct modes, deliberately kept separate:
- `list-types`: no API calls — returns the full discovery menu (what can be
  checked, and what can't) for presenting a multi-select to a user who
  doesn't know what's Terraform-manageable. See SKILL.md's "Workflow 2".
- `get`: fetch exactly one object by ID/URL — cheap, safe to run anytime.
- `find`: lists every live object of a type in the org — only run this when
  the user has explicitly asked to reconcile that whole category. See
  SKILL.md's "Workflow 5" for why this isn't something to do unprompted.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / 'shared'))
from local_cli import run_local
from subprocess_json import run_script_json

TERRAFORM_SHOW_TIMEOUT = 300

RESOURCE_TYPES = {
    'user': {
        'list_script': 'okta-users/scripts/users.py',
        'list_args': ['list'],
        'get_args': ['get'],
        'label_field': 'profile.login',
        'tf_resource_type': 'okta_user',
        'description': 'Users',
        'high_cardinality': True,
    },
    'group': {
        'list_script': 'okta-groups/scripts/groups.py',
        'list_args': ['list'],
        'get_args': ['get'],
        'label_field': 'profile.name',
        'tf_resource_type': 'okta_group',
        'description': 'Groups',
        'high_cardinality': True,
    },
    'group_rule': {
        'list_script': 'okta-groups/scripts/groups.py',
        'list_args': ['list-rules'],
        'get_args': ['get-rule'],
        'label_field': 'name',
        'tf_resource_type': 'okta_group_rule',
        'description': 'Group membership rules',
    },
    'network_zone': {
        'list_script': 'okta-network-zones/scripts/network_zones.py',
        'list_args': ['list'],
        'get_args': ['get'],
        'label_field': 'name',
        'tf_resource_type': 'okta_network_zone',
        'description': 'Network zones',
    },
    'authenticator': {
        'list_script': 'okta-authenticators/scripts/authenticators.py',
        'list_args': ['list'],
        'get_args': ['get'],
        'label_field': 'name',
        'tf_resource_type': 'okta_authenticator',
        'description': 'Authenticators (factor types)',
    },
    'behavior': {
        'list_script': 'okta-behaviors/scripts/behaviors.py',
        'list_args': ['list'],
        'get_args': ['get'],
        'label_field': 'name',
        'tf_resource_type': 'okta_behavior',
        'description': 'Behavior detection rules',
    },
    'auth_server': {
        'list_script': 'okta-authorization-servers/scripts/authorization_servers.py',
        'list_args': ['list'],
        'get_args': ['get'],
        'label_field': 'name',
        'tf_resource_type': 'okta_auth_server',
        'description': 'Custom authorization servers',
    },
    'admin_role_custom': {
        'list_script': 'okta-iam/scripts/iam.py',
        'list_args': ['list'],
        'get_args': ['get'],
        'label_field': 'label',
        'tf_resource_type': 'okta_admin_role_custom',
        'description': 'Custom admin roles (IAM)',
    },
    'resource_set': {
        'list_script': 'okta-iam/scripts/iam.py',
        'list_args': ['list-resource-sets'],
        'get_args': ['get-resource-set'],
        'label_field': 'label',
        'tf_resource_type': 'okta_resource_set',
        'description': 'IAM resource sets',
    },
}

# Terraform-manageable categories that can't be safely auto-mapped to one okta_* resource type
# (the mapping depends on a live object's own attributes, e.g. signOnMode or policy type) — surfaced
# in the discovery menu so a user unfamiliar with the provider still learns they exist, but handled
# by hand via Workflow 1/2 rather than through `get`/`find`.
MANUAL_ONLY_CATEGORIES = {
    'apps': {
        'description': 'Applications',
        'reason': (
            'Resource type depends on signOnMode (okta_app_oauth, okta_app_saml, okta_app_bookmark, '
            'okta_app_basic_auth, okta_app_swa, etc.); not every signOnMode has a matching resource.'
        ),
    },
    'policies': {
        'description': 'Policies (sign-on, password, MFA, profile enrollment, IdP discovery)',
        'reason': (
            "Resource type depends on the policy's type (okta_policy_signon, okta_policy_password, "
            'okta_policy_mfa, okta_policy_profile_enrollment, okta_policy_idp_discovery).'
        ),
    },
    'device_assurance_policy': {
        'description': 'Device assurance policies',
        'reason': (
            'Resource type depends on platform (okta_policy_device_assurance_android/_ios/'
            '_chromeos/_windows/_macos).'
        ),
    },
    'identity_provider': {
        'description': 'Identity providers',
        'reason': 'Resource type depends on type (okta_idp_saml, okta_idp_oidc, okta_idp_social).',
    },
    'schema_org_settings': {
        'description': (
            'Schemas, org settings, realms, OAuth client role assignments, '
            'security/attack-protection settings'
        ),
        'reason': 'Singleton or per-property configuration rather than discrete listable objects.',
    },
}

# Okta concepts with no okta_* Terraform resource at all — not manageable in Terraform by any means.
NOT_TERRAFORM_MANAGEABLE = ['devices', 'sessions', 'logs', 'api_tokens']


def describe_registry():
    """Full discovery menu for a user who doesn't know what's Terraform-manageable: auto-discoverable
    types (usable with `get`/`find`), manual-only categories (exist in Terraform but need Workflow 3/4),
    and concepts with no Terraform representation at all."""
    return {
        'auto_discoverable': {
            name: {
                'tf_resource_type': spec['tf_resource_type'],
                'description': spec['description'],
                'high_cardinality': spec.get('high_cardinality', False),
            }
            for name, spec in RESOURCE_TYPES.items()
        },
        'manual_only': MANUAL_ONLY_CATEGORIES,
        'not_terraform_manageable': NOT_TERRAFORM_MANAGEABLE,
    }


def _get_by_path(obj, dotted_path):
    """Walk a dotted path (e.g. 'profile.login') through nested dicts; None if any segment is missing."""
    for part in dotted_path.split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def _sanitize(text):
    value = re.sub(r'[^a-z0-9_-]', '_', str(text).lower())
    return re.sub(r'_+', '_', value).strip('_-')


def safe_tf_name(label, fallback_id):
    """Sanitize a live object's label into a valid Terraform identifier, falling back to
    fallback_id if the label is missing or sanitizes to nothing (e.g. a punctuation-only label)."""
    value = _sanitize(label) if label else _sanitize(fallback_id)
    if not value:
        value = _sanitize(fallback_id)
    if not value or value[0].isdigit():
        value = f'_{value}'
    return value


def run_read_script(script, args):
    """Invoke a read-skill's subcommand (list or get) and return its parsed JSON stdout."""
    return run_script_json(REPO_ROOT / 'skills' / script, args)


def resolve_resource_id(id_or_url):
    """Accept a bare Okta object ID or an Okta URL (admin console or API) and return just the ID."""
    if not re.match(r'^https?://', id_or_url):
        return id_or_url
    path = urlparse(id_or_url).path
    segments = [s for s in path.split('/') if s]
    if not segments:
        raise ValueError(f'could not extract an object ID from URL: {id_or_url}')
    return segments[-1]


def walk_state_resources(module):
    """Yield every resource in a `terraform show -json` module, recursing into child modules."""
    yield from module.get('resources', [])
    for child in module.get('child_modules', []):
        yield from walk_state_resources(child)


def read_managed_resources(tf_dir, tf_resource_type):
    """Return (ids, names) already managed as `tf_resource_type` in tf_dir's state: the live-object
    IDs, and the Terraform-local resource names already taken (e.g. "eng" in `okta_group.eng`) — so
    a caller generating new import blocks can avoid colliding with an address already in use."""
    proc = subprocess.run(
        ['terraform', f'-chdir={tf_dir}', 'show', '-no-color', '-json'],
        capture_output=True, text=True, check=False, timeout=TERRAFORM_SHOW_TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(f'terraform show -json failed in {tf_dir}: {proc.stderr.strip()}')
    state = json.loads(proc.stdout) if proc.stdout.strip() else {}
    root_module = state.get('values', {}).get('root_module', {})
    ids, names = set(), set()
    for resource in walk_state_resources(root_module):
        if resource.get('type') != tf_resource_type or resource.get('mode', 'managed') != 'managed':
            continue
        ids.add(resource['values']['id'])
        if resource.get('name'):
            names.add(resource['name'])
    return ids, names


def diff_live_vs_managed(live_objects, managed_ids, label_field, tf_resource_type, managed_names=frozenset()):
    """Pure diff: which live objects (list of dicts with an 'id' key) aren't in managed_ids.

    Disambiguates by appending the object's own ID to any sanitized name that collides with
    an earlier one in this same batch, or with managed_names (an address already taken by a
    resource already in state), so the generated import blocks never target the same
    Terraform resource address twice.
    """
    unmanaged = []
    seen_names = set(managed_names)
    for obj in live_objects:
        obj_id = obj.get('id')
        if obj_id in managed_ids:
            continue
        label = _get_by_path(obj, label_field)
        name = safe_tf_name(label, obj_id)
        if name in seen_names:
            name = safe_tf_name(f'{label}_{obj_id}' if label else obj_id, obj_id)
        seen_names.add(name)
        unmanaged.append({
            'id': obj_id,
            'label': label,
            'tf_resource_type': tf_resource_type,
            'import_block': f'import {{\n  to = {tf_resource_type}.{name}\n  id = "{obj_id}"\n}}',
        })
    return unmanaged


def find_unmanaged(resource_type, tf_dir):
    """Bulk mode: list every live object of resource_type and diff against tf_dir's state.

    Lists the entire org's population of this type. Only call this for a category
    the user has explicitly asked to reconcile — see the module docstring.
    """
    spec = RESOURCE_TYPES[resource_type]
    live_objects = run_read_script(spec['list_script'], spec['list_args'])
    managed_ids, managed_names = read_managed_resources(tf_dir, spec['tf_resource_type'])
    return diff_live_vs_managed(live_objects, managed_ids, spec['label_field'], spec['tf_resource_type'], managed_names)


def find_single(resource_type, id_or_url, tf_dir):
    """Targeted mode: fetch exactly one live object by ID/URL and check if it's managed."""
    spec = RESOURCE_TYPES[resource_type]
    resource_id = resolve_resource_id(id_or_url)
    live_object = run_read_script(spec['list_script'], [*spec['get_args'], resource_id])
    managed_ids, managed_names = read_managed_resources(tf_dir, spec['tf_resource_type'])
    unmanaged = diff_live_vs_managed(
        [live_object], managed_ids, spec['label_field'], spec['tf_resource_type'], managed_names
    )
    if unmanaged:
        return unmanaged[0]
    return {
        'id': live_object.get('id'),
        'tf_resource_type': spec['tf_resource_type'],
        'already_managed': True,
    }


def main():
    parser = argparse.ArgumentParser(description="Find Okta resources not yet managed in a Terraform project")
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser(
        'list-types',
        help='Full discovery menu: auto-discoverable types, manual-only categories, and non-manageable concepts',
    )

    p_get = sub.add_parser(
        'get',
        help='Check a single resource (by ID or URL) against Terraform state — cheap, safe to run anytime',
    )
    p_get.add_argument('resource_type', choices=sorted(RESOURCE_TYPES), help='Resource type of the object')
    p_get.add_argument('--id', required=True, help='Okta object ID, or an admin console / API URL containing it')
    p_get.add_argument('--tf-dir', default='.', help='Terraform working directory (default: current directory)')

    p_find = sub.add_parser(
        'find',
        help='Bulk: list every live object of a type and diff against Terraform state. '
             'Lists the whole org for that type — only run when the user explicitly asked '
             'to reconcile that category, not as an unprompted sweep.',
    )
    p_find.add_argument('resource_type', choices=sorted(RESOURCE_TYPES), help='Resource type to check')
    p_find.add_argument('--tf-dir', default='.', help='Terraform working directory (default: current directory)')

    def dispatch(args):
        if args.command == 'list-types':
            return describe_registry()
        if args.command == 'get':
            return find_single(args.resource_type, args.id, args.tf_dir)
        return find_unmanaged(args.resource_type, args.tf_dir)

    run_local(parser, dispatch)


if __name__ == '__main__':
    main()
