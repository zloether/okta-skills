"""diagnose_login.py: policy-tree walk against canned API responses (no network)."""
from unittest.mock import MagicMock
from urllib.parse import unquote

import pytest
from conftest import args, make_response
from test_scripts import BASE_URL, import_script

diag = import_script('okta-logs', 'diagnose_login.py')

T = '2026-10-18T12:00:00.000Z'
USER = {'id': '00u1', 'status': 'ACTIVE', 'profile': {'login': 'a@example.com'}, 'type': {'id': 'oty1'}}


def _deny(rule_id='rul1', policy_id='pol1', ip='10.0.0.5', zone=None, device=None):
    return {
        'uuid': 'e1', 'published': T, 'eventType': 'policy.evaluate_sign_on',
        'outcome': {'result': 'DENY', 'reason': 'Rule denied'},
        'client': {'ipAddress': ip, 'zone': zone},
        'device': device,
        'target': [
            {'type': 'AppInstance', 'id': '0oa1', 'displayName': 'App'},
            {'type': 'Rule', 'id': rule_id, 'detailEntry': {'policyId': policy_id}},
        ],
    }


def _allow_rule(**over):
    return {
        'id': 'rul0', 'name': 'Allow', 'priority': 0, 'status': 'ACTIVE', 'lastUpdated': '2026-01-01T00:00:00.000Z',
        'conditions': {'network': {'connection': 'ZONE', 'include': ['nzo1']}},
        'actions': {'appSignOn': {'access': 'ALLOW'}},
    } | over


CATCH_ALL = {
    'id': 'rul1', 'name': 'Catch-all', 'priority': 99, 'status': 'ACTIVE', 'lastUpdated': '2026-01-01T00:00:00.000Z',
    'conditions': None, 'actions': {'appSignOn': {'access': 'DENY'}},
}


def _session(events, rules, zones=None):
    routes = {
        '/api/v1/users/a@example.com': USER,
        '/api/v1/users/00u1/groups': [],
        '/api/v1/policies/pol1/rules': rules,
        '/api/v1/policies/pol1': {'id': 'pol1', 'name': 'Pol', 'type': 'ACCESS_POLICY', 'lastUpdated': '2026-01-01T00:00:00.000Z'},
        '/api/v1/zones': zones if zones is not None else [{'id': 'nzo1', 'name': 'Office', 'type': 'IP', 'gateways': [{'type': 'CIDR', 'value': '192.168.0.0/24'}]}],
    }

    def get(url, params=None):
        path = unquote(url.removeprefix(BASE_URL))
        if path == '/api/v1/logs':
            f = (params or {}).get('filter', '')
            return make_response(events if 'policy' not in f and 'group.user' not in f and 'update_profile' not in f and 'user.account.lock' not in f and 'verify' not in f else [])
        return make_response(routes[path])

    s = MagicMock()
    s.get.side_effect = get
    return s


def _args(**kw):
    return args(**{'user': 'a@example.com', 'since': '2026-10-18T00:00:00Z', 'until': None, 'limit': 1000,
                   'max_denials': 3, 'ip_concentration': 0.5, 'concurrency': 1} | kw)


def test_catch_all_deny_reports_failed_network_check():
    result = diag.cmd_diagnose_login(_session([_deny()], [_allow_rule(), CATCH_ALL]), BASE_URL, _args())
    d = result['denials'][0]['diagnoses'][0]
    assert d['kind'] == 'no_allow_rule_matched'
    row = d['candidates'][0]['checks'][0]
    assert (row['check'], row['pass']) == ('network.include', False)
    assert result['summary']['policy_denials'] == 1


def test_matching_ip_makes_allow_rule_unexplained():
    s = _session([_deny(ip='192.168.0.9')], [_allow_rule(), CATCH_ALL])
    d = diag.cmd_diagnose_login(s, BASE_URL, _args())['denials'][0]['diagnoses'][0]
    assert d['kind'] == 'allow_rule_unexplained'
    assert d['candidates'][0]['status'] == 'would_allow'


def test_dynamic_zone_is_undetermined_unless_event_zone_matches():
    zones = [{'id': 'nzo1', 'name': 'Dyn', 'type': 'DYNAMIC'}]
    d = diag.cmd_diagnose_login(_session([_deny()], [_allow_rule(), CATCH_ALL], zones), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    assert d['kind'] == 'undetermined'
    d = diag.cmd_diagnose_login(_session([_deny(zone='Dyn')], [_allow_rule(), CATCH_ALL], zones), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    assert d['candidates'][0]['checks'][0]['pass'] is True


def test_repeated_denials_are_grouped():
    result = diag.cmd_diagnose_login(_session([_deny(), _deny()], [CATCH_ALL]), BASE_URL, _args())
    assert result['summary']['distinct_denials'] == 1
    assert result['denials'][0]['count'] == 2
    assert result['denials'][0]['diagnoses'][0]['kind'] == 'no_allow_rule_above_catch_all'


def test_config_changed_after_event_is_flagged():
    rule = _allow_rule(lastUpdated='2026-10-18T13:00:00.000Z')
    result = diag.cmd_diagnose_login(_session([_deny()], [rule, CATCH_ALL]), BASE_URL, _args())
    assert [c['id'] for c in result['denials'][0]['changed_after_event']['config_lastUpdated_after_event']] == ['rul0']


def test_unreadable_zones_degrade_to_unknown_not_crash():
    s = _session([_deny()], [_allow_rule(), CATCH_ALL])
    base = s.get.side_effect

    def get(url, params=None):
        if url.endswith('/api/v1/zones'):
            raise RuntimeError('403')
        return base(url, params)

    s.get.side_effect = get
    d = diag.cmd_diagnose_login(s, BASE_URL, _args())['denials'][0]['diagnoses'][0]
    assert d['kind'] == 'undetermined'


def test_quote_in_user_rejected():
    with pytest.raises(ValueError):
        diag.cmd_diagnose_login(MagicMock(), BASE_URL, _args(user='a"b'))
