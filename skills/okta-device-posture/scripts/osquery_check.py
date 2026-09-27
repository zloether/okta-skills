#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "PyYAML>=6.0",
# ]
# ///
"""Scaffold and validate custom osquery-based Okta Advanced Posture Checks, entirely locally.

Advanced Posture Checks are a different feature from the EDR-integration device posture
checks read by device_posture.py: Okta Verify runs an admin-authored osquery SQL query on
the device and reports the result back for a device assurance policy to evaluate. Okta
doesn't expose a public API to create these checks — they're pasted into the Admin Console
by hand — so this script never calls the Okta API. It only helps draft and sanity-check the
YAML/query locally first, following the format Okta's own sample-checks repo uses:
https://github.com/okta/customer-detections/tree/master/sample_osquery_checks
"""
import argparse
import sys
import uuid
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / 'shared'))
from local_cli import run_local

ALLOWED_PLATFORMS = {'macOS', 'Windows', 'Linux'}

_SKELETON_QUERY = """-- TODO: replace with your osquery SQL. Two established patterns (see SKILL.md):
-- 1) Presence check: non-empty result means the check fails (indicator found).
--      SELECT 1 AS result FROM (
--          SELECT path FROM file WHERE path LIKE '/path/to/indicator' LIMIT 1
--      );
-- 2) Weighted/scored check: always returns one row with an explicit 0/1 flag,
--    combining several weak signals to cut down false positives.
--      WITH indicator_a AS (SELECT COALESCE(COUNT(*), 0) AS total FROM processes WHERE name LIKE '%x%'),
--           indicator_b AS (SELECT COALESCE(COUNT(*), 0) AS total FROM file WHERE path LIKE '%x%')
--      SELECT CASE WHEN (indicator_a.total + indicator_b.total) > 1 THEN 1 ELSE 0 END AS detected
--      FROM indicator_a, indicator_b;
SELECT 1 AS result FROM (SELECT 1 WHERE 1 = 0);
"""


def _yaml_scalar(value):
    """Render value as PyYAML would inline, safely quoting it if it needs quoting."""
    return yaml.safe_dump({'x': value}, default_flow_style=False).strip()[3:]


def _yaml_block(text):
    """Render text as a `|` block scalar, indented to match Okta's own sample checks."""
    body = '\n'.join(f'    {line}' if line else '' for line in text.rstrip('\n').split('\n'))
    return f'|\n{body}'


def render_check_yaml(doc):
    """Render a check dict (title/id/description/references/author/platform/query) as YAML text."""
    lines = [
        f"title: {_yaml_scalar(doc['title'])}",
        f"id: {_yaml_scalar(doc['id'])}",
        f"description: {_yaml_block(doc['description'])}",
    ]
    if doc['references']:
        lines.append('references:')
        lines += [f'    - {_yaml_scalar(r)}' for r in doc['references']]
    else:
        lines.append('references: []')
    lines.append('author:')
    lines += [f'    - {_yaml_scalar(a)}' for a in doc['author']]
    if isinstance(doc['platform'], list):
        lines.append('platform:')
        lines += [f'    - {_yaml_scalar(p)}' for p in doc['platform']]
    else:
        lines.append(f"platform: {_yaml_scalar(doc['platform'])}")
    lines.append(f"query: {_yaml_block(doc['query'])}")
    return '\n'.join(lines) + '\n'


def new_check(title, description, platforms, authors, references, out_path, query=None):
    """Build and write a new check YAML skeleton to out_path. Never overwrites an existing file."""
    out_path = Path(out_path)
    if out_path.exists():
        raise FileExistsError(f'{out_path} already exists — pick a different --out path')
    unknown = set(platforms) - ALLOWED_PLATFORMS
    if unknown:
        raise ValueError(f'unknown platform(s): {", ".join(sorted(unknown))} — must be one of {sorted(ALLOWED_PLATFORMS)}')

    doc = {
        'title': title,
        'id': uuid.uuid4().hex,
        'description': description,
        'references': list(references),
        'author': list(authors),
        'platform': platforms[0] if len(platforms) == 1 else list(platforms),
        'query': query or _SKELETON_QUERY,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_check_yaml(doc))
    return {'written': str(out_path), 'id': doc['id']}


def validate_check(path):
    """Structural check of a check YAML file: required fields, allowed platform values, a
    non-empty query. Never runs the query — osquery itself is the only thing that can tell you
    if it's valid SQL against your schema version; see SKILL.md for testing with `osqueryi`."""
    text = Path(path).read_text()
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        return {'valid': False, 'errors': [f'not valid YAML: {e}'], 'warnings': []}

    if not isinstance(doc, dict):
        return {'valid': False, 'errors': ['top-level YAML must be a mapping'], 'warnings': []}

    errors = []
    for field in ('title', 'id', 'description', 'author', 'platform', 'query'):
        if not doc.get(field):
            errors.append(f'missing or empty required field: {field}')

    platform = doc.get('platform')
    platforms = platform if isinstance(platform, list) else [platform] if platform else []
    non_string_platforms = [p for p in platforms if not isinstance(p, str)]
    if non_string_platforms:
        # YAML 1.1 parses bareword no/yes/on/off as booleans, so a mistyped `platform: no` lands
        # here rather than as the unknown-string case below — report it instead of letting the
        # set/sorted/join calls below crash on a non-string value.
        errors.append(f'platform value(s) must be strings, got: {non_string_platforms!r}')
    else:
        unknown = set(platforms) - ALLOWED_PLATFORMS
        if unknown:
            errors.append(f'unknown platform(s): {", ".join(sorted(unknown))} — must be one of {sorted(ALLOWED_PLATFORMS)}')

    warnings = []
    query = (doc.get('query') or '').lower()
    if query and 'select' not in query:
        warnings.append('query has no SELECT statement — osquery checks must return a result set')
    if query and not any(marker in query for marker in ('as result', 'as detected', '_detected', 'case when')):
        warnings.append(
            "query doesn't obviously follow either established pattern (a 'result' presence column, "
            "or a CASE-based 0/1 detection flag) — double check how Okta will evaluate its output"
        )

    return {'valid': not errors, 'errors': errors, 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(
        description='Scaffold and validate custom osquery-based Okta Advanced Posture Checks (local only, no Okta API calls)'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_new = sub.add_parser('new', help='Scaffold a new check YAML file')
    p_new.add_argument('--title', required=True)
    p_new.add_argument('--description', required=True)
    p_new.add_argument('--platform', required=True, action='append', choices=sorted(ALLOWED_PLATFORMS), help='Repeat for multiple platforms')
    p_new.add_argument('--author', required=True, action='append', help='Repeat for multiple authors')
    p_new.add_argument('--reference', action='append', default=[], help='Repeat for multiple reference URLs')
    p_new.add_argument('--query-file', help='Path to a file with the finished query; omit to write a TODO skeleton')
    p_new.add_argument('--out', required=True, help='Output .yml path')

    p_validate = sub.add_parser('validate', help='Structurally validate a check YAML file')
    p_validate.add_argument('path')

    def dispatch(args):
        if args.command == 'new':
            query = Path(args.query_file).read_text() if args.query_file else None
            return new_check(args.title, args.description, args.platform, args.author, args.reference, args.out, query)
        return validate_check(args.path)

    run_local(parser, dispatch)


if __name__ == '__main__':
    main()
