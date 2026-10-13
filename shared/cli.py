"""Shared CLI entry point: parse args, open a session, dispatch, and report errors as JSON."""
import json
import sys

import requests
from okta_client import get_session

STREAMED = object()  # return from a command that has already printed its own output

_AUTH_HINT = {
    401: 'Unauthorized: the token/credentials are invalid or expired, the OAuth app was not granted the scope this endpoint needs (check OKTA_CLIENT_SCOPES and the app\'s granted scopes), or the feature is not enabled for this org (see the Okta message above).',
    403: 'Forbidden: the token is valid but lacks permission for this endpoint — a missing OAuth scope (okta.<resource>.read) or an admin role that does not cover this resource.',
}


def _error_message(exc):
    """Turn an HTTPError into a message that includes Okta's error body and, for
    401/403, a hint about the likely cause. Other exceptions pass through as str()."""
    resp = getattr(exc, 'response', None)
    if not isinstance(exc, requests.HTTPError) or resp is None:
        return str(exc)
    msg = str(exc)
    try:
        summary = resp.json().get('errorSummary')
    except (ValueError, AttributeError):
        summary = None
    if summary:
        msg += f' — Okta: {summary}'
    if resp.status_code in _AUTH_HINT:
        msg += f' — {_AUTH_HINT[resp.status_code]}'
    return msg


def _strip_links(obj):
    if isinstance(obj, dict):
        return {k: _strip_links(v) for k, v in obj.items() if k != '_links'}
    if isinstance(obj, list):
        return [_strip_links(v) for v in obj]
    return obj


def _pick(item, paths):
    """Keep only the dotted `paths` from a dict, preserving nesting (a.b -> {'a': {'b': ...}})."""
    if not isinstance(item, dict):
        return item
    out = {}
    for path in paths:
        src, dst = item, out
        keys = path.split('.')
        for i, key in enumerate(keys):
            if not isinstance(src, dict) or key not in src:
                break
            if i == len(keys) - 1:
                dst[key] = src[key]
            else:
                src = src[key]
                dst = dst.setdefault(key, {})
    return out


class KeyedResults(dict):
    """A {identifier: result} batch response; --select applies to each value, not the outer keys."""


def _select(result, paths):
    if isinstance(result, KeyedResults):
        return {k: v if isinstance(v, dict) and 'error' in v else _select(v, paths) for k, v in result.items()}
    if isinstance(result, list):
        return [_pick(item, paths) for item in result]
    return _pick(result, paths)


def apply_output_options(args, result):
    """Apply --strip-links and --select to a result (also used by commands that stream their own output)."""
    if args.strip_links:
        result = _strip_links(result)
    if args.select:
        result = _select(result, [p.strip() for p in args.select.split(',') if p.strip()])
    return result


def _add_output_options(parser):
    """Add --select/--strip-links to every subcommand so large responses can be trimmed."""
    for action in parser._actions:
        if isinstance(getattr(action, 'choices', None), dict):
            for sub in action.choices.values():
                sub.add_argument('--select', help='Comma-separated dotted field paths to keep from each result (e.g. id,profile.login,status); drops everything else')
                sub.add_argument('--strip-links', action='store_true', help='Remove all "_links" keys from the output')


def add_page_size(parser, maximum=200):
    """Add --page-size for endpoints whose spec defines a `limit` query param (max `maximum`)."""
    parser.add_argument(
        '--page-size', type=int, choices=range(1, maximum + 1), metavar=f'1-{maximum}',
        help='Items per API request (--limit alone only truncates results client-side)',
    )


def with_page_size(params, args, maximum=200):
    """Set `limit` in `params` from --page-size, else from --limit (so a small --limit doesn't fetch a full page).

    Only call for endpoints whose spec defines a `limit` query param.
    """
    size = args.page_size or (min(args.limit, maximum) if (getattr(args, 'limit', None) or 0) > 0 else None)
    if size:
        params['limit'] = size
    return params


def run(parser, commands, before=None):
    """Parse args, dispatch to commands[args.command], and print the JSON result.

    `before(args, session, base_url)`, if given, runs inside the try block
    before dispatch and may mutate `args` (e.g. resolving a login to an ID).
    """
    _add_output_options(parser)
    args = parser.parse_args()
    try:
        session, base_url = get_session()
        if before:
            before(args, session, base_url)
        result = commands[args.command](session, base_url, args)
        if result is STREAMED:  # command already wrote its own output (e.g. --jsonl)
            return
        print(json.dumps(apply_output_options(args, result), indent=2))
    except Exception as e:  # noqa: BLE001 — top-level handler must turn any failure into a JSON error, not a traceback
        print(json.dumps({'error': _error_message(e)}), file=sys.stderr)
        sys.exit(1)
