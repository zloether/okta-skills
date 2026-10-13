from unittest.mock import MagicMock

from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'


def _call(cmd, **kw):
    mod = import_script('okta-oauth-client-roles', 'oauth_client_roles.py')
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(mod, cmd)(
        session, BASE_URL,
        args(**{'client_id': '0oa1', 'role_assignment_id': 'r1', 'limit': None, 'page_size': None, **kw}),
    )
    return session.get.call_args[1]['params']


def test_app_targets_page_size_sent():
    assert _call('cmd_list_app_targets', page_size=200) == {'limit': 200}


def test_group_targets_page_size_sent():
    assert _call('cmd_list_group_targets', page_size=50) == {'limit': 50}


def test_targets_limit_used_as_page_size():
    assert _call('cmd_list_group_targets', limit=7) == {'limit': 7}


def test_targets_no_limit_param_by_default():
    assert _call('cmd_list_app_targets') == {}
