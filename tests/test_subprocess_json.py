"""Tests for shared/subprocess_json.py."""
import importlib.util
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SCRIPT_PATH = Path(__file__).parents[1] / 'shared' / 'subprocess_json.py'
_spec = importlib.util.spec_from_file_location('subprocess_json', _SCRIPT_PATH)
sj = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sj)


def test_run_script_json_returns_parsed_stdout_on_success():
    proc = MagicMock(returncode=0, stdout='{"id": "g1"}', stderr='')
    with patch('subprocess.run', return_value=proc) as run:
        result = sj.run_script_json(Path('some/script.py'), ['list'])
    assert result == {'id': 'g1'}
    assert run.call_args[0][0][0:2] == ['uv', 'run']
    assert run.call_args.kwargs['timeout'] == sj.DEFAULT_TIMEOUT


def test_run_script_json_passes_custom_timeout():
    proc = MagicMock(returncode=0, stdout='[]', stderr='')
    with patch('subprocess.run', return_value=proc) as run:
        sj.run_script_json(Path('some/script.py'), ['list'], timeout=5)
    assert run.call_args.kwargs['timeout'] == 5


def test_run_script_json_raises_immediately_on_genuine_script_failure_without_retry():
    proc = MagicMock(returncode=1, stdout='', stderr='{"error": "boom"}')
    with patch('subprocess.run', return_value=proc) as run, \
         pytest.raises(RuntimeError, match='boom'):
        sj.run_script_json(Path('some/script.py'), ['list'])
    run.assert_called_once()  # never falls back to the plain interpreter for a genuine script failure


def test_run_script_json_falls_back_on_uv_launch_failure_missing_binary():
    proc = MagicMock(returncode=0, stdout='[]', stderr='')
    with patch('subprocess.run', side_effect=[FileNotFoundError(), proc]) as run:
        result = sj.run_script_json(Path('some/script.py'), ['list'])
    assert result == []
    assert run.call_count == 2


def test_run_script_json_falls_back_on_uv_non_json_stderr():
    uv_proc = MagicMock(returncode=1, stdout='', stderr='error: could not initialize cache')
    py_proc = MagicMock(returncode=0, stdout='[]', stderr='')
    with patch('subprocess.run', side_effect=[uv_proc, py_proc]) as run:
        result = sj.run_script_json(Path('some/script.py'), ['list'])
    assert result == []
    assert run.call_count == 2
    assert run.call_args_list[1][0][0][0] != 'uv'


def test_run_script_json_raises_when_both_interpreters_fail():
    uv_proc = MagicMock(returncode=1, stdout='', stderr='error: uv broke')
    py_proc = MagicMock(returncode=1, stdout='', stderr='plain failure, not json')
    with patch('subprocess.run', side_effect=[uv_proc, py_proc]), \
         pytest.raises(RuntimeError, match='plain failure'):
        sj.run_script_json(Path('some/script.py'), ['list'])


def test_run_script_json_raises_when_neither_interpreter_launches():
    with patch('subprocess.run', side_effect=[FileNotFoundError(), FileNotFoundError()]), \
         pytest.raises(RuntimeError, match='neither "uv" nor'):
        sj.run_script_json(Path('some/script.py'), ['list'])


def test_run_script_json_propagates_timeout_expired():
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='uv', timeout=5)), \
         pytest.raises(subprocess.TimeoutExpired):
        sj.run_script_json(Path('some/script.py'), ['list'], timeout=5)
