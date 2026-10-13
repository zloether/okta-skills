"""Page-size and resource-server-keys unwrap tests for okta-authorization-servers."""
from unittest.mock import MagicMock

import pytest
from conftest import args, make_response
from test_scripts import BASE_URL, import_script


@pytest.fixture
def aus():
    return import_script('okta-authorization-servers', 'authorization_servers.py')


def _params(session):
    return session.get.call_args.kwargs['params']


_CASES = [
    ('cmd_list', dict(q=None)),
    ('cmd_list_associated_servers', dict(id='a', trusted=None, q=None)),
    ('cmd_list_tokens', dict(id='a', client_id='c', expand=None)),
    ('cmd_list_scopes', dict(id='a', q=None, filter=None)),
]


@pytest.mark.parametrize('fn,extra', _CASES)
def test_page_size_sent_as_limit(aus, fn, extra):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(aus, fn)(session, BASE_URL, args(**extra, limit=None, page_size=100))
    assert _params(session)['limit'] == 100


@pytest.mark.parametrize('fn,extra', _CASES)
def test_limit_caps_page_size_at_200(aus, fn, extra):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(aus, fn)(session, BASE_URL, args(**extra, limit=999, page_size=None))
    assert _params(session)['limit'] == 200


@pytest.mark.parametrize('fn,extra', _CASES)
def test_no_limit_param_when_unset(aus, fn, extra):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(aus, fn)(session, BASE_URL, args(**extra, limit=None, page_size=None))
    assert 'limit' not in _params(session)


@pytest.mark.parametrize('fn,extra', [
    ('cmd_list_claims', dict(id='a')),
    ('cmd_list_clients', dict(id='a')),
    ('cmd_list_keys', dict(id='a')),
    ('cmd_list_policies', dict(id='a')),
    ('cmd_list_policy_rules', dict(id='a', policy_id='p')),
])
def test_endpoints_without_limit_param_never_send_it(aus, fn, extra):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(aus, fn)(session, BASE_URL, args(**extra, limit=50, page_size=None))
    params = session.get.call_args.kwargs.get('params') or {}
    assert 'limit' not in params


def test_resource_server_keys_unwraps_keys_object(aus):
    session = MagicMock()
    session.get.return_value = make_response({'keys': [{'kid': 'k1'}, {'kid': 'k2'}]})
    assert aus.cmd_list_resource_server_keys(session, BASE_URL, args(id='a', limit=None)) == [
        {'kid': 'k1'}, {'kid': 'k2'}
    ]


def test_resource_server_keys_applies_limit_and_handles_null(aus):
    session = MagicMock()
    session.get.return_value = make_response({'keys': [{'kid': 'k1'}, {'kid': 'k2'}]})
    assert aus.cmd_list_resource_server_keys(session, BASE_URL, args(id='a', limit=1)) == [{'kid': 'k1'}]
    session.get.return_value = make_response({'keys': None})
    assert aus.cmd_list_resource_server_keys(session, BASE_URL, args(id='a', limit=None)) == []
