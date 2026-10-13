"""Guardrail: URLs passed to the Okta fetch helpers must be literal templates.

Path segments are percent-encoded by `okta_client.build_url` from `path_params`. An
f-string interpolating anything but `base_url`, a concatenation, or a `.format()`
call as the URL would bypass that and reintroduce path injection, so this fails on
any such call under skills/.
"""
import ast
from pathlib import Path

_SKILLS_DIR = Path(__file__).parents[1] / 'skills'
_FETCHERS = {'get_resource', 'paginated_get', 'paginated_get_wrapped', 'build_url'}


_HTTP_VERBS = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'request'}


def _looks_like_url(node):
    """Heuristic so `some_dict.get('key')` isn't mistaken for an HTTP call."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str) and '/' in node.value
    if isinstance(node, ast.JoinedStr):
        return any(isinstance(p, ast.Constant) and '/' in p.value for p in node.values)
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'build_url'


def _url_arg(call):
    """Return the URL argument of a fetch call, or None if the call isn't one."""
    func = call.func
    if isinstance(func, ast.Name) and func.id in _FETCHERS:
        index, keyword = (0, 'template') if func.id == 'build_url' else (1, 'url')
    elif isinstance(func, ast.Attribute) and func.attr in _HTTP_VERBS:
        index, keyword = (1, 'url') if func.attr == 'request' else (0, 'url')
    else:
        return None
    if len(call.args) > index:
        arg = call.args[index]
    else:
        arg = next((kw.value for kw in call.keywords if kw.arg == keyword), None)
    if isinstance(func, ast.Attribute) and arg is not None:
        http_receiver = isinstance(func.value, ast.Name) and func.value.id in {'session', 'requests'}
        if not (http_receiver or _looks_like_url(arg)):
            return None
    return arg


def _is_literal(node):
    """A string literal, a `build_url(...)` call (checked on its own), or an f-string interpolating only the bare `base_url`."""
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id == 'build_url'
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    return isinstance(node, ast.JoinedStr) and all(
        isinstance(part, ast.Constant)
        or (isinstance(part.value, ast.Name) and part.value.id == 'base_url' and part.format_spec is None)
        for part in node.values
    )


def _offending(source):
    return [
        n for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call) and (u := _url_arg(n)) is not None and not _is_literal(u)
    ]


def test_guardrail_catches_bypasses():
    bad = [
        "paginated_get(session=session, url=f'{base_url}/x/{args.id}')",
        "s.get(f'{base_url}/x/{args.id}')",
        "session.post(f'{base_url}/x/{args.id}/lifecycle')",
        "get_resource(session, '{base}/x/{id}'.format(id=args.id))",
        "session.get(build_url(f'{base_url}/x/{args.id}'))",
    ]
    for src in bad:
        assert _offending(src), src
    good = [
        "get_resource(session, '{base}/x/{id}', path_params={})",
        "session.get(build_url('{base}/x/{id}', {}))",
        "config.get('key')",
        "data.get(name)",
    ]
    for src in good:
        assert not _offending(src), src


def test_fetch_urls_are_literal_templates():
    offenders = []
    for script in sorted(_SKILLS_DIR.glob('*/scripts/*.py')):
        for node in ast.walk(ast.parse(script.read_text())):
            if isinstance(node, ast.Call):
                url = _url_arg(node)
                if url is not None and not _is_literal(url):
                    offenders.append(f'{script.relative_to(_SKILLS_DIR)}:{node.lineno}')
    assert not offenders, (
        'URL must be a string literal template with path_params (see okta_client.build_url):\n'
        + '\n'.join(offenders)
    )
