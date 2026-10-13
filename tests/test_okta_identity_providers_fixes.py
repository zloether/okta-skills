"""Page-size tests for okta-identity-providers."""
from unittest.mock import MagicMock

import pytest
from conftest import args, make_response
from test_scripts import BASE_URL, import_script


@pytest.fixture
def idps():
    return import_script('okta-identity-providers', 'identity_providers.py')


def _params(session):
    return session.get.call_args.kwargs['params']


_CASES = [
    ('cmd_list', {'q': None, 'type': None}),
    ('cmd_list_keys', {}),
    ('cmd_list_users', {'idp_id': 'i', 'q': None, 'expand': None}),
]


@pytest.mark.parametrize('fn,extra', _CASES)
def test_page_size_sent_as_limit(idps, fn, extra):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(idps, fn)(session, BASE_URL, args(**extra, limit=None, page_size=50))
    assert _params(session)['limit'] == 50


@pytest.mark.parametrize('fn,extra', _CASES)
def test_limit_caps_page_size_at_200(idps, fn, extra):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(idps, fn)(session, BASE_URL, args(**extra, limit=999, page_size=None))
    assert _params(session)['limit'] == 200


@pytest.mark.parametrize('fn,extra', _CASES)
def test_no_limit_param_when_unset(idps, fn, extra):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(idps, fn)(session, BASE_URL, args(**extra, limit=None, page_size=None))
    assert 'limit' not in (session.get.call_args.kwargs.get('params') or {})


@pytest.mark.parametrize('fn', ['cmd_list_csrs', 'cmd_list_signing_keys'])
def test_endpoints_without_limit_param_never_send_it(idps, fn):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(idps, fn)(session, BASE_URL, args(idp_id='i', limit=50, page_size=None))
    assert 'limit' not in (session.get.call_args.kwargs.get('params') or {})
