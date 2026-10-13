"""okta-org-settings: yubikey token list sends the spec's `limit`."""
from unittest.mock import MagicMock

import pytest
from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'


@pytest.fixture(scope='module')
def org_settings():
    return import_script('okta-org-settings', 'org_settings.py')


def _call(org_settings, **kw):
    s = MagicMock()
    s.get.return_value = make_response([])
    base = dict(filter=None, limit=None, page_size=None, expand_user=False, sort_by=None, sort_order=None)
    org_settings.cmd_list_yubikey_tokens(s, BASE_URL, args(**{**base, **kw}))
    return s.get.call_args[1].get('params') or {}


def test_yubikey_page_size_sent_as_limit(org_settings):
    assert _call(org_settings, page_size=100)['limit'] == 100


def test_yubikey_limit_alone_sent_as_page_size_capped(org_settings):
    assert _call(org_settings, limit=500)['limit'] == 200


def test_yubikey_no_limit_not_sent(org_settings):
    assert 'limit' not in _call(org_settings)
