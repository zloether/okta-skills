#!/usr/bin/env python3
"""Diff GET operations in management-minimal.yaml against what skills/*/scripts/*.py actually call.

Reports two kinds of gaps:
  1. Spec tags/paths that don't map to any skill's documented endpoint prefix (new resource areas).
  2. GET operations within an existing skill's prefix that the skill's script never calls.

Requires PyYAML (see requirements-dev.txt).
"""
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit('PyYAML is required: pip install -r requirements-dev.txt')

REPO_ROOT = Path(__file__).parent.parent
SPEC_PATH = REPO_ROOT / 'management-minimal.yaml'
AGENTS_MD = REPO_ROOT / 'AGENTS.md'
SKILLS_DIR = REPO_ROOT / 'skills'

_TABLE_ROW_RE = re.compile(r'^\|\s*(okta-[\w-]+)\s*\|\s*`skills/[\w-]+/`\s*\|\s*(.+?)\s*\|')
_BACKTICK_RE = re.compile(r'`([^`]+)`')


def normalize_path(path):
    """Replace each {param} path segment with '*' for structural comparison."""
    segments = path.strip('/').split('/')
    return tuple('*' if seg.startswith('{') and seg.endswith('}') else seg for seg in segments)


def parse_skill_prefixes(agents_md_text):
    """Return {skill_name: [normalized_prefix_tuple, ...]} from the Skill Inventory table."""
    prefixes = {}
    for line in agents_md_text.splitlines():
        match = _TABLE_ROW_RE.match(line)
        if not match:
            continue
        skill, endpoint_cell = match.groups()
        endpoints = [e for e in _BACKTICK_RE.findall(endpoint_cell) if e.startswith('/')]
        if endpoints:
            prefixes[skill] = [normalize_path(e) for e in endpoints]
    return prefixes


def prefix_matches(prefix, path):
    if len(prefix) > len(path):
        return False
    return all(p == '*' or p == s for p, s in zip(prefix, path))


def match_skill(path, skill_prefixes):
    """Return the skill whose prefix best (longest) matches path, or None."""
    best_skill, best_len = None, -1
    for skill, prefixes in skill_prefixes.items():
        for prefix in prefixes:
            if prefix_matches(prefix, path) and len(prefix) > best_len:
                best_skill, best_len = skill, len(prefix)
    return best_skill


def parse_spec_get_ops(spec_path):
    """Yield (normalized_path, raw_path, operation_id, tags) for every non-deprecated GET op."""
    loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
    with open(spec_path) as f:
        spec = yaml.load(f, Loader=loader)
    for path, methods in spec.get('paths', {}).items():
        if not isinstance(methods, dict):
            continue
        op = methods.get('get')
        if not isinstance(op, dict) or op.get('deprecated'):
            continue
        yield normalize_path(path), path, op.get('operationId', '?'), op.get('tags', ['?'])


def extract_implemented_paths(script_path):
    """Return the set of normalized path templates a skill script actually requests."""
    tree = ast.parse(script_path.read_text())
    templates = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr) or len(node.values) < 2:
            continue
        if not isinstance(node.values[0], ast.FormattedValue):
            continue
        second = node.values[1]
        if not (isinstance(second, ast.Constant) and isinstance(second.value, str)
                and second.value.startswith('/')):
            continue
        raw = ''.join(
            '\x00' if isinstance(v, ast.FormattedValue) else v.value
            for v in node.values
        )
        path = raw[raw.index('/'):]
        segments = tuple('*' if '\x00' in seg else seg for seg in path.strip('/').split('/'))
        templates.add(segments)
    return templates


def implemented_paths_for_skill(skill_name):
    templates = set()
    for script_path in sorted((SKILLS_DIR / skill_name / 'scripts').glob('*.py')):
        templates |= extract_implemented_paths(script_path)
    return templates


def fmt(path_tuple):
    return '/' + '/'.join(path_tuple)


def main():
    if not SPEC_PATH.exists():
        sys.exit(f'{SPEC_PATH} not found — run scripts/update-management-spec.sh first')

    skill_prefixes = parse_skill_prefixes(AGENTS_MD.read_text())
    ops = list(parse_spec_get_ops(SPEC_PATH))

    unmapped = defaultdict(list)
    by_skill = defaultdict(list)
    for norm_path, raw_path, op_id, tags in ops:
        skill = match_skill(norm_path, skill_prefixes)
        if skill is None:
            unmapped[tags[0]].append((raw_path, op_id))
        else:
            by_skill[skill].append((norm_path, raw_path, op_id))

    print(f'Okta API spec coverage diff ({SPEC_PATH.name}, {len(ops)} non-deprecated GET operations)\n')

    print('== Gaps in existing skills ==')
    gap_skills = 0
    for skill in sorted(by_skill):
        implemented = implemented_paths_for_skill(skill)
        gaps = [(raw, op_id) for norm, raw, op_id in by_skill[skill] if norm not in implemented]
        if not gaps:
            continue
        gap_skills += 1
        print(f'\n{skill}:')
        for raw, op_id in sorted(gaps):
            print(f'  GET {raw}  ({op_id})')
    if not gap_skills:
        print('  (none)')

    print('\n== Unmapped resource areas (no matching skill) ==')
    for tag in sorted(unmapped):
        print(f'\n[{tag}]')
        for raw, op_id in sorted(unmapped[tag]):
            print(f'  GET {raw}  ({op_id})')

    total_unmapped = sum(len(v) for v in unmapped.values())
    print('\n== Summary ==')
    print(f'{len(by_skill)} skills with matching endpoints, {gap_skills} of them have gaps')
    print(f'{len(unmapped)} unmapped tags, {total_unmapped} GET operations total')


if __name__ == '__main__':
    main()
