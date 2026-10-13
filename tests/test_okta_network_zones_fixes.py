from unittest.mock import MagicMock

from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'


def _list(**kw):
    mod = import_script('okta-network-zones', 'network_zones.py')
    session = MagicMock()
    session.get.return_value = make_response([])
    mod.cmd_list(session, BASE_URL, args(**{'usage': None, 'system': None, 'limit': None, 'page_size': None, **kw}))
    return session.get.call_args[1]['params']


def test_zones_page_size_sent_as_limit():
    assert _list(page_size=100) == {'limit': 100}


def test_zones_limit_sent_as_page_size_when_no_page_size():
    assert _list(limit=5) == {'limit': 5}


def test_zones_no_limit_param_by_default():
    assert 'limit' not in _list()


def test_zones_page_size_combines_with_filter():
    assert _list(usage='POLICY', page_size=50) == {'filter': 'usage eq "POLICY"', 'limit': 50}
