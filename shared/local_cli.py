"""Shared CLI entry point for scripts that never call the Okta API: parse args, dispatch, report errors as JSON."""
import json
import sys


def run_local(parser, dispatch):
    """Parse args, call dispatch(args) to get a JSON-serializable result, and print it.

    Mirrors shared/cli.py's run() for scripts that need no Okta session — dispatch does its
    own args.command branching and returns the result directly.
    """
    args = parser.parse_args()
    try:
        result = dispatch(args)
        print(json.dumps(result, indent=2))
    except Exception as e:  # noqa: BLE001 — top-level handler must turn any failure into a JSON error, not a traceback
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)
