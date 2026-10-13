"""okta-schemas: profile mapping list sends the spec's `limit`."""
from unittest.mock import MagicMock

import pytest
from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'


@pytest.fixture(scope='module')
def schemas():
    return import_script('okta-schemas', 'schemas.py')


def _call(schemas, **kw):
    s = MagicMock()
    s.get.return_value = make_response([])
    base = dict(source_id=None, target_id=None, limit=None, page_size=None)
    schemas.cmd_list(s, BASE_URL, args(**{**base, **kw}))
    return s.get.call_args[1].get('params') or {}


def test_mappings_page_size_sent_as_limit(schemas):
    assert _call(schemas, page_size=200)['limit'] == 200


def test_mappings_limit_alone_sent_as_page_size(schemas):
    assert _call(schemas, limit=5)['limit'] == 5


def test_mappings_no_limit_not_sent(schemas):
    assert 'limit' not in _call(schemas)


def test_mappings_limit_combines_with_filters(schemas):
    assert _call(schemas, source_id='oty1', page_size=10) == {'sourceId': 'oty1', 'limit': 10}
