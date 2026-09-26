#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Locate the applicable Terraform root module in a repo and its pinned okta provider version.

Parsing here is regex-based, not a real HCL parser — good enough to detect the
common, flat shapes these blocks are almost always written in, but it can be
fooled by unusual nesting (e.g. a `module` block with a nested `providers = {}`
map). Treat its output as a strong hint, not ground truth.
"""
import argparse
import json
import re
import sys
from pathlib import Path

_PROVIDER_BLOCK_RE = re.compile(r'provider\s+"okta"\s*{')
_BACKEND_BLOCK_RE = re.compile(r'backend\s+"[a-z0-9_]+"\s*{')
_RESOURCE_RE = re.compile(r'resource\s+"(okta_[a-z0-9_]+)"')
_MODULE_BLOCK_RE = re.compile(r'module\s+"[^"]+"\s*{([^}]*)}')
_SOURCE_ATTR_RE = re.compile(r'source\s*=\s*"([^"]+)"')
_REQUIRED_PROVIDERS_OKTA_RE = re.compile(r'okta\s*=\s*{([^}]*)}')
_SOURCE_IS_OKTA_RE = re.compile(r'source\s*=\s*"okta/okta"')
_VERSION_ATTR_RE = re.compile(r'version\s*=\s*"([^"]+)"')
_LOCK_PROVIDER_BLOCK_RE = re.compile(r'provider\s+"registry\.terraform\.io/okta/okta"\s*{([^}]*)}')


def find_tf_dirs(root):
    """Every directory under root containing at least one *.tf file."""
    return sorted({p.parent for p in Path(root).rglob('*.tf')})


def dir_has_provider_block(tf_dir):
    return any(_PROVIDER_BLOCK_RE.search(f.read_text(errors='ignore')) for f in tf_dir.glob('*.tf'))


def dir_has_backend_block(tf_dir):
    return any(_BACKEND_BLOCK_RE.search(f.read_text(errors='ignore')) for f in tf_dir.glob('*.tf'))


def count_okta_resources(tf_dir):
    """okta_* resource block counts in this directory's own *.tf files (not recursive into modules)."""
    counts = {}
    for f in tf_dir.glob('*.tf'):
        for match in _RESOURCE_RE.finditer(f.read_text(errors='ignore')):
            counts[match.group(1)] = counts.get(match.group(1), 0) + 1
    return counts


def _scan_own_tf_files(tf_dir):
    """Single read pass over tf_dir's own *.tf files for the three things list_root_modules needs
    per directory, instead of reading each file three separate times."""
    has_provider = False
    has_backend = False
    counts = {}
    for f in tf_dir.glob('*.tf'):
        text = f.read_text(errors='ignore')
        has_provider = has_provider or bool(_PROVIDER_BLOCK_RE.search(text))
        has_backend = has_backend or bool(_BACKEND_BLOCK_RE.search(text))
        for match in _RESOURCE_RE.finditer(text):
            counts[match.group(1)] = counts.get(match.group(1), 0) + 1
    return has_provider, has_backend, counts


def _local_module_sources_in_file(tf_file):
    dirs = set()
    for block in _MODULE_BLOCK_RE.findall(tf_file.read_text(errors='ignore')):
        source_match = _SOURCE_ATTR_RE.search(block)
        if source_match and source_match.group(1).startswith('.'):
            dirs.add((tf_file.parent / source_match.group(1)).resolve())
    return dirs


def resolve_local_module_dirs(tf_dir):
    """Local (non-registry) module sources this directory's own *.tf files reference, resolved to real dirs."""
    dirs = set()
    for f in tf_dir.glob('*.tf'):
        dirs |= _local_module_sources_in_file(f)
    return dirs


def aggregate_okta_resource_counts(tf_dir, _seen=None):
    """count_okta_resources for tf_dir, plus recursively for any local module it composes in — so a
    root module split via `module { source = "./modules/..." }` is counted as one logical state."""
    tf_dir = Path(tf_dir).resolve()
    seen = _seen if _seen is not None else set()
    if tf_dir in seen:
        return {}
    seen.add(tf_dir)
    counts = dict(count_okta_resources(tf_dir))
    for child_dir in resolve_local_module_dirs(tf_dir):
        for rt, n in aggregate_okta_resource_counts(child_dir, seen).items():
            counts[rt] = counts.get(rt, 0) + n
    return counts


def find_module_callers(root):
    """Resolved directories referenced as a local `module` block's source anywhere under root."""
    resolved = set()
    for tf_file in Path(root).rglob('*.tf'):
        resolved |= _local_module_sources_in_file(tf_file)
    return resolved


def parse_required_version_constraint(tf_dir):
    """The version constraint string in this dir's `required_providers { okta = {...} }`, if any."""
    for f in tf_dir.glob('*.tf'):
        for block in _REQUIRED_PROVIDERS_OKTA_RE.findall(f.read_text(errors='ignore')):
            if not _SOURCE_IS_OKTA_RE.search(block):
                continue
            version_match = _VERSION_ATTR_RE.search(block)
            if version_match:
                return version_match.group(1)
    return None


def parse_lock_file(tf_dir):
    """The exact resolved okta provider version from .terraform.lock.hcl, if present."""
    lock_path = tf_dir / '.terraform.lock.hcl'
    if not lock_path.is_file():
        return None
    match = _LOCK_PROVIDER_BLOCK_RE.search(lock_path.read_text(errors='ignore'))
    if not match:
        return None
    version_match = _VERSION_ATTR_RE.search(match.group(1))
    return version_match.group(1) if version_match else None


def list_root_modules(root, resource_type=None):
    """Rank every .tf-containing directory by how likely it is to be the root module in play."""
    module_callers = find_module_callers(root)
    candidates = []
    for tf_dir in find_tf_dirs(root):
        has_provider, has_backend, resource_counts = _scan_own_tf_files(tf_dir)
        resource_counts = dict(resource_counts)
        for child_dir in resolve_local_module_dirs(tf_dir):
            for rt, n in aggregate_okta_resource_counts(child_dir, {tf_dir.resolve()}).items():
                resource_counts[rt] = resource_counts.get(rt, 0) + n
        candidates.append({
            'dir': str(tf_dir),
            'has_provider_block': has_provider,
            'has_backend_block': has_backend,
            'referenced_as_child_module': tf_dir.resolve() in module_callers,
            'okta_resource_counts': resource_counts,
            'matches_resource_type': (resource_type in resource_counts) if resource_type else None,
        })
    candidates.sort(key=lambda c: (
        c['referenced_as_child_module'] or not c['has_provider_block'],
        not c['matches_resource_type'],
        -sum(c['okta_resource_counts'].values()),
    ))
    return candidates


def resolve_version(tf_dir):
    """How to pin doc lookups for tf_dir: an exact locked version, an unresolved constraint, or nothing yet."""
    tf_dir = Path(tf_dir)
    locked = parse_lock_file(tf_dir)
    if locked:
        return {'source': 'lock', 'version': locked}
    constraint = parse_required_version_constraint(tf_dir)
    if constraint:
        return {
            'source': 'constraint',
            'version': None,
            'constraint': constraint,
            'note': (
                f'No .terraform.lock.hcl in {tf_dir}; run `terraform init` there to resolve '
                f'"{constraint}" to an exact version before fetching version-pinned docs.'
            ),
        }
    return {
        'source': 'none',
        'version': None,
        'note': (
            'No existing okta provider version pin found in this directory. Check the latest '
            'release before writing a required_providers block: '
            'curl -sSL https://api.github.com/repos/okta/terraform-provider-okta/releases/latest'
        ),
    }


def main():
    parser = argparse.ArgumentParser(description='Locate the applicable Terraform root module and its okta provider version')
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list-root-modules', help='Rank .tf directories by likelihood of being the relevant root module')
    p_list.add_argument('--dir', default='.', help='Directory to search (default: current directory)')
    p_list.add_argument('--resource-type', help='e.g. okta_group — ranks directories that already use it first')

    p_resolve = sub.add_parser('resolve-version', help="Determine a root module's pinned okta provider version")
    p_resolve.add_argument('--dir', required=True, help='Root module directory')

    args = parser.parse_args()
    try:
        if args.command == 'list-root-modules':
            result = list_root_modules(args.dir, args.resource_type)
        else:
            result = resolve_version(args.dir)
        print(json.dumps(result, indent=2))
    except Exception as e:  # noqa: BLE001 — top-level handler must turn any failure into a JSON error, not a traceback
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
