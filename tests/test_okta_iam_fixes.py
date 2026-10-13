"""okta-iam: `limit` is sent only where the spec defines it; --limit stays a client-side cap."""
from unittest.mock import MagicMock

import pytest
from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'


@pytest.fixture(scope='module')
def iam():
    return import_script('okta-iam', 'iam.py')


def _session(key):
    session = MagicMock()
    session.get.return_value = make_response({key: [{'id': 'a'}, {'id': 'b'}, {'id': 'c'}]})
    return session


def _params(s):
    return s.get.call_args[1].get('params') or {}


@pytest.mark.parametrize('cmd,key,kw', [
    ('cmd_list_assignees', 'value', {}),
    ('cmd_list_resources', 'resources', dict(resource_set_id='rs1')),
    ('cmd_list_bundles', 'bundles', {}),
    ('cmd_list_bundle_entitlements', 'entitlements', dict(bundle_id='b1')),
    ('cmd_list_bundle_entitlement_values', 'entitlementValues', dict(bundle_id='b1', entitlement_id='e1')),
])
def test_limit_capable_commands_send_page_size(iam, cmd, key, kw):
    s = _session(key)
    getattr(iam, cmd)(s, BASE_URL, args(limit=None, page_size=25, **kw))
    assert _params(s)['limit'] == 25


def test_limit_alone_is_sent_as_page_size(iam):
    s = _session('bundles')
    iam.cmd_list_bundles(s, BASE_URL, args(limit=7, page_size=None))
    assert _params(s)['limit'] == 7


@pytest.mark.parametrize('cmd,key,kw', [
    ('cmd_list', 'roles', {}),
    ('cmd_list_resource_sets', 'resource-sets', {}),
    ('cmd_list_bindings', 'roles', dict(resource_set_id='rs1')),
    ('cmd_list_binding_members', 'members', dict(resource_set_id='rs1', role_id='r1')),
])
def test_no_limit_endpoints_never_send_limit_but_cap_client_side(iam, cmd, key, kw):
    s = _session(key)
    result = getattr(iam, cmd)(s, BASE_URL, args(limit=2, **kw))
    assert 'limit' not in _params(s)
    assert len(result) == 2


def test_wrapped_pagination_follows_body_links_next(iam):
    s = MagicMock()
    first = make_response({'roles': [{'id': 'a'}], '_links': {'next': {'href': f'{BASE_URL}/api/v1/iam/roles?after=x'}}})
    second = make_response({'roles': [{'id': 'b'}]})
    s.get.side_effect = [first, second]
    assert iam.cmd_list(s, BASE_URL, args(limit=None)) == [{'id': 'a'}, {'id': 'b'}]
