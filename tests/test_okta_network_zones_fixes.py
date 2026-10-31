from unittest.mock import MagicMock

from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'


def _list(**kw):
    mod = import_script('okta-network-zones', 'network_zones.py')
    session = MagicMock()
    session.get.return_value = make_response([])
    mod.cmd_list(session, BASE_URL, args(**{'usage': None, 'system': None, 'limit': None, 'page_size': None, 'cidrs': False, **kw}))
    return session.get.call_args[1]['params']


def test_zones_cidrs_normalizes_ip_zones_and_drops_dynamic():
    mod = import_script('okta-network-zones', 'network_zones.py')
    session = MagicMock()
    session.get.return_value = make_response([
        {'id': 'nzo1', 'name': 'office', 'type': 'IP', 'usage': 'POLICY', 'status': 'ACTIVE',
         'gateways': [
             {'type': 'CIDR', 'value': '10.0.0.0/24'},
             {'type': 'CIDR', 'value': '192.0.2.7'},
             {'type': 'RANGE', 'value': '198.51.100.9-198.51.100.9'},
             {'type': 'RANGE', 'value': '203.0.113.0-203.0.113.5'},
             {'type': 'CIDR', 'value': '2001:db8::/32'},
         ],
         'proxies': None},
        {'id': 'nzo2', 'name': 'USA', 'type': 'DYNAMIC', 'usage': 'POLICY', 'status': 'ACTIVE'},
    ])
    out = mod.cmd_list(session, BASE_URL, args(usage=None, system=None, limit=None, page_size=None, cidrs=True))
    assert out == [{
        'id': 'nzo1', 'name': 'office', 'usage': 'POLICY', 'status': 'ACTIVE',
        'gateways': ['10.0.0.0/24', '192.0.2.7/32', '198.51.100.9/32', '203.0.113.0/30', '203.0.113.4/31', '2001:db8::/32'],
        'proxies': [],
    }]


def test_zones_cidrs_reports_unparseable_entries_without_failing():
    mod = import_script('okta-network-zones', 'network_zones.py')
    session = MagicMock()
    session.get.return_value = make_response([
        {'id': 'nzo1', 'name': 'odd', 'type': 'IP', 'usage': 'POLICY', 'status': 'ACTIVE',
         'gateways': [
             {'type': 'RANGE', 'value': '198.51.100.9-198.51.100.1'},
             {'type': 'RANGE', 'value': '192.0.2.1-2001:db8::1'},
             {'type': 'CIDR', 'value': 'not-an-ip'},
             {'type': 'CIDR'},
             {'type': 'RANGE', 'value': '10.0.0.1'},
             {'type': 'CIDR', 'value': '10.0.0.77/24'},
         ],
         'proxies': [{'type': 'CIDR', 'value': '192.0.2.0/24'}, {'type': 'CIDR', 'value': 'bad'}]},
    ])
    out = mod.cmd_list(session, BASE_URL, args(usage=None, system=None, limit=None, page_size=None, cidrs=True))
    assert out[0]['gateways'] == ['10.0.0.0/24']
    assert out[0]['proxies'] == ['192.0.2.0/24']
    assert out[0]['unparsed'] == {
        'gateways': ['198.51.100.9-198.51.100.1', '192.0.2.1-2001:db8::1', 'not-an-ip', '', '10.0.0.1'],
        'proxies': ['bad'],
    }


def test_zones_cidrs_limit_counts_ip_zones_only():
    mod = import_script('okta-network-zones', 'network_zones.py')
    session = MagicMock()
    session.get.return_value = make_response([
        {'id': 'nzo0', 'type': 'DYNAMIC'},
        {'id': 'nzo1', 'type': 'IP', 'gateways': None},
        {'id': 'nzo2', 'type': 'IP', 'gateways': None},
    ])
    out = mod.cmd_list(session, BASE_URL, args(usage=None, system=None, limit=1, page_size=None, cidrs=True))
    assert [z['id'] for z in out] == ['nzo1']
    assert 'limit' not in session.get.call_args[1]['params']


def test_zones_page_size_sent_as_limit():
    assert _list(page_size=100) == {'limit': 100}


def test_zones_limit_sent_as_page_size_when_no_page_size():
    assert _list(limit=5) == {'limit': 5}


def test_zones_no_limit_param_by_default():
    assert 'limit' not in _list()


def test_zones_page_size_combines_with_filter():
    assert _list(usage='POLICY', page_size=50) == {'filter': 'usage eq "POLICY"', 'limit': 50}
