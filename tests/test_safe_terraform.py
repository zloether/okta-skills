"""Tests for skills/okta-terraform/scripts/safe_terraform.py."""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SCRIPT_PATH = Path(__file__).parents[1] / 'skills' / 'okta-terraform' / 'scripts' / 'safe_terraform.py'
_spec = importlib.util.spec_from_file_location('safe_terraform', _SCRIPT_PATH)
st = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(st)


# ---------------------------------------------------------------------------
# check_allowed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('args', [
    ['plan', '-chdir=path'],
    ['validate', '-chdir=path'],
    ['fmt', '-chdir=path'],
    ['show', '-json', '-chdir=path'],
    ['init', '-chdir=path'],
    ['state', 'list', '-chdir=path'],
    ['state', 'show', 'okta_group.eng', '-chdir=path'],
])
def test_check_allowed_permits_read_only_operations(args):
    st.check_allowed(args)  # must not raise


@pytest.mark.parametrize('args', [
    ['apply', '-chdir=path'],
    ['apply', '-auto-approve', '-chdir=path'],
    ['import', 'okta_group.eng', 'g1'],
    ['destroy', '-chdir=path'],
    ['state', 'mv', 'a', 'b'],
    ['state', 'rm', 'okta_group.eng'],
    ['taint', 'okta_group.eng'],
    ['force-unlock', 'lock-id'],
])
def test_check_allowed_rejects_mutating_operations(args):
    with pytest.raises(ValueError):
        st.check_allowed(args)


def test_check_allowed_rejects_no_subcommand():
    with pytest.raises(ValueError, match='no terraform subcommand'):
        st.check_allowed(['-chdir=path'])


def test_check_allowed_rejects_unknown_state_subcommand():
    with pytest.raises(ValueError, match='terraform state mv'):
        st.check_allowed(['state', 'mv', 'a', 'b'])


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def test_main_refuses_apply_without_invoking_terraform():
    with patch('sys.argv', ['safe_terraform.py', 'apply']), \
         patch('subprocess.run') as run, \
         pytest.raises(SystemExit) as exc_info:
        st.main()
    run.assert_not_called()
    assert exc_info.value.code == 1


def test_main_runs_terraform_for_allowed_subcommand():
    proc = MagicMock(returncode=0)
    with patch('sys.argv', ['safe_terraform.py', 'plan', '-chdir=path']), \
         patch('subprocess.run', return_value=proc) as run, \
         pytest.raises(SystemExit) as exc_info:
        st.main()
    run.assert_called_once_with(['terraform', 'plan', '-chdir=path'], check=False, timeout=300)
    assert exc_info.value.code == 0
