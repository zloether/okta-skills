"""Tests for shared/cli.py's run() entry point."""
import json
import sys
from unittest.mock import MagicMock, patch

import pytest
from cli import run


def _parser(argv):
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    sys.argv = argv
    return parser


def test_run_prints_json_result(capsys):
    parser = _parser(['prog', 'list'])
    commands = {'list': lambda session, base_url, args: {'ok': True}}
    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')):
        run(parser, commands)
    out = json.loads(capsys.readouterr().out)
    assert out == {'ok': True}


def test_run_calls_before_hook_and_can_mutate_args(capsys):
    parser = _parser(['prog', 'list'])

    def before(args, session, base_url):
        args.injected = 'value'

    commands = {'list': lambda session, base_url, args: {'injected': args.injected}}
    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')):
        run(parser, commands, before=before)
    out = json.loads(capsys.readouterr().out)
    assert out == {'injected': 'value'}


def test_run_dispatches_to_correct_command(capsys):
    parser = _parser(['prog', 'list'])
    commands = {'list': MagicMock(return_value={'called': 'list'})}
    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')):
        run(parser, commands)
    commands['list'].assert_called_once()
    out = json.loads(capsys.readouterr().out)
    assert out == {'called': 'list'}


def test_run_reports_exception_as_json_error_and_exits_1(capsys):
    parser = _parser(['prog', 'list'])

    def raises(session, base_url, args):
        raise RuntimeError('boom')

    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')), \
            pytest.raises(SystemExit) as exc_info:
        run(parser, {'list': raises})

    assert exc_info.value.code == 1
    err = json.loads(capsys.readouterr().err)
    assert err == {'error': 'boom'}


def test_run_before_hook_exception_reported_as_json_error(capsys):
    parser = _parser(['prog', 'list'])

    def before(args, session, base_url):
        raise ValueError('bad before')

    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')), \
            pytest.raises(SystemExit) as exc_info:
        run(parser, {'list': lambda s, b, a: {}}, before=before)

    assert exc_info.value.code == 1
    err = json.loads(capsys.readouterr().err)
    assert err == {'error': 'bad before'}


def test_run_get_session_error_reported_as_json_not_traceback(capsys, monkeypatch):
    """A get_session() failure (e.g. missing env vars) must go through the same
    JSON-error-and-exit(1) path as command errors, not raise an uncaught traceback."""
    parser = _parser(['prog', 'list'])
    monkeypatch.delenv('OKTA_CLIENT_ORGURL', raising=False)

    with pytest.raises(SystemExit) as exc_info:
        run(parser, {'list': lambda s, b, a: {}})

    assert exc_info.value.code == 1
    err = json.loads(capsys.readouterr().err)
    assert err == {'error': 'OKTA_CLIENT_ORGURL environment variable is not set'}


def _http_error(status, body=None):
    import requests
    resp = requests.Response()
    resp.status_code = status
    resp.url = 'https://example.okta.com/api/v1/x'
    resp._content = json.dumps(body or {}).encode()
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        return e


@pytest.mark.parametrize('status,expected', [(401, 'OKTA_CLIENT_SCOPES'), (403, 'missing OAuth scope')])
def test_run_auth_errors_include_hint_and_okta_summary(capsys, status, expected):
    parser = _parser(['prog', 'list'])
    exc = _http_error(status, {'errorSummary': 'Invalid token provided'})

    def raises(session, base_url, args):
        raise exc

    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')), \
            pytest.raises(SystemExit):
        run(parser, {'list': raises})

    msg = json.loads(capsys.readouterr().err)['error']
    assert str(status) in msg
    assert 'Okta: Invalid token provided' in msg
    assert expected in msg


def test_run_404_error_has_no_auth_hint(capsys):
    parser = _parser(['prog', 'list'])
    exc = _http_error(404)

    def raises(session, base_url, args):
        raise exc

    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')), \
            pytest.raises(SystemExit):
        run(parser, {'list': raises})

    assert 'OKTA_CLIENT_SCOPES' not in json.loads(capsys.readouterr().err)['error']


def test_run_strip_links_removes_nested_links(capsys):
    parser = _parser(['prog', 'list', '--strip-links'])
    result = [{'id': '1', '_links': {'self': {}}, 'child': {'_links': {}, 'x': 1}}]
    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')):
        run(parser, {'list': lambda s, b, a: result})
    assert json.loads(capsys.readouterr().out) == [{'id': '1', 'child': {'x': 1}}]


def test_run_select_keeps_only_dotted_paths(capsys):
    parser = _parser(['prog', 'list', '--select', 'id,profile.login,missing.path'])
    result = [{'id': '1', 'status': 'ACTIVE', 'profile': {'login': 'a@b.c', 'email': 'a@b.c'}}]
    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')):
        run(parser, {'list': lambda s, b, a: result})
    assert json.loads(capsys.readouterr().out) == [{'id': '1', 'profile': {'login': 'a@b.c'}}]
