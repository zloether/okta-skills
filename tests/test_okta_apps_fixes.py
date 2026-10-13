"""Page-size and jwks-unwrap tests for okta-apps."""
from unittest.mock import MagicMock

import pytest
from conftest import args, make_response
from test_scripts import BASE_URL, import_script


@pytest.fixture
def apps():
    return import_script('okta-apps', 'apps.py')


def _params(session):
    return session.get.call_args.kwargs['params']


_BASE = dict(limit=None, page_size=None)

# (function, extra args, spec max)
_CASES = [
    ('cmd_list', dict(filter=None, q=None, expand=None, use_optimization=False,
                     always_include_vpn_settings=False, include_non_deleted=False), 200),
    ('cmd_get_users', dict(id='a', q=None, expand=None), 500),
    ('cmd_get_groups', dict(id='a', q=None, expand=None), 200),
    ('cmd_list_tokens', dict(id='a', expand=None), 200),
    ('cmd_list_cwo_connections', dict(
        id='a', status=None, requesting_app_id=None, resource_app_id=None, active_apps_only=False,
        requesting_app_name=None, resource_app_name=None), 200),
    ('cmd_list_group_push_mappings', dict(id='a', last_updated=None, source_group_id=None, status=None), 1000),
]


@pytest.mark.parametrize('fn,extra,maximum', _CASES)
def test_page_size_sent_as_limit(apps, fn, extra, maximum):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(apps, fn)(session, BASE_URL, args(**extra, limit=None, page_size=maximum))
    assert _params(session)['limit'] == maximum


@pytest.mark.parametrize('fn,extra,maximum', _CASES)
def test_limit_caps_page_size_at_spec_max(apps, fn, extra, maximum):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(apps, fn)(session, BASE_URL, args(**extra, limit=maximum + 5000, page_size=None))
    assert _params(session)['limit'] == maximum


@pytest.mark.parametrize('fn,extra,maximum', _CASES)
def test_no_limit_param_when_unset(apps, fn, extra, maximum):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(apps, fn)(session, BASE_URL, args(**extra, **_BASE))
    assert 'limit' not in _params(session)


@pytest.mark.parametrize('fn', [
    'cmd_list_features', 'cmd_list_csrs', 'cmd_list_keys', 'cmd_list_secrets', 'cmd_list_grants',
    'cmd_list_federated_claims',
])
def test_endpoints_without_limit_param_never_send_it(apps, fn):
    session = MagicMock()
    session.get.return_value = make_response([])
    getattr(apps, fn)(session, BASE_URL, args(id='a', expand=None, limit=50, page_size=None))
    params = session.get.call_args.kwargs.get('params') or {}
    assert 'limit' not in params


def test_list_jwks_unwraps_keys_object(apps):
    session = MagicMock()
    session.get.return_value = make_response({'keys': [{'kid': 'k1'}]})
    assert apps.cmd_list_jwks(session, BASE_URL, args(id='a')) == [{'kid': 'k1'}]


def test_list_jwks_null_keys_returns_empty_list(apps):
    session = MagicMock()
    session.get.return_value = make_response({'keys': None})
    assert apps.cmd_list_jwks(session, BASE_URL, args(id='a')) == []
