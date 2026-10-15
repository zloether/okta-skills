"""okta-groups: `limit` is sent only to endpoints whose spec defines it."""
from unittest.mock import MagicMock

import pytest
from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'


@pytest.fixture(scope='module')
def groups():
    return import_script('okta-groups', 'groups.py')


def _params(call):
    return call.get.call_args[1].get('params') or {}


def _session():
    session = MagicMock()
    session.get.return_value = make_response([])
    return session


def _list_args(**kw):
    base = {'filter': None, 'search': None, 'q': None, 'expand': None, 'sort_by': None,
                'sort_order': None, 'limit': None, 'page_size': None}
    return args(**{**base, **kw})


def test_list_sends_page_size_as_limit(groups):
    s = _session()
    groups.cmd_list(s, BASE_URL, _list_args(page_size=5000))
    assert _params(s)['limit'] == 5000


def test_list_limit_alone_sets_page_size_capped_at_10000(groups):
    s = _session()
    groups.cmd_list(s, BASE_URL, _list_args(limit=20000))
    assert _params(s)['limit'] == 10000


def test_list_with_q_does_not_send_limit(groups):
    s = _session()
    groups.cmd_list(s, BASE_URL, _list_args(q='Eng', page_size=100))
    assert 'limit' not in _params(s)


def test_list_without_limit_sends_none(groups):
    s = _session()
    groups.cmd_list(s, BASE_URL, _list_args())
    assert 'limit' not in _params(s)


@pytest.mark.parametrize('cmd,kw', [
    ('cmd_get_members', {'id': 'g1'}),
    ('cmd_get_apps', {'id': 'g1'}),
    ('cmd_get_owners', {'id': 'g1', 'search': None}),
    ('cmd_list_rules', {'search': None, 'expand': None}),
])
def test_limit_capable_commands_send_page_size(groups, cmd, kw):
    s = _session()
    getattr(groups, cmd)(s, BASE_URL, args(limit=None, page_size=50, **kw))
    assert _params(s)['limit'] == 50


@pytest.mark.parametrize('cmd', ['cmd_list_role_app_targets', 'cmd_list_role_group_targets'])
def test_role_target_commands_never_send_limit(groups, cmd):
    s = _session()
    getattr(groups, cmd)(s, BASE_URL, args(id='g1', role_id='r1', limit=5))
    assert 'limit' not in _params(s)


def test_groups_search_requires_a_query(groups):
    with pytest.raises(ValueError, match='provide a search query'):
        groups.cmd_search(_session(), BASE_URL, args(query=None, q_flag=None, limit=None))
