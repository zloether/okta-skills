"""Tests for shared/local_cli.py's run_local() entry point."""
import argparse
import json
import sys

import pytest
from local_cli import run_local


def _parser(argv):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('go')
    sys.argv = argv
    return parser


def test_run_local_prints_json_result(capsys):
    run_local(_parser(['prog', 'go']), lambda args: {'command': args.command})
    assert json.loads(capsys.readouterr().out) == {'command': 'go'}


def test_run_local_reports_exception_as_json_error_and_exits_1(capsys):
    def boom(args):
        raise RuntimeError('bad')

    with pytest.raises(SystemExit) as exc:
        run_local(_parser(['prog', 'go']), boom)
    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().err) == {'error': 'bad'}
