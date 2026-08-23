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

    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')):
        with pytest.raises(SystemExit) as exc_info:
            run(parser, {'list': raises})

    assert exc_info.value.code == 1
    err = json.loads(capsys.readouterr().err)
    assert err == {'error': 'boom'}


def test_run_before_hook_exception_reported_as_json_error(capsys):
    parser = _parser(['prog', 'list'])

    def before(args, session, base_url):
        raise ValueError('bad before')

    with patch('cli.get_session', return_value=(MagicMock(), 'https://example.okta.com')):
        with pytest.raises(SystemExit) as exc_info:
            run(parser, {'list': lambda s, b, a: {}}, before=before)

    assert exc_info.value.code == 1
    err = json.loads(capsys.readouterr().err)
    assert err == {'error': 'bad before'}
