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


def test_validate_rejects_unparseable_yaml_with_valid_headers():
    pytest.importorskip('yaml')
    with pytest.raises(ValueError, match='invalid YAML'):
        us.validate(_VALID + '  /c:\n    get: [unclosed\n')


def test_update_removes_tmp_file_when_replace_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(us, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(us, 'SPECS', {'x': ('http://example/x.yaml', 'x.yaml')})
    monkeypatch.setattr(us, 'fetch', lambda url: _VALID)

    def boom(src, dst):
        raise OSError('disk full')

    monkeypatch.setattr(us.os, 'replace', boom)
    with pytest.raises(OSError):
        us.update('x')
    assert list(tmp_path.iterdir()) == []


def test_validate_rejects_non_mapping_parse(monkeypatch):
    pytest.importorskip('yaml')
    with pytest.raises(ValueError, match='non-empty "paths"'):
        us.validate('openapi: 3.0.3\npaths:\n')


def test_describe_counts_zero_gets_without_version():
    assert us.describe('openapi: 3.0.3\npaths:\n') == 'version n/a, 0 GET operations'


def test_fetch_sends_user_agent_and_decodes_body(monkeypatch):
    seen = {}

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return 'héllo'.encode()

    def fake_urlopen(request, timeout):
        seen['ua'] = request.get_header('User-agent')
        seen['url'] = request.full_url
        return Resp()

    monkeypatch.setattr(us.urllib.request, 'urlopen', fake_urlopen)
    assert us.fetch('http://example/x.yaml') == 'héllo'
    assert seen == {'ua': 'okta-skills-update-specs', 'url': 'http://example/x.yaml'}


def test_update_reports_updated_when_content_changes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(us, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(us, 'SPECS', {'x': ('http://example/x.yaml', 'x.yaml')})
    (tmp_path / 'x.yaml').write_text('old')
    monkeypatch.setattr(us, 'fetch', lambda url: _VALID)
    us.update('x')
    assert 'x: updated' in capsys.readouterr().out
    assert (tmp_path / 'x.yaml').read_text() == _VALID


def _run_main(monkeypatch, *argv):
    monkeypatch.setattr('sys.argv', ['update-specs.py', *argv])
    with pytest.raises(SystemExit) as exc:
        us.main()
    return exc.value.code


def test_main_list_prints_specs_without_downloading(monkeypatch, capsys):
    monkeypatch.setattr(us, 'update', lambda name: pytest.fail('should not download'))
    monkeypatch.setattr('sys.argv', ['update-specs.py', '--list'])
    us.main()
    out = capsys.readouterr().out
    assert 'management\tmanagement-minimal.yaml\t' in out and 'workload-principals' in out


def test_main_rejects_unknown_spec_name(monkeypatch, capsys):
    assert _run_main(monkeypatch, 'bogus') == 2
    assert 'unknown spec(s): bogus' in capsys.readouterr().err


def test_main_exits_1_but_keeps_going_when_one_spec_fails(monkeypatch, capsys):
    calls = []

    def fake_update(name):
        calls.append(name)
        if name == 'management':
            raise OSError('network down')

    monkeypatch.setattr(us, 'update', fake_update)
    assert _run_main(monkeypatch) == 1
    assert calls == list(us.SPECS)
    assert 'management: FAILED - network down' in capsys.readouterr().err


def test_main_exits_0_when_all_specs_succeed(monkeypatch):
    monkeypatch.setattr(us, 'update', lambda name: None)
    assert _run_main(monkeypatch, 'management') == 0
