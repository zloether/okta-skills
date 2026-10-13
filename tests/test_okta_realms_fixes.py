from unittest.mock import MagicMock

from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'


def _call(cmd, **kw):
    mod = import_script('okta-realms', 'realms.py')
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(mod, cmd)(session, BASE_URL, args(**{'limit': None, 'page_size': None, **kw}))
    return session.get.call_args[1]['params']


def test_realms_page_size_sent():
    p = _call('cmd_list_realms', search=None, sort_by=None, sort_order=None, page_size=150)
    assert p == {'limit': 150}


def test_realms_page_size_overrides_small_limit():
    p = _call('cmd_list_realms', search=None, sort_by=None, sort_order=None, limit=5, page_size=100)
    assert p == {'limit': 100}


def test_realm_assignments_page_size_sent():
    assert _call('cmd_list_realm_assignments', page_size=200) == {'limit': 200}


def test_realm_assignment_operations_page_size_sent():
    assert _call('cmd_list_realm_assignment_operations', page_size=25) == {'limit': 25}


def test_realms_no_limit_param_by_default():
    assert _call('cmd_list_realm_assignments') == {}
