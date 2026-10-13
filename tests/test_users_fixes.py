from unittest.mock import MagicMock

from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'
users = import_script('okta-users', 'users.py')


def _list_args(**kw):
    d = {'filter': None, 'search': None, 'q': None, 'sort_by': None, 'sort_order': None, 'fields': None, 'expand': None, 'limit': None, 'page_size': None}
    d.update(kw)
    return args(**d)


def _params(session):
    return session.get.call_args[1]['params']


def test_list_without_limit_sends_no_limit_param():
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, _list_args())
    assert 'limit' not in _params(session)


def test_list_limit_sent_as_page_size_and_capped_at_200():
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, _list_args(limit=25))
    assert _params(session)['limit'] == 25
    users.cmd_list(session, BASE_URL, _list_args(limit=5000))
    assert _params(session)['limit'] == 200


def test_list_q_with_limit_sends_limit():
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, _list_args(q='jane', limit=50))
    assert _params(session) == {'q': 'jane', 'limit': 50}


def test_list_page_size_flag():
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, _list_args(page_size=100))
    assert _params(session)['limit'] == 100


def test_search_sends_limit_when_given():
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'a'}, {'id': 'b'}])
    result = users.cmd_search(session, BASE_URL, args(query='Jane', limit=1, page_size=None))
    assert _params(session) == {'q': 'Jane', 'limit': 1}
    assert len(result) == 1


def test_search_without_limit_sends_only_q():
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_search(session, BASE_URL, args(query='Jane', limit=None, page_size=None))
    assert _params(session) == {'q': 'Jane'}
