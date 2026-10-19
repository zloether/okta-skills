"""diagnose_login.py: policy-tree walk against canned API responses (no network)."""
from unittest.mock import MagicMock
from urllib.parse import unquote

import pytest
from conftest import args, make_response
from test_scripts import BASE_URL, import_script

diag = import_script('okta-logs', 'diagnose_login.py')

T = '2026-10-18T12:00:00.000Z'
USER = {'id': '00u1', 'status': 'ACTIVE', 'profile': {'login': 'a@example.com'}, 'type': {'id': 'oty1'}}


def _deny(rule_id='rul1', policy_id='pol1', ip='10.0.0.5', zone=None, device=None, extra_targets=()):
    return {
        'uuid': 'e1', 'published': T, 'eventType': 'policy.evaluate_sign_on',
        'outcome': {'result': 'DENY', 'reason': 'Rule denied'},
        'client': {'ipAddress': ip, 'zone': zone},
        'device': device,
        'target': [
            {'type': 'AppInstance', 'id': '0oa1', 'displayName': 'App'},
            {'type': 'Rule', 'id': rule_id, 'detailEntry': {'policyId': policy_id}},
            *extra_targets,
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


def _session(events, rules, zones=None, extra=None):
    routes = {
        '/api/v1/users/a@example.com': USER,
        '/api/v1/users/00u1/groups': [],
        '/api/v1/policies/pol1/rules': rules,
        '/api/v1/policies/pol1': {'id': 'pol1', 'name': 'Pol', 'type': 'ACCESS_POLICY', 'lastUpdated': '2026-01-01T00:00:00.000Z'},
        '/api/v1/zones': zones if zones is not None else [{'id': 'nzo1', 'name': 'Office', 'type': 'IP', 'gateways': [{'type': 'CIDR', 'value': '192.168.0.0/24'}]}],
    } | (extra or {})

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


def test_blocking_list_and_reason_name_the_failed_checks():
    result = diag.cmd_diagnose_login(_session([_deny()], [_allow_rule(), CATCH_ALL]), BASE_URL, _args())
    d = result['denials'][0]['diagnoses'][0]
    cand = d['candidates'][0]
    assert [b['check'] for b in cand['blocking']] == ['network.include']
    assert cand['unresolved'] == 0
    assert d['reason'].startswith('ALLOW rule "Allow" did not match: network.include')


def test_assurance_with_no_device_platform_is_unknown_not_failed():
    rule = _allow_rule(conditions={'device': {'assurance': {'include': ['daa1']}}})
    extra = {'/api/v1/device-assurances/daa1': {'name': 'Mac', 'platform': 'MACOS'}}
    d = diag.cmd_diagnose_login(_session([_deny()], [rule, CATCH_ALL], extra=extra), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    row = d['candidates'][0]['checks'][0]
    assert (row['check'], row['pass']) == ('device.assurance', None)
    assert d['kind'] == 'undetermined'


def test_assurance_for_other_platform_still_fails():
    rule = _allow_rule(conditions={'device': {'assurance': {'include': ['daa1']}}})
    extra = {'/api/v1/device-assurances/daa1': {'name': 'Win', 'platform': 'WINDOWS'}}
    d = diag.cmd_diagnose_login(_session([_deny(device={'os_platform': 'MACOS'})], [rule, CATCH_ALL], extra=extra), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    assert d['candidates'][0]['checks'][0]['pass'] is False


def _gated_rule():
    return _allow_rule(conditions=None, actions={'appSignOn': {'access': 'ALLOW', 'verificationMethod': {
        'type': 'ASSURANCE', 'constraints': [{'possession': {
            'authenticationMethods': [{'key': 'okta_verify', 'method': 'signed_nonce'}],
            'phishingResistant': 'REQUIRED', 'userVerification': 'REQUIRED'}}]}}})


def _gate_routes(enrollments):
    return {
        '/api/v1/users/00u1/authenticator-enrollments': enrollments,
        '/api/v1/authenticators': [{'id': 'aut1', 'key': 'okta_verify', 'status': 'ACTIVE'}],
        '/api/v1/authenticators/aut1/methods': [{'type': 'signed_nonce', 'status': 'ACTIVE'}],
    }


def test_verified_properties_collapse_to_one_row_when_no_verify_event():
    enrolled = [{'key': 'okta_verify', 'status': 'ACTIVE', 'created': '2026-01-01T00:00:00.000Z'}]
    d = diag.cmd_diagnose_login(_session([_deny()], [_gated_rule(), CATCH_ALL], extra=_gate_routes(enrolled)), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    rows = [r for r in d['candidates'][0]['checks'] if 'verified' in r['check']]
    assert len(rows) == 1
    assert rows[0]['pass'] is None
    assert rows[0]['required'] == ['PHISHING_RESISTANT', 'USER_VERIFYING']


def test_verified_properties_skipped_when_enrollment_already_blocks():
    d = diag.cmd_diagnose_login(_session([_deny()], [_gated_rule(), CATCH_ALL], extra=_gate_routes([])), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    checks = d['candidates'][0]['checks']
    assert not [r for r in checks if 'verified' in r['check']]
    assert [b['check'] for b in d['candidates'][0]['blocking']] == ['okta_verify/signed_nonce: user enrolled at event time']


def test_mfa_enroll_rule_is_context_without_noise():
    mfa_rule = {'id': '0pr1', 'name': 'Default Rule', 'priority': 1, 'conditions': {'network': {'connection': 'ANYWHERE'}}, 'actions': {}}
    extra = {
        '/api/v1/policies': [{'id': 'pmfa', 'name': 'Default Policy', 'type': 'MFA_ENROLL'}],
        '/api/v1/policies/pmfa/rules': [mfa_rule],
    }
    target = {'type': 'Rule', 'id': '0pr1', 'detailEntry': {'policyName': 'Default Policy'}}
    result = diag.cmd_diagnose_login(
        _session([_deny(extra_targets=[target])], [_allow_rule(), CATCH_ALL], extra=extra), BASE_URL, _args())
    ctx = next(d for d in result['denials'][0]['diagnoses'] if d['kind'] == 'enrollment_policy_context')
    assert 'access' not in ctx['matched_rule']
    assert ctx['checks'] == []


def _assurance_diag(device, policy):
    rule = _allow_rule(conditions={'device': {'assurance': {'include': ['daa1']}}})
    extra = {'/api/v1/device-assurances/daa1': {'name': 'Mac', 'platform': 'MACOS'} | policy}
    d = diag.cmd_diagnose_login(_session([_deny(device=device)], [rule, CATCH_ALL], extra=extra), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    return {r['check']: r for r in d['candidates'][0]['checks']}


def test_osx_event_platform_matches_macos_assurance_policy():
    rows = _assurance_diag({'os_platform': 'OSX', 'os_version': '28.0.1'}, {'osVersion': {'minimum': '28.0.0'}})
    assert rows['device.assurance']['pass'] is True
    assert rows['device.assurance']['actual'] == 'met "Mac"'


def test_os_version_below_minimum_is_the_blocking_check():
    rows = _assurance_diag({'os_platform': 'OSX', 'os_version': '27.0.1'}, {'osVersion': {'minimum': '28.0.0'}})
    row = rows['assurance "Mac": osVersion.minimum']
    assert (row['required'], row['actual'], row['pass']) == ('28.0.0', '27.0.1', False)


def test_os_version_comparison_pads_short_versions():
    rows = _assurance_diag({'os_platform': 'OSX', 'os_version': '28'}, {'osVersion': {'minimum': '28.0.0'}})
    assert rows['device.assurance']['pass'] is True


def test_dynamic_os_version_requirement_stays_unknown():
    rows = _assurance_diag({'os_platform': 'OSX', 'os_version': '27.0.1'}, {'osVersion': {'dynamicVersionRequirement': {'type': 'MINIMUM'}}})
    assert rows['assurance "Mac": osVersion']['pass'] is None


def _multi_assurance(policies, device):
    rule = _allow_rule(conditions={'device': {'assurance': {'include': list(policies)}}})
    extra = {f'/api/v1/device-assurances/{i}': {'platform': 'MACOS', 'name': i} | p for i, p in policies.items()}
    d = diag.cmd_diagnose_login(_session([_deny(device=device)], [rule, CATCH_ALL], extra=extra), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    return d, {r['check']: r for r in d['candidates'][0]['checks']}


def test_any_one_assurance_policy_satisfies_the_rule():
    d, rows = _multi_assurance(
        {'strict': {'osVersion': {'minimum': '28.0.0'}}, 'relaxed': {'osVersion': {'minimum': '26.0.0'}}},
        {'os_platform': 'OSX', 'os_version': '27.0.1'})
    assert rows['device.assurance']['pass'] is True
    assert 'relaxed' in rows['device.assurance']['actual']
    assert d['kind'] == 'allow_rule_unexplained'


def test_all_assurance_policies_failing_blocks_and_shows_closest():
    d, _ = _multi_assurance(
        {'a': {'osVersion': {'minimum': '28.0.0'}, 'secureHardwarePresent': True},
         'b': {'osVersion': {'minimum': '29.0.0'}}},
        {'os_platform': 'OSX', 'os_version': '27.0.1', 'secure_hardware_present': False})
    assert d['kind'] == 'no_allow_rule_matched'
    assert [b['check'] for b in d['candidates'][0]['blocking']] == ['assurance "b": osVersion.minimum']


def test_unknown_assurance_policy_keeps_rule_undetermined_when_none_is_met():
    d, _ = _multi_assurance(
        {'a': {'osVersion': {'minimum': '28.0.0'}}, 'b': {'osVersion': {'dynamicVersionRequirement': {'type': 'MINIMUM'}}}},
        {'os_platform': 'OSX', 'os_version': '27.0.1'})
    assert d['kind'] == 'undetermined'
