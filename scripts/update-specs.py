#!/usr/bin/env python3
"""Download the Okta OpenAPI specs the skills are built against into the repo root.

Usage: update-specs.py [--list] [name ...]   (no names = all specs)

Each download is validated as an OpenAPI document before it replaces the local copy, so a
failed or truncated fetch never clobbers a good file. Local copies are gitignored.
Stdlib only.
"""
import argparse
import hashlib
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# name -> (url, local filename). To track another spec, add an entry here, add its filename to
# .gitignore, and (to include it in coverage diffs) to SPEC_FILES in diff-spec-coverage.py.
SPECS = {
    # The -minimal variant omits examples and is what diff-spec-coverage.py was built against.
    'management': (
        'https://raw.githubusercontent.com/okta/okta-management-openapi-spec/refs/heads/master/dist/current/management-minimal.yaml',
        'management-minimal.yaml',
    ),
    # Okta for AI Agents (Beta). Not in the public okta-management-openapi-spec repo; this is the
    # bundle behind the "Download OpenAPI description" link on the developer.okta.com docs page.
    'workload-principals': (
        'https://okta.redocly.app/docs/api/_bundle/secures-ai/openapi/secures-ai-workload-principals/secures-ai-workload-principals.yaml',
        'workload-principals.yaml',
    ),
}


def validate(text):
    """Raise ValueError unless text looks like a complete OpenAPI YAML document."""
    if not text.lstrip().startswith('openapi:'):
        raise ValueError('not an OpenAPI document (no leading "openapi:")')
    if not re.search(r'^paths:', text, re.MULTILINE):
        raise ValueError('no top-level "paths:" section')


def describe(text):
    """Return 'version X, N GET operations' for log output."""
    match = re.search(r'^  version: (\S+)', text, re.MULTILINE)
    version = match.group(1) if match and match.group(1) != 'null' else 'n/a'
    gets = len(re.findall(r'^    get:', text, re.MULTILINE))
    return f'version {version}, {gets} GET operations'


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'okta-skills-update-specs'})
    with urllib.request.urlopen(request, timeout=60) as resp:
        return resp.read().decode('utf-8')


def update(name):
    url, filename = SPECS[name]
    dest = REPO_ROOT / filename
    text = fetch(url)
    validate(text)
    data = text.encode('utf-8')
    previous = hashlib.sha256(dest.read_bytes()).digest() if dest.exists() else None
    if previous == hashlib.sha256(data).digest():
        status = 'unchanged'
    else:
        tmp = dest.with_name(dest.name + '.tmp')
        tmp.write_bytes(data)
        os.replace(tmp, dest)
        status = 'new' if previous is None else 'updated'
    print(f'{name}: {status} -> {filename} ({describe(text)})')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('names', nargs='*', metavar='name',
                        help=f'specs to download (default: all). One of: {", ".join(SPECS)}')
    parser.add_argument('--list', action='store_true', help='print the tracked specs and exit')
    args = parser.parse_args()
    unknown = [n for n in args.names if n not in SPECS]
    if unknown:
        parser.error(f'unknown spec(s): {", ".join(unknown)} (choose from: {", ".join(SPECS)})')

    if args.list:
        for name, (url, filename) in SPECS.items():
            print(f'{name}\t{filename}\t{url}')
        return

    failed = False
    for name in args.names or SPECS:
        try:
            update(name)
        except Exception as e:  # keep going so one bad spec doesn't block the others
            failed = True
            print(f'{name}: FAILED - {e}', file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
