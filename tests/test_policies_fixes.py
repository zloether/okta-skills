from unittest.mock import MagicMock

from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'
policies = import_script('okta-policies', 'policies.py')


def _list_args(**kw):
    d = {'type': 'OKTA_SIGN_ON', 'status': None, 'q': None, 'expand': None, 'sort_by': None, 'resource_id': None, 'limit': None, 'page_size': None}
    d.update(kw)
    return args(**d)


def _get(session):
    return session.get.call_args[1]['params']


def test_list_without_limit_sends_no_limit_param():
    session = MagicMock()
    session.get.return_value = make_response([])
    policies.cmd_list(session, BASE_URL, _list_args())
    assert 'limit' not in _get(session)


def test_list_limit_is_sent_as_page_size():
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'a'}, {'id': 'b'}])
    result = policies.cmd_list(session, BASE_URL, _list_args(limit=1))
    assert _get(session)['limit'] == 1
    assert len(result) == 1


def test_list_page_size_overrides_limit():
    session = MagicMock()
    session.get.return_value = make_response([])
    policies.cmd_list(session, BASE_URL, _list_args(limit=500, page_size=50))
    assert _get(session)['limit'] == 50


def test_get_rules_limit_sent_and_truncates():
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'r1'}, {'id': 'r2'}])
    result = policies.cmd_get_rules(session, BASE_URL, args(id=['p1'], summary=False, limit=1, page_size=None))
    assert _get(session)['limit'] == 1
    assert [r['id'] for r in result] == ['r1']


def test_get_rules_without_limit_sends_no_limit():
    session = MagicMock()
    session.get.return_value = make_response([])
    policies.cmd_get_rules(session, BASE_URL, args(id=['p1'], summary=False, limit=None, page_size=None))
    assert 'limit' not in (_get(session) or {})
