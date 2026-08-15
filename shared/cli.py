"""Shared CLI entry point: parse args, open a session, dispatch, and report errors as JSON."""
import json
import sys

from okta_client import get_session


def run(parser, commands, before=None):
    """Parse args, dispatch to commands[args.command], and print the JSON result.

    `before(args, session, base_url)`, if given, runs inside the try block
    before dispatch and may mutate `args` (e.g. resolving a login to an ID).
    """
    args = parser.parse_args()
    session, base_url = get_session()
    try:
        if before:
            before(args, session, base_url)
        result = commands[args.command](session, base_url, args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)
