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


def _session(events, rules, zones=None, extra=None, logs=None):
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
            for needle, canned in (logs or {}).items():
                if needle in f:
                    return make_response(canned)
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


def _risk_row(rule_level, event_level):
    rule = _allow_rule(conditions={'riskScore': {'level': rule_level}})
    event = _deny() | {'securityContext': {'risk': {'level': event_level}}}
    d = diag.cmd_diagnose_login(_session([event], [rule, CATCH_ALL]), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    return d['candidates'][0]['checks'][0]


def test_risk_level_is_an_exact_match():
    assert _risk_row('HIGH', 'HIGH')['pass'] is True
    assert _risk_row('LOW', 'HIGH')['pass'] is False
    assert _risk_row('MEDIUM', 'LOW')['pass'] is False
    assert _risk_row('ANY', 'HIGH')['pass'] is True


GEO = {
    'client': {'ipAddress': '1.2.3.4', 'zone': None, 'geographicalContext': {'country': 'United States', 'state': 'North Carolina'}},
    'securityContext': {'asNumber': 54113, 'isProxy': True, 'ipDetails': {'ipServiceCategories': [{'operator': 'ICLOUD_RELAY_PROXY', 'type': 'Proxy', 'isAnonymous': True}]}},
}
US, DE = {'country': 'US'}, {'country': 'DE'}


@pytest.mark.parametrize(('zone', 'expected'), [
    ({'type': 'DYNAMIC', 'locations': [US]}, True),
    ({'type': 'DYNAMIC', 'locations': [DE]}, False),
    ({'type': 'DYNAMIC', 'locations': [{'country': 'US', 'region': 'US-NC'}]}, True),
    ({'type': 'DYNAMIC', 'locations': [{'country': 'US', 'region': 'US-CA'}]}, False),
    ({'type': 'DYNAMIC', 'asns': ['54113']}, True),
    ({'type': 'DYNAMIC', 'asns': ['1']}, False),
    ({'type': 'DYNAMIC', 'proxyType': 'Any'}, True),
    ({'type': 'DYNAMIC', 'proxyType': 'Tor'}, False),
    ({'type': 'DYNAMIC', 'proxyType': ''}, None),
    ({'type': 'DYNAMIC_V2', 'ipServiceCategories': {'include': ['ALL_ANONYMIZERS']}}, True),
    ({'type': 'DYNAMIC_V2', 'ipServiceCategories': {'include': ['APPLE_ICLOUD_RELAY_PROXY']}}, True),
    ({'type': 'DYNAMIC_V2', 'ipServiceCategories': {'include': ['ANONYMIZER_TOR']}}, False),
    ({'type': 'DYNAMIC_V2', 'locations': {'include': [US]}, 'asns': {'exclude': ['54113']}}, False),
    ({'type': 'DYNAMIC_V2', 'locations': {'include': [US], 'exclude': [DE]}}, True),
    ({'type': 'DYNAMIC_V2', 'locations': {'exclude': [DE]}}, None),
])
def test_dynamic_zones_are_evaluated_from_event_geo_asn_and_ip_services(zone, expected):
    zones = [{'id': 'nzo1', 'name': 'Z'} | zone]
    d = diag.cmd_diagnose_login(_session([_deny() | GEO], [_allow_rule(), CATCH_ALL], zones), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    row = d['candidates'][0]['checks'][0]
    assert row['pass'] is expected
    assert 'United States, North Carolina, AS54113' in row['actual']


def test_dynamic_zone_with_unlisted_country_is_unknown():
    event = _deny() | GEO | {'client': GEO['client'] | {'geographicalContext': {'country': 'Atlantis'}}}
    zones = [{'id': 'nzo1', 'name': 'Z', 'type': 'DYNAMIC', 'locations': [US]}]
    d = diag.cmd_diagnose_login(_session([event], [_allow_rule(), CATCH_ALL], zones), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    assert d['candidates'][0]['checks'][0]['pass'] is None


def _gate_diag(vm, enrollments, logs=None, event=None):
    """Diagnose an ALLOW rule gated by `vm`, with an MFA_ENROLL policy that allows okta_verify and okta_email enrollment."""
    rule = _allow_rule(conditions=None, actions={'appSignOn': {'access': 'ALLOW', 'verificationMethod': vm}})
    mfa = {'id': 'pmfa', 'name': 'Enroll', 'type': 'MFA_ENROLL', 'settings': {'authenticators': [
        {'key': 'okta_verify', 'enroll': {'self': 'OPTIONAL'}}, {'key': 'okta_email', 'enroll': {'self': 'REQUIRED'}}]}}
    extra = _gate_routes(enrollments) | {
        '/api/v1/authenticators': [{'id': 'aut1', 'key': 'okta_verify', 'status': 'ACTIVE'}, {'id': 'aut2', 'key': 'okta_email', 'status': 'ACTIVE'},
                                   {'id': 'aut3', 'key': 'phone', 'status': 'ACTIVE'}],
        '/api/v1/authenticators/aut2/methods': [{'type': 'email', 'status': 'ACTIVE'}],
        '/api/v1/authenticators/aut3/methods': [{'type': 'sms', 'status': 'ACTIVE'}, {'type': 'voice', 'status': 'INACTIVE'}],
        '/api/v1/policies': [mfa],
        '/api/v1/policies/pmfa/rules': [{'id': '0pr1', 'name': 'Default Rule', 'priority': 1, 'conditions': {'network': {'connection': 'ANYWHERE'}}, 'actions': {}}],
    }
    event = event or _deny()
    event = event | {'target': [*event['target'], {'type': 'Rule', 'id': '0pr1', 'detailEntry': {'policyName': 'Enroll'}}]}
    result = diag.cmd_diagnose_login(_session([event], [rule, CATCH_ALL], extra=extra, logs=logs), BASE_URL, _args())
    denial = result['denials'][0]
    return denial, next(d for d in denial['diagnoses'] if d['kind'] != 'enrollment_policy_context')


OV = {'key': 'okta_verify', 'status': 'ACTIVE', 'type': 'app', 'created': '2026-01-01T00:00:00.000Z'}
EMAIL = {'key': 'okta_email', 'status': 'ACTIVE', 'type': 'email', 'created': '2026-01-01T00:00:00.000Z'}


def test_every_next_step_of_an_authentication_chain_is_followed():
    step = lambda key, method, **kw: {'authenticationMethods': [{'key': key, 'method': method}], **kw}
    vm = {'type': 'AUTH_METHOD_CHAIN', 'chains': [step('okta_email', 'email', next=[step('okta_verify', 'signed_nonce'), step('okta_email', 'email')])]}
    _, d = _gate_diag(vm, [EMAIL])
    # branch 1 needs okta_verify (not enrolled); branch 2 needs only email, which is enrolled -> the second path satisfies the rule
    assert d['candidates'][0]['status'] == 'would_allow'
    assert d['kind'] == 'allow_rule_unexplained'


def test_chain_blocks_only_when_every_branch_is_blocked():
    step = lambda key, method, **kw: {'authenticationMethods': [{'key': key, 'method': method}], **kw}
    vm = {'type': 'AUTH_METHOD_CHAIN', 'chains': [step('okta_email', 'email', next=[step('okta_verify', 'signed_nonce'), step('okta_verify', 'push')])]}
    _, d = _gate_diag(vm, [EMAIL])
    blocking = [b['check'] for b in d['candidates'][0]['blocking']]
    assert d['candidates'][0]['status'] == 'blocked'
    assert any('okta_verify' in b for b in blocking)


def test_listed_methods_of_a_constraint_are_alternatives():
    vm = {'type': 'ASSURANCE', 'constraints': [{'possession': {'authenticationMethods': [
        {'key': 'okta_verify', 'method': 'signed_nonce'}, {'key': 'okta_email', 'method': 'email'}]}}]}
    _, d = _gate_diag(vm, [EMAIL])
    assert d['kind'] == 'allow_rule_unexplained'
    assert d['candidates'][0]['status'] == 'would_allow'


def test_types_constraint_is_evaluated_against_enrollments():
    vm = {'type': 'ASSURANCE', 'constraints': [{'possession': {'types': ['SECURITY_KEY']}}]}
    _, d = _gate_diag(vm, [OV, EMAIL])
    row = d['candidates'][0]['checks'][0]
    assert (row['check'], row['pass']) == ('enrolled authenticator', False)
    _, d = _gate_diag(vm, [OV, {'key': 'webauthn', 'status': 'ACTIVE', 'type': 'security_key', 'created': '2026-01-01T00:00:00.000Z'}])
    assert d['candidates'][0]['checks'][0]['pass'] is True


PHONE = {'key': 'phone', 'status': 'ACTIVE', 'type': 'phone', 'created': '2026-01-01T00:00:00.000Z'}


def test_methods_constraint_needs_the_authenticator_and_an_active_method_on_it():
    vm = lambda *methods: {'type': 'ASSURANCE', 'constraints': [{'possession': {'methods': list(methods)}}]}
    assert _gate_diag(vm('SMS', 'VOICE'), [OV])[1]['candidates'][0]['checks'][0]['pass'] is False
    assert _gate_diag(vm('SMS', 'VOICE'), [OV, PHONE])[1]['candidates'][0]['checks'][0]['pass'] is True
    assert _gate_diag(vm('VOICE'), [OV, PHONE])[1]['candidates'][0]['checks'][0]['pass'] is False


def _excl_diag(excluded, verify_key):
    vm = {'type': 'ASSURANCE', 'constraints': [{'knowledge': {'excludedAuthenticationMethods': excluded}}]}
    event = _deny() | {'transaction': {'id': 'tx1'}}
    logs = {'verify': [_verify(tx='tx1') | {'target': [{'type': 'AuthenticatorMethod', 'detailEntry': {'authenticatorKey': verify_key}}]}]} if verify_key else None
    _, d = _gate_diag(vm, [OV], event=event, logs=logs)
    return next(r for r in d['candidates'][0]['checks'] if r['check'] == 'excludedAuthenticationMethods')['pass']


def test_excluded_authentication_methods_are_checked_against_the_verify_event():
    assert _excl_diag({'key': 'okta_password'}, 'okta_password') is False  # single-object form, as in Okta's examples
    assert _excl_diag([{'key': 'okta_password'}], 'okta_verify') is True
    assert _excl_diag([{'key': 'okta_password'}], None) is None
    assert _excl_diag([{'key': 'okta_password', 'method': 'password'}], 'okta_password') is None


def _verify(tx=None, sid=None, props='PHISHING_RESISTANT, USER_VERIFYING', published='2026-10-18T11:59:00.000Z'):
    return {'published': published, 'eventType': 'user.authentication.verify', 'transaction': {'id': tx}, 'authenticationContext': {'rootSessionId': sid},
            'target': [{'type': 'AuthenticatorMethod', 'detailEntry': {'authenticatorKey': 'okta_verify', 'methodUsedVerifiedProperties': props}}]}


def test_verify_events_must_share_the_denys_transaction_or_root_session():
    event = _deny() | {'transaction': {'id': 'tx1'}, 'authenticationContext': {'rootSessionId': 'sid1'}}
    vm = _gated_rule()['actions']['appSignOn']['verificationMethod']
    other = _verify(tx='tx9', sid='sid9')
    denial, d = _gate_diag(vm, [OV], event=event, logs={'verify': [other]})
    assert denial['verify_events_matched_by'] is None
    assert [r['pass'] for r in d['candidates'][0]['checks'] if 'verified' in r['check']] == [None]
    denial, d = _gate_diag(vm, [OV], event=event, logs={'verify': [other, _verify(sid='sid1')]})
    assert denial['verify_events_matched_by'] == 'rootSessionId'
    assert d['candidates'][0]['status'] == 'would_allow'
    denial, _ = _gate_diag(vm, [OV], event=event, logs={'verify': [_verify(tx='tx1', sid='sid1')]})
    assert denial['verify_events_matched_by'] == 'transaction.id'


def _status_event(event_type, published):
    return {'published': published, 'eventType': event_type, 'actor': {'alternateId': 'admin@example.com'}}


def test_user_status_is_reported_as_of_the_event():
    s = _session([_deny()], [CATCH_ALL], logs={'user.lifecycle.': [_status_event('user.account.unlock', '2026-10-18T14:00:00.000Z'), _status_event('user.account.lock', '2026-10-18T13:00:00.000Z')]})
    denial = diag.cmd_diagnose_login(s, BASE_URL, _args())['denials'][0]
    assert denial['user_status_at_event'] == {'status': 'ACTIVE', 'now': 'ACTIVE', 'differs': False}
    assert [e['eventType'] for e in denial['changed_after_event']['user_status_events_since']] == ['user.account.unlock', 'user.account.lock']
    s = _session([_deny()], [CATCH_ALL], logs={'user.lifecycle.': [_status_event('user.account.unlock', '2026-10-18T14:00:00.000Z')]})
    assert diag.cmd_diagnose_login(s, BASE_URL, _args())['denials'][0]['user_status_at_event'] == {'status': 'LOCKED_OUT', 'now': 'ACTIVE', 'differs': True}


def test_user_status_is_unknown_when_the_prior_state_is_not_derivable():
    s = _session([_deny()], [CATCH_ALL], logs={'user.lifecycle.': [_status_event('user.lifecycle.reactivate', '2026-10-18T14:00:00.000Z')]})
    assert diag.cmd_diagnose_login(s, BASE_URL, _args())['denials'][0]['user_status_at_event']['status'] == 'UNKNOWN'


def _win_diag(version, constraints):
    rule = _allow_rule(conditions={'device': {'assurance': {'include': ['daa1']}}})
    extra = {'/api/v1/device-assurances/daa1': {'name': 'Win', 'platform': 'WINDOWS', 'osVersionConstraints': constraints}}
    device = {'os_platform': 'WINDOWS', 'os_version': version}
    d = diag.cmd_diagnose_login(_session([_deny(device=device)], [rule, CATCH_ALL], extra=extra), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    return d['candidates'][0]['checks'][0]


WIN_CONS = [{'majorVersionConstraint': 'WINDOWS_11', 'minimum': '10.0.22621.2000'}, {'majorVersionConstraint': 'WINDOWS_10', 'minimum': '10.0.19045.3000'}]


def test_os_version_constraints_use_the_minimum_for_the_devices_major_version():
    assert _win_diag('10.0.22621.2715', WIN_CONS)['pass'] is True
    row = _win_diag('10.0.22000.100', WIN_CONS)
    assert (row['check'], row['pass']) == ('assurance "Win": osVersionConstraints[WINDOWS_11]', False)
    assert _win_diag('10.0.19044.1', WIN_CONS)['check'].endswith('[WINDOWS_10]')
    assert _win_diag('10.0.19045.4000', WIN_CONS)['pass'] is True


def test_os_version_constraint_not_allowed_and_dynamic():
    assert _win_diag('10.0.19045.4000', [{'majorVersionConstraint': 'WINDOWS_10', 'dynamicVersionRequirement': {'type': 'NOT_ALLOWED'}}])['pass'] is False
    assert _win_diag('10.0.19045.4000', [{'majorVersionConstraint': 'WINDOWS_10', 'dynamicVersionRequirement': {'type': 'MINIMUM'}}])['pass'] is None
    assert _win_diag('10.0.19045.4000', [{'majorVersionConstraint': 'WINDOWS_11', 'minimum': '10.0.22000'}])['pass'] is None


def _fail(published, event_type, reason, **extra):
    return {'published': published, 'eventType': event_type, 'outcome': {'result': 'FAILURE', 'reason': reason}, 'client': {'ipAddress': '9.9.9.9'}} | extra


def test_each_failed_attempt_gets_a_root_cause():
    events = [
        _fail('2026-10-18T10:05:00.000Z', 'user.session.start', 'LOCKED_OUT'),
        _fail('2026-10-18T10:04:00.000Z', 'user.authentication.auth_via_mfa', 'VERIFICATION_ERROR', authenticationContext={'credentialType': 'OTP'}),
        _fail('2026-10-18T10:00:00.000Z', 'user.session.start', 'INVALID_CREDENTIALS'),
        _fail('2026-10-18T09:00:00.000Z', 'app.oauth2.token.grant', 'User is not assigned to the client application.'),
    ]
    s = _session(events, [CATCH_ALL], logs={'user.account.lock': [{'published': '2026-10-18T10:01:00.000Z', 'eventType': 'user.account.lock'}]})
    other = diag.cmd_diagnose_login(s, BASE_URL, _args())['other_failures']
    causes = [a['cause'] for a in other['attempts']]
    assert causes == ['account is locked out', 'MFA failed (OTP): authenticator verification failed', 'wrong password or credential', 'user is not assigned to the app']
    assert other['attempts'][2]['lock_followed_at'] == '2026-10-18T10:01:00.000Z'
    assert 'lock_followed_at' not in other['attempts'][0]
    assert other['by_cause']['wrong password or credential'] == 1


def test_country_table_covers_every_iso_3166_1_alpha_2_code():
    codes = set(diag._COUNTRIES.values())
    assert len(codes) >= 249
    assert {diag._COUNTRIES[n] for n in ('united states', 'türkiye', 'turkey', 'czechia', 'czech republic', 'south korea', 'vietnam', 'viet nam')} == {'US', 'TR', 'CZ', 'KR', 'VN'}


def test_tor_is_recognised_by_service_type_and_excluded_from_all_anonymizers_except_tor():
    tor = {'securityContext': {'ipDetails': {'ipServiceCategories': [{'operator': 'TORPROJECT', 'type': 'Tor', 'isAnonymous': True}]}}}
    assert diag._svc_hit(['ANONYMIZER_TOR'], tor) is True
    assert diag._svc_hit(['ALL_ANONYMIZERS_EXCEPT_TOR'], tor) is False
    assert diag._svc_hit(['ABCPROXY_PROXY'], GEO) is None
    vpn = {'securityContext': {'ipDetails': {'ipServiceCategories': [{'operator': 'ACTMOBILE', 'type': 'VPN', 'isAnonymous': False}]}}}
    assert diag._svc_hit(['ACTMOBILE_VPN'], vpn) is True
    assert diag._svc_hit(['ALL_PROXIES_VPNS'], vpn) is True


def _e(v, latest=False, dist=0, sup=True):
    return {'osVersion': v, 'distanceFromLatestMajor': dist, 'supportedMajor': sup} | ({'isLatest': True} if latest else {'isPreset': True})


OV_CONFIG = {'platformVersionsInfo': {
    'WINDOWS': [_e('10.0.19045.0', dist=0), _e('10.0.19045.7725', True, 0), _e('10.0.22631.0', dist=3), _e('10.0.22631.7582', True, 3),
                _e('10.0.26100.0', dist=2), _e('10.0.26100.9445', True, 2), _e('10.0.26300.0', dist=0), _e('10.0.26300.9550', True, 0),
                _e('10.0.22000.0', dist=5, sup=False)],
    'MACOS': [_e('14.0.0', dist=1), _e('14.8.9', True, 1), _e('15.0.0', dist=0), _e('15.0.1', True, 0)],
    'IOS': [_e('17.0.0', dist=1), _e('17.7.2', True, 1), _e('18.0.0', dist=0), _e('18.7.10', True, 0)],
}}


def _dyn(platform, version, dyn, ov=OV_CONFIG):
    rule = _allow_rule(conditions={'device': {'assurance': {'include': ['daa1']}}})
    extra = {'/api/v1/device-assurances/daa1': {'name': 'P', 'platform': platform, 'osVersion': {'dynamicVersionRequirement': dyn}}}
    if ov:
        extra['/.well-known/ov-configurations'] = ov
    device = {'os_platform': platform, 'os_version': version}
    d = diag.cmd_diagnose_login(_session([_deny(device=device)], [rule, CATCH_ALL], extra=extra), BASE_URL, _args())['denials'][0]['diagnoses'][0]
    return d['candidates'][0]['checks'][0]


@pytest.mark.parametrize('platform,version,dyn,expected', [
    ('WINDOWS', '10.0.26100.1', {'type': 'MINIMUM', 'distanceFromLatestMajor': 2}, True),
    ('WINDOWS', '10.0.22631.5', {'type': 'MINIMUM', 'distanceFromLatestMajor': 2}, False),
    ('WINDOWS', '10.0.26100.9000', {'type': 'MINIMUM', 'distanceFromLatestMajor': 2, 'latestSecurityPatch': True}, False),
    ('WINDOWS', '10.0.26100.9445', {'type': 'MINIMUM', 'distanceFromLatestMajor': 2, 'latestSecurityPatch': True}, True),
    ('WINDOWS', '10.0.26100.1', {'type': 'EXACT', 'distanceFromLatestMajor': 2}, True),
    ('WINDOWS', '10.0.26300.1', {'type': 'EXACT', 'distanceFromLatestMajor': 2}, False),
    ('WINDOWS', '10.0.22000.100', {'type': 'EXACT_ANY_SUPPORTED'}, False),
    ('WINDOWS', '10.0.22631.100', {'type': 'EXACT_ANY_SUPPORTED'}, True),
    ('MACOS', '14.1.0', {'type': 'MINIMUM', 'distanceFromLatestMajor': 1}, True),
    ('MACOS', '13.7.0', {'type': 'MINIMUM', 'distanceFromLatestMajor': 1}, False),
    ('MACOS', '15.0.0', {'type': 'MINIMUM', 'distanceFromLatestMajor': 0, 'latestSecurityPatch': True}, False),
    ('IOS', '17.5', {'type': 'MINIMUM', 'distanceFromLatestMajor': 1}, True),
    ('IOS', '16.7', {'type': 'MINIMUM', 'distanceFromLatestMajor': 1}, False),
    ('IOS', '17.7.2', {'type': 'EXACT', 'distanceFromLatestMajor': 0}, False),
])
def test_dynamic_os_requirement_uses_the_okta_latest_version_list(platform, version, dyn, expected):
    assert _dyn(platform, version, dyn)['pass'] is expected


def test_dynamic_os_requirement_is_undetermined_without_the_version_list():
    assert _dyn('WINDOWS', '10.0.26100.1', {'type': 'MINIMUM', 'distanceFromLatestMajor': 2}, ov=None)['pass'] is None


def _first_diag(event, rules, zones=None):
    return diag.cmd_diagnose_login(_session([event], rules, zones), BASE_URL, _args())['denials'][0]['diagnoses'][0]


@pytest.mark.parametrize('client,device', [
    ({'ipAddress': '10.0.0.5', 'userAgent': {'os': 'Mac OS X'}, 'device': 'Computer'}, None),
    ({'ipAddress': '10.0.0.5'}, {'os_platform': 'MACOS'}),
    ({'ipAddress': '10.0.0.5'}, {'os_platform': 'OSX'}),
])
def test_macos_matches_the_osx_platform_condition_however_the_event_names_it(client, device):
    rule = _allow_rule(conditions={'platform': {'include': [{'type': 'ANY', 'os': {'type': 'OSX'}}]}})
    d = _first_diag(_deny(device=device) | {'client': client}, [rule, CATCH_ALL])
    assert d['candidates'][0]['checks'][0]['pass'] is True


def test_inactive_zone_never_matches():
    zones = [{'id': 'nzo1', 'name': 'Office', 'type': 'IP', 'status': 'INACTIVE', 'gateways': [{'type': 'CIDR', 'value': '10.0.0.0/24'}]}]
    assert _first_diag(_deny(), [_allow_rule(), CATCH_ALL], zones)['candidates'][0]['checks'][0]['pass'] is False
    exclude = _allow_rule(conditions={'network': {'connection': 'ZONE', 'exclude': ['nzo1']}})
    assert _first_diag(_deny(), [exclude, CATCH_ALL], zones)['candidates'][0]['checks'][0]['pass'] is True


def test_catch_all_is_recognised_by_the_system_flag_when_present():
    custom_deny = CATCH_ALL | {'system': False}
    assert _first_diag(_deny(), [_allow_rule(), custom_deny])['kind'] == 'explicit_deny_rule'
    system_with_conditions = CATCH_ALL | {'system': True, 'conditions': {'network': {'connection': 'ANYWHERE'}}}
    assert _first_diag(_deny(), [_allow_rule(), system_with_conditions])['kind'] == 'no_allow_rule_matched'


def test_lock_followed_at_is_the_first_lock_after_the_attempt():
    locks = [{'published': '2026-10-18T12:08:00.000Z'}, {'published': '2026-10-18T12:02:00.000Z'}]  # newest first
    attempt = diag._attempt({'published': '2026-10-18T12:00:00.000Z', 'eventType': 'user.session.start', 'outcome': {'result': 'FAILURE', 'reason': 'x'}}, locks)
    assert attempt['lock_followed_at'] == '2026-10-18T12:02:00.000Z'


def test_user_status_changes_are_limited_to_successful_events():
    s = _session([_deny()], [CATCH_ALL])
    diag.cmd_diagnose_login(s, BASE_URL, _args())
    filters = [c.kwargs['params']['filter'] for c in s.get.call_args_list if c.kwargs.get('params')]
    assert any('user.account.unlock' in f and 'outcome.result eq "SUCCESS"' in f for f in filters)


def test_constraint_naming_nothing_adds_no_row_and_does_not_block():
    vm = {'type': 'ASSURANCE', 'constraints': [{'possession': {}}]}
    _, d = _gate_diag(vm, [OV])
    assert not [r for r in d['candidates'][0]['checks'] if 'authenticator' in r['check'] and 'MFA_ENROLL' not in r['check']]
    assert d['candidates'][0]['status'] == 'would_allow'
