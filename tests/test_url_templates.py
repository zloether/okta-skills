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


def _url_arg(call):
    """Return the URL argument of a fetch call, or None if the call isn't one."""
    func = call.func
    if isinstance(func, ast.Name) and func.id in _FETCHERS:
        index = 0 if func.id == 'build_url' else 1
    elif isinstance(func, ast.Attribute) and func.attr == 'get' and isinstance(func.value, ast.Name) and func.value.id == 'session':
        index = 0
    else:
        return None
    return call.args[index] if len(call.args) > index else None


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
