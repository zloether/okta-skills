import importlib.util
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).parents[1] / 'scripts' / 'update-specs.py'
_spec = importlib.util.spec_from_file_location('update_specs', _SCRIPT_PATH)
us = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(us)

_VALID = 'openapi: 3.0.3\ninfo:\n  title: T\n  version: 2026.09.2\npaths:\n  /a:\n    get:\n      operationId: a\n  /b:\n    post:\n      operationId: b\n'


def test_validate_accepts_openapi_document():
    us.validate(_VALID)


@pytest.mark.parametrize('text', ['<html>404</html>', '', 'openapi: 3.0.3\ninfo:\n  title: T\n'])
def test_validate_rejects_non_spec_or_truncated(text):
    with pytest.raises(ValueError):
        us.validate(text)


def test_describe_reports_version_and_get_count():
    assert us.describe(_VALID) == 'version 2026.09.2, 1 GET operations'


def test_describe_handles_null_version():
    assert us.describe(_VALID.replace('2026.09.2', 'null')).startswith('version n/a')


def test_update_writes_new_then_reports_unchanged(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(us, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(us, 'SPECS', {'x': ('http://example/x.yaml', 'x.yaml')})
    monkeypatch.setattr(us, 'fetch', lambda url: _VALID)
    us.update('x')
    us.update('x')
    out = capsys.readouterr().out
    assert 'x: new' in out and 'x: unchanged' in out
    assert (tmp_path / 'x.yaml').read_text() == _VALID


def test_update_keeps_existing_file_when_download_invalid(tmp_path, monkeypatch):
    monkeypatch.setattr(us, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(us, 'SPECS', {'x': ('http://example/x.yaml', 'x.yaml')})
    (tmp_path / 'x.yaml').write_text(_VALID)
    monkeypatch.setattr(us, 'fetch', lambda url: '<html>oops</html>')
    with pytest.raises(ValueError):
        us.update('x')
    assert (tmp_path / 'x.yaml').read_text() == _VALID
