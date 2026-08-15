"""Tests for individual skill scripts — verifies correct API URLs and params.

Rather than testing all 9 scripts exhaustively (they share the same patterns),
these tests cover the distinct cases: users (list/get/search), policies
(required --type param), logs (flag-to-param mapping), and devices (uses
'search' not 'filter').
"""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from conftest import args, make_response

_SKILLS_DIR = Path(__file__).parents[1] / 'skills'
_script_cache = {}


def import_script(skill_name, script_filename):
    """Import a skill script by path, caching to avoid re-execution."""
    key = f'{skill_name}/{script_filename}'
    if key not in _script_cache:
        path = _SKILLS_DIR / skill_name / 'scripts' / script_filename
        spec = importlib.util.spec_from_file_location(key, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _script_cache[key] = module
    return _script_cache[key]


BASE_URL = 'https://example.okta.com'


# ---------------------------------------------------------------------------
# users.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def users():
    return import_script('okta-users', 'users.py')


def test_users_list_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, args(filter=None, search=None, q=None, sort_by=None, sort_order=None, fields=None, expand=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/users'


def test_users_list_passes_filter_param(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, args(filter='status eq "ACTIVE"', search=None, q=None, sort_by=None, sort_order=None, fields=None, expand=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'status eq "ACTIVE"'}


def test_users_list_no_filter_sends_empty_params(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, args(filter=None, search=None, q=None, sort_by=None, sort_order=None, fields=None, expand=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_users_get_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'u1'})
    users.cmd_get(session, BASE_URL, args(id='user@example.com', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/users/user@example.com'


def test_users_resolve_user_id_passes_through_an_id(users):
    session = MagicMock()
    assert users.resolve_user_id(session, BASE_URL, '00us8whbc8nFfqQ1o697') == '00us8whbc8nFfqQ1o697'
    session.get.assert_not_called()


def test_users_resolve_user_id_looks_up_a_login(users):
    session = MagicMock()
    session.get.return_value = make_response({'id': '00us8whbc8nFfqQ1o697'})
    assert users.resolve_user_id(session, BASE_URL, 'user@example.com') == '00us8whbc8nFfqQ1o697'
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/user%40example.com'


def test_users_resolve_user_id_quotes_special_characters_in_a_login(users):
    session = MagicMock()
    session.get.return_value = make_response({'id': '00us8whbc8nFfqQ1o697'})
    assert users.resolve_user_id(session, BASE_URL, 'user/name#1?') == '00us8whbc8nFfqQ1o697'
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/user%2Fname%231%3F'


def test_users_search_uses_q_param(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_search(session, BASE_URL, args(query='Jane'))
    params = session.get.call_args[1]['params']
    assert params == {'q': 'Jane'}


def test_users_get_apps_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_apps(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/appLinks'


def test_users_get_blocks_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_blocks(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/blocks'


def test_users_get_groups_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_groups(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/groups'


def test_users_get_idps_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_idps(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/idps'


def test_users_get_linked_objects_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_linked_objects(session, BASE_URL, args(id='u1', relationship='manager'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/linkedObjects/manager'


def test_users_get_enrollments_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_enrollments(session, BASE_URL, args(id='u1', disclose_identifiers=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/authenticator-enrollments'


def test_users_get_enrollments_disclose_identifiers_sends_phone(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_enrollments(session, BASE_URL, args(id='u1', disclose_identifiers='phone'))
    assert session.get.call_args[1]['params'] == {'discloseIdentifiers': 'phone'}


def test_users_get_classification_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_classification(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/classification'


def test_users_get_clients_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_clients(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/clients'


def test_users_get_client_grants_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_client_grants(session, BASE_URL, args(id='u1', client_id='c1', limit=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/clients/c1/grants'


def test_users_get_client_grants_passes_limit(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_client_grants(session, BASE_URL, args(id='u1', client_id='c1', limit=10))
    assert session.get.call_args[1]['params'].get('limit') == 10


def test_users_get_client_tokens_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_client_tokens(session, BASE_URL, args(id='u1', client_id='c1', limit=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/clients/c1/tokens'


def test_users_get_client_token_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_client_token(session, BASE_URL, args(id='u1', client_id='c1', token_id='t1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/clients/c1/tokens/t1'


def test_users_get_devices_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_devices(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/devices'


def test_users_get_factors_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_factors(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/factors'


def test_users_get_grants_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_grants(session, BASE_URL, args(id='u1', scope_id=None, expand=None, limit=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/grants'


def test_users_get_grants_passes_scope_id(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_grants(session, BASE_URL, args(id='u1', scope_id='okta.users.read', expand=None, limit=None))
    assert session.get.call_args[1]['params'].get('scopeId') == 'okta.users.read'


def test_users_get_grants_no_scope_id_sends_empty_params(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_grants(session, BASE_URL, args(id='u1', scope_id=None, expand=None, limit=None))
    assert session.get.call_args[1]['params'] == {}


def test_users_get_grant_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_grant(session, BASE_URL, args(id='u1', grant_id='g1', expand=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/grants/g1'


def test_users_get_risk_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_risk(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/risk'


def test_users_get_roles_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_roles(session, BASE_URL, args(id='u1', expand=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/roles'


def test_users_get_role_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_role(session, BASE_URL, args(id='u1', role_id='r1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/roles/r1'


def test_users_get_subscriptions_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_subscriptions(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/subscriptions'


def test_users_get_subscription_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_subscription(session, BASE_URL, args(id='u1', notification_type='OKTA_ANNOUNCEMENT'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/subscriptions/OKTA_ANNOUNCEMENT'


def test_users_get_factors_catalog_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_factors_catalog(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/factors/catalog'


def test_users_get_factors_questions_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_factors_questions(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/factors/questions'


def test_users_get_factor_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_factor(session, BASE_URL, args(id='u1', factor_id='f1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/factors/f1'


def test_users_get_factor_transaction_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_factor_transaction(session, BASE_URL, args(id='u1', factor_id='f1', transaction_id='t1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/factors/f1/transactions/t1'


def test_users_get_enrollment_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_enrollment(session, BASE_URL, args(id='u1', enrollment_id='e1', disclose_identifiers=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/authenticator-enrollments/e1'


def test_users_get_enrollment_disclose_identifiers_sends_phone(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_enrollment(session, BASE_URL, args(id='u1', enrollment_id='e1', disclose_identifiers='phone'))
    assert session.get.call_args[1]['params'] == {'discloseIdentifiers': 'phone'}


def test_users_get_role_governance_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_role_governance(session, BASE_URL, args(id='u1', role_id='r1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/roles/r1/governance'


def test_users_get_role_governance_grant_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_role_governance_grant(session, BASE_URL, args(id='u1', role_id='r1', grant_id='g1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/roles/r1/governance/g1'


def test_users_get_role_governance_grant_resources_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({'resources': []})
    users.cmd_get_role_governance_grant_resources(session, BASE_URL, args(id='u1', role_id='r1', grant_id='g1', limit=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/roles/r1/governance/g1/resources'


def test_users_get_role_app_targets_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_role_app_targets(session, BASE_URL, args(id='u1', role_id='r1', limit=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/roles/r1/targets/catalog/apps'


def test_users_get_role_group_targets_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_role_group_targets(session, BASE_URL, args(id='u1', role_id='r1', limit=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/roles/r1/targets/groups'


def test_users_get_role_targets_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_role_targets(session, BASE_URL, args(id='u1', role_id='r1', assignment_type=None, limit=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/roles/r1/targets'


def test_users_get_role_targets_passes_assignment_type(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_role_targets(session, BASE_URL, args(id='u1', role_id='r1', assignment_type='GROUP', limit=None))
    assert session.get.call_args[1]['params'].get('assignmentType') == 'GROUP'


# ---------------------------------------------------------------------------
# policies.py — --type is required by the Okta API
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def policies():
    return import_script('okta-policies', 'policies.py')


def test_policies_list_passes_type_param(policies):
    session = MagicMock()
    session.get.return_value = make_response([])
    policies.cmd_list(session, BASE_URL, args(type='OKTA_SIGN_ON', status=None, q=None, expand=None, sort_by=None, resource_id=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'type': 'OKTA_SIGN_ON'}


def test_policies_list_respects_limit(policies):
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'p1'}, {'id': 'p2'}, {'id': 'p3'}])
    result = policies.cmd_list(session, BASE_URL, args(type='OKTA_SIGN_ON', status=None, q=None, expand=None, sort_by=None, resource_id=None, limit=2))
    assert result == [{'id': 'p1'}, {'id': 'p2'}]


def test_policies_list_rejects_invalid_type(policies):
    with pytest.raises(SystemExit):
        policies.main.__globals__['__name__'] = '__main__'
        import sys
        old_argv = sys.argv
        sys.argv = ['policies.py', 'list', '--type', 'NOT_A_REAL_TYPE']
        try:
            policies.main()
        finally:
            sys.argv = old_argv


def test_policies_get_calls_correct_url(policies):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'pol123'})
    policies.cmd_get(session, BASE_URL, args(id='pol123', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/policies/pol123'


def test_policies_get_rules_calls_correct_url(policies):
    session = MagicMock()
    session.get.return_value = make_response([])
    policies.cmd_get_rules(session, BASE_URL, args(id='pol123'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/policies/pol123/rules'


def test_policies_get_rule_calls_correct_url(policies):
    session = MagicMock()
    session.get.return_value = make_response({})
    policies.cmd_get_rule(session, BASE_URL, args(id='pol123', rule_id='rule1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/policies/pol123/rules/rule1'


def test_policies_list_mappings_calls_correct_url(policies):
    session = MagicMock()
    session.get.return_value = make_response([])
    policies.cmd_list_mappings(session, BASE_URL, args(id='pol123'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/policies/pol123/mappings'


def test_policies_get_mapping_calls_correct_url(policies):
    session = MagicMock()
    session.get.return_value = make_response({})
    policies.cmd_get_mapping(session, BASE_URL, args(id='pol123', mapping_id='map1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/policies/pol123/mappings/map1'


# ---------------------------------------------------------------------------
# logs.py — flag-to-param mapping
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def logs():
    return import_script('okta-logs', 'logs.py')


def _log_args(**kwargs):
    defaults = {'since': None, 'until': None, 'filter': None, 'q': None, 'sort_order': None, 'limit': None}
    defaults.update(kwargs)
    return args(**defaults)


def _failure_args(**kwargs):
    defaults = {'since': None, 'until': None, 'user': None, 'q': None, 'sort_order': None, 'limit': None}
    defaults.update(kwargs)
    return args(**defaults)


def test_logs_list_no_args_sends_empty_params(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_list(session, BASE_URL, _log_args())
    params = session.get.call_args[1]['params']
    assert params == {}


def test_logs_list_since_and_filter(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_list(session, BASE_URL, _log_args(
        since='2024-01-01T00:00:00Z',
        filter='eventType eq "user.session.start"',
    ))
    params = session.get.call_args[1]['params']
    assert params['since'] == '2024-01-01T00:00:00Z'
    assert params['filter'] == 'eventType eq "user.session.start"'
    assert 'eventType' not in params


def test_logs_list_sort_order_maps_to_sortOrder(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_list(session, BASE_URL, _log_args(sort_order='DESCENDING'))
    params = session.get.call_args[1]['params']
    assert params['sortOrder'] == 'DESCENDING'


def test_login_failures_makes_one_request(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args())
    assert session.get.call_count == 1


def test_login_failures_queries_failure_and_deny_in_single_filter(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args())
    f = session.get.call_args[1]['params']['filter']
    assert 'FAILURE' in f
    assert 'DENY' in f
    assert ' or ' in f


def test_login_failures_defaults_to_24h_window(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args())
    since = session.get.call_args[1]['params']['since']
    assert since is not None


def test_login_failures_respects_explicit_since(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args(since='2024-01-01T00:00:00Z'))
    since = session.get.call_args[1]['params']['since']
    assert since == '2024-01-01T00:00:00Z'


def test_login_failures_adds_user_filter(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args(user='user@example.com'))
    f = session.get.call_args[1]['params']['filter']
    assert 'actor.alternateId eq "user@example.com"' in f


def test_login_failures_rejects_user_with_double_quote(logs):
    session = MagicMock()
    with pytest.raises(ValueError):
        logs.cmd_login_failures(session, BASE_URL, _failure_args(user='a" or 1 eq 1 or actor.alternateId eq "b'))


def test_login_failures_groups_by_event_type(logs):
    events = [
        {'eventType': 'user.session.start', 'outcome': {'result': 'FAILURE'}},
        {'eventType': 'user.session.start', 'outcome': {'result': 'FAILURE'}},
        {'eventType': 'policy.evaluate_sign_on', 'outcome': {'result': 'DENY'}},
    ]
    session = MagicMock()
    session.get.return_value = make_response(events)
    result = logs.cmd_login_failures(session, BASE_URL, _failure_args())
    assert result['summary']['by_event_type']['user.session.start'] == 2
    assert result['summary']['by_event_type']['policy.evaluate_sign_on'] == 1
    assert result['summary']['by_outcome']['FAILURE'] == 2
    assert result['summary']['by_outcome']['DENY'] == 1
    assert result['summary']['total'] == 3
    assert result['summary']['truncated'] is False


def test_login_failures_truncated_when_result_count_hits_limit(logs):
    events = [{'eventType': 'user.session.start', 'outcome': {'result': 'FAILURE'}}] * 2
    session = MagicMock()
    session.get.return_value = make_response(events)
    result = logs.cmd_login_failures(session, BASE_URL, _failure_args(limit=2))
    assert result['summary']['total'] == 2
    assert result['summary']['truncated'] is True


def test_login_failures_by_outcome_always_has_failure_and_deny_keys(logs):
    # Zero-count outcomes must be present so consumers can access them without KeyError
    events = [{'eventType': 'policy.evaluate_sign_on', 'outcome': {'result': 'DENY'}}]
    session = MagicMock()
    session.get.return_value = make_response(events)
    result = logs.cmd_login_failures(session, BASE_URL, _failure_args())
    assert result['summary']['by_outcome']['FAILURE'] == 0
    assert result['summary']['by_outcome']['DENY'] == 1


# ---------------------------------------------------------------------------
# devices.py — list uses 'search' param, not 'filter'
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def devices():
    return import_script('okta-devices', 'devices.py')


def test_devices_list_uses_search_not_filter(devices):
    session = MagicMock()
    session.get.return_value = make_response([])
    devices.cmd_list(session, BASE_URL, args(search='status eq "ACTIVE"', expand=None, limit=None))
    params = session.get.call_args[1]['params']
    assert 'search' in params
    assert 'filter' not in params


def test_devices_get_users_calls_correct_url(devices):
    session = MagicMock()
    session.get.return_value = make_response([])
    devices.cmd_get_users(session, BASE_URL, args(id='dev123'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/devices/dev123/users'


def test_devices_get_calls_correct_url(devices):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'dev123'})
    devices.cmd_get(session, BASE_URL, args(id='dev123'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/devices/dev123'


def test_devices_get_os_accounts_calls_correct_url(devices):
    session = MagicMock()
    session.get.return_value = make_response([])
    devices.cmd_get_os_accounts(session, BASE_URL, args(id='dev123', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/devices/dev123/os-accounts'


def test_devices_get_os_account_calls_correct_url(devices):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'osa123'})
    devices.cmd_get_os_account(session, BASE_URL, args(id='dev123', os_account_id='osa123', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/devices/dev123/os-accounts/osa123'


# ---------------------------------------------------------------------------
# groups.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def groups():
    return import_script('okta-groups', 'groups.py')


def test_groups_list_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter=None, search=None, q=None, expand=None, sort_by=None, sort_order=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups'


def test_groups_list_passes_filter_param(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter='type eq "OKTA_GROUP"', search=None, q=None, expand=None, sort_by=None, sort_order=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'type eq "OKTA_GROUP"'}


def test_groups_list_rejects_filter_and_search_together(groups):
    with pytest.raises(SystemExit):
        groups.main.__globals__['__name__'] = '__main__'
        import sys
        old_argv = sys.argv
        sys.argv = ['groups.py', 'list', '--filter', 'type eq "OKTA_GROUP"', '--search', 'profile.name co "Eng"']
        try:
            groups.main()
        finally:
            sys.argv = old_argv


def test_groups_list_passes_search_param(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter=None, search='profile.name co "Eng"', q=None, expand=None, sort_by=None, sort_order=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params.get('search') == 'profile.name co "Eng"'


def test_groups_list_no_filter_sends_empty_params(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter=None, search=None, q=None, expand=None, sort_by=None, sort_order=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_groups_get_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'g1'})
    groups.cmd_get(session, BASE_URL, args(id='g1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/g1'


def test_groups_get_members_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_get_members(session, BASE_URL, args(id='g1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/g1/users'


def test_groups_search_uses_q_param(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_search(session, BASE_URL, args(query='Admins'))
    params = session.get.call_args[1]['params']
    assert params == {'q': 'Admins'}


def test_groups_get_apps_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_get_apps(session, BASE_URL, args(id='g1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/g1/apps'


def test_groups_get_owners_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_get_owners(session, BASE_URL, args(id='g1', search=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/g1/owners'


def test_groups_list_rules_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list_rules(session, BASE_URL, args(search=None, expand=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/rules'


def test_groups_list_rules_passes_search_param(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list_rules(session, BASE_URL, args(search='Engineering', expand=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params.get('search') == 'Engineering'


def test_groups_get_rule_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response({})
    groups.cmd_get_rule(session, BASE_URL, args(id='r1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/rules/r1'


def test_groups_list_roles_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list_roles(session, BASE_URL, args(id='grp1', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/grp1/roles'


def test_groups_get_role_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'role1'})
    groups.cmd_get_role(session, BASE_URL, args(id='grp1', role_id='role1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/grp1/roles/role1'


def test_groups_list_role_app_targets_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list_role_app_targets(session, BASE_URL, args(id='grp1', role_id='role1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/grp1/roles/role1/targets/catalog/apps'


def test_groups_list_role_group_targets_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list_role_group_targets(session, BASE_URL, args(id='grp1', role_id='role1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/grp1/roles/role1/targets/groups'


# ---------------------------------------------------------------------------
# apps.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def apps():
    return import_script('okta-apps', 'apps.py')


def test_apps_list_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list(session, BASE_URL, args(filter=None, q=None, expand=None, use_optimization=False, always_include_vpn_settings=False, include_non_deleted=False, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps'


def test_apps_list_passes_filter_param(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list(session, BASE_URL, args(filter='status eq "ACTIVE"', q=None, expand=None, use_optimization=False, always_include_vpn_settings=False, include_non_deleted=False, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'status eq "ACTIVE"'}


def test_apps_list_no_filter_sends_empty_params(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list(session, BASE_URL, args(filter=None, q=None, expand=None, use_optimization=False, always_include_vpn_settings=False, include_non_deleted=False, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_apps_list_rejects_filter_and_q_together(apps):
    with pytest.raises(SystemExit):
        apps.main.__globals__['__name__'] = '__main__'
        import sys
        old_argv = sys.argv
        sys.argv = ['apps.py', 'list', '--filter', 'status eq "ACTIVE"', '--q', 'okta']
        try:
            apps.main()
        finally:
            sys.argv = old_argv


def test_apps_get_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'app1'})
    apps.cmd_get(session, BASE_URL, args(id='app1', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1'


def test_apps_get_users_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_get_users(session, BASE_URL, args(id='app1', q=None, expand=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/users'


def test_apps_get_groups_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_get_groups(session, BASE_URL, args(id='app1', q=None, expand=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/groups'


def test_apps_get_group_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'grp1'})
    apps.cmd_get_group(session, BASE_URL, args(id='app1', group_id='grp1', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/groups/grp1'


def test_apps_get_connection_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({})
    apps.cmd_get_connection(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/connections/default'


def test_apps_get_connection_jwks_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({})
    apps.cmd_get_connection_jwks(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/connections/default/jwks'


def test_apps_list_csrs_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_csrs(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/credentials/csrs'


def test_apps_get_csr_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'csr1'})
    apps.cmd_get_csr(session, BASE_URL, args(id='app1', csr_id='csr1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/credentials/csrs/csr1'


def test_apps_list_jwks_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_jwks(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/credentials/jwks'


def test_apps_get_jwk_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'kid': 'key1'})
    apps.cmd_get_jwk(session, BASE_URL, args(id='app1', key_id='key1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/credentials/jwks/key1'


def test_apps_list_keys_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_keys(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/credentials/keys'


def test_apps_get_key_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'kid': 'key1'})
    apps.cmd_get_key(session, BASE_URL, args(id='app1', key_id='key1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/credentials/keys/key1'


def test_apps_list_secrets_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_secrets(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/credentials/secrets'


def test_apps_get_secret_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'sec1'})
    apps.cmd_get_secret(session, BASE_URL, args(id='app1', secret_id='sec1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/credentials/secrets/sec1'


def test_apps_list_cwo_connections_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_cwo_connections(session, BASE_URL, args(
        id='app1', status=None, requesting_app_id=None, resource_app_id=None,
        active_apps_only=False, requesting_app_name=None, resource_app_name=None, limit=None,
    ))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/cwo/connections'


def test_apps_get_cwo_connection_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'conn1'})
    apps.cmd_get_cwo_connection(session, BASE_URL, args(id='app1', connection_id='conn1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/cwo/connections/conn1'


def test_apps_list_features_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_features(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/features'


def test_apps_get_feature_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'name': 'feat1'})
    apps.cmd_get_feature(session, BASE_URL, args(id='app1', feature_name='feat1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/features/feat1'


def test_apps_list_federated_claims_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_federated_claims(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/federated-claims'


def test_apps_get_federated_claim_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'claim1'})
    apps.cmd_get_federated_claim(session, BASE_URL, args(id='app1', claim_id='claim1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/federated-claims/claim1'


def test_apps_list_grants_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_grants(session, BASE_URL, args(id='app1', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/grants'


def test_apps_get_grant_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'grant1'})
    apps.cmd_get_grant(session, BASE_URL, args(id='app1', grant_id='grant1', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/grants/grant1'


def test_apps_list_group_push_mappings_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_group_push_mappings(session, BASE_URL, args(id='app1', last_updated=None, source_group_id=None, status=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/group-push/mappings'


def test_apps_get_group_push_mapping_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'map1'})
    apps.cmd_get_group_push_mapping(session, BASE_URL, args(id='app1', mapping_id='map1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/group-push/mappings/map1'


def test_apps_list_interclient_allowed_apps_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_interclient_allowed_apps(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/interclient-allowed-apps'


def test_apps_list_interclient_target_apps_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_interclient_target_apps(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/interclient-target-apps'


def test_apps_get_saml_metadata_calls_correct_url_and_params(apps):
    session = MagicMock()
    resp = MagicMock()
    resp.text = '<EntityDescriptor/>'
    session.get.return_value = resp
    result = apps.cmd_get_saml_metadata(session, BASE_URL, args(id='app1', kid='key1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/sso/saml/metadata'
    assert session.get.call_args[1]['params'] == {'kid': 'key1'}
    assert session.get.call_args[1]['headers'] == {'Accept': 'text/xml'}
    assert result == {'metadata': '<EntityDescriptor/>'}


def test_apps_list_tokens_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_tokens(session, BASE_URL, args(id='app1', expand=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/tokens'


def test_apps_get_token_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'tok1'})
    apps.cmd_get_token(session, BASE_URL, args(id='app1', token_id='tok1', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/tokens/tok1'


def test_apps_get_user_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'user1'})
    apps.cmd_get_user(session, BASE_URL, args(id='app1', user_id='user1', expand=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/users/user1'


# ---------------------------------------------------------------------------
# network_zones.py — --usage/--system are translated into a filter expression
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def network_zones():
    return import_script('okta-network-zones', 'network_zones.py')


def test_network_zones_list_calls_correct_url(network_zones):
    session = MagicMock()
    session.get.return_value = make_response([])
    network_zones.cmd_list(session, BASE_URL, args(usage=None, system=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/zones'


def test_network_zones_list_no_filter_sends_empty_params(network_zones):
    session = MagicMock()
    session.get.return_value = make_response([])
    network_zones.cmd_list(session, BASE_URL, args(usage=None, system=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_network_zones_list_usage_builds_filter_expression(network_zones):
    session = MagicMock()
    session.get.return_value = make_response([])
    network_zones.cmd_list(session, BASE_URL, args(usage='POLICY', system=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'usage eq "POLICY"'}


def test_network_zones_list_system_builds_filter_expression(network_zones):
    session = MagicMock()
    session.get.return_value = make_response([])
    network_zones.cmd_list(session, BASE_URL, args(usage=None, system=True, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'system eq true'}


def test_network_zones_get_calls_correct_url(network_zones):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'nzo1'})
    network_zones.cmd_get(session, BASE_URL, args(id='nzo1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/zones/nzo1'


# ---------------------------------------------------------------------------
# device_assurance.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def device_assurance():
    return import_script('okta-device-assurance', 'device_assurance.py')


def test_device_assurance_list_calls_correct_url(device_assurance):
    session = MagicMock()
    session.get.return_value = make_response([])
    device_assurance.cmd_list(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/device-assurances'


def test_device_assurance_get_calls_correct_url(device_assurance):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'dap1'})
    device_assurance.cmd_get(session, BASE_URL, args(id='dap1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/device-assurances/dap1'


# ---------------------------------------------------------------------------
# device_posture.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def device_posture():
    return import_script('okta-device-posture', 'device_posture.py')


def test_device_posture_list_calls_correct_url(device_posture):
    session = MagicMock()
    session.get.return_value = make_response([])
    device_posture.cmd_list(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/device-posture-checks'


def test_device_posture_get_calls_correct_url(device_posture):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'dpc1'})
    device_posture.cmd_get(session, BASE_URL, args(id='dpc1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/device-posture-checks/dpc1'


def test_device_posture_list_defaults_calls_correct_url(device_posture):
    session = MagicMock()
    session.get.return_value = make_response([])
    device_posture.cmd_list_defaults(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/device-posture-checks/default'


# ---------------------------------------------------------------------------
# api_tokens.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def api_tokens():
    return import_script('okta-api-tokens', 'api_tokens.py')


def test_api_tokens_list_calls_correct_url(api_tokens):
    session = MagicMock()
    session.get.return_value = make_response([])
    api_tokens.cmd_list(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/api-tokens'


def test_api_tokens_get_calls_correct_url(api_tokens):
    session = MagicMock()
    session.get.return_value = make_response({'id': '00T1'})
    api_tokens.cmd_get(session, BASE_URL, args(id='00T1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/api-tokens/00T1'


# ---------------------------------------------------------------------------
# sessions.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def sessions():
    return import_script('okta-sessions', 'sessions.py')


def test_sessions_get_calls_correct_url(sessions):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'sess1'})
    sessions.cmd_get(session, BASE_URL, args(id='sess1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/sessions/sess1'


# ---------------------------------------------------------------------------
# iam.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def iam():
    return import_script('okta-iam', 'iam.py')


def test_iam_list_unwraps_roles_key(iam):
    session = MagicMock()
    session.get.return_value = make_response({'roles': [{'id': 'r1'}]})
    result = iam.cmd_list(session, BASE_URL, args(limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/roles'
    assert result == [{'id': 'r1'}]


def test_iam_get_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'r1'})
    iam.cmd_get(session, BASE_URL, args(role_id='r1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/roles/r1'


def test_iam_list_permissions_unwraps_permissions_key(iam):
    session = MagicMock()
    session.get.return_value = make_response({'permissions': [{'label': 'okta.users.read'}]})
    result = iam.cmd_list_permissions(session, BASE_URL, args(role_id='r1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/roles/r1/permissions'
    assert result == [{'label': 'okta.users.read'}]


def test_iam_get_permission_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'label': 'okta.users.read'})
    iam.cmd_get_permission(session, BASE_URL, args(role_id='r1', permission_type='okta.users.read'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/roles/r1/permissions/okta.users.read'


def test_iam_list_assignees_unwraps_value_key(iam):
    session = MagicMock()
    session.get.return_value = make_response({'value': [{'id': 'u1'}]})
    result = iam.cmd_list_assignees(session, BASE_URL, args(limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/assignees/users'
    assert result == [{'id': 'u1'}]


def test_iam_list_resource_sets_unwraps_hyphenated_key(iam):
    session = MagicMock()
    session.get.return_value = make_response({'resource-sets': [{'id': 'rs1'}]})
    result = iam.cmd_list_resource_sets(session, BASE_URL, args(limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/resource-sets'
    assert result == [{'id': 'rs1'}]


def test_iam_get_resource_set_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'rs1'})
    iam.cmd_get_resource_set(session, BASE_URL, args(resource_set_id='rs1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/resource-sets/rs1'


def test_iam_list_bindings_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'roles': []})
    iam.cmd_list_bindings(session, BASE_URL, args(resource_set_id='rs1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/resource-sets/rs1/bindings'


def test_iam_get_binding_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'b1'})
    iam.cmd_get_binding(session, BASE_URL, args(resource_set_id='rs1', role_id='r1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/resource-sets/rs1/bindings/r1'


def test_iam_list_binding_members_unwraps_members_key(iam):
    session = MagicMock()
    session.get.return_value = make_response({'members': [{'id': 'm1'}]})
    result = iam.cmd_list_binding_members(
        session, BASE_URL, args(resource_set_id='rs1', role_id='r1', limit=None)
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/resource-sets/rs1/bindings/r1/members'
    assert result == [{'id': 'm1'}]


def test_iam_get_binding_member_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'm1'})
    iam.cmd_get_binding_member(
        session, BASE_URL, args(resource_set_id='rs1', role_id='r1', member_id='m1')
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/resource-sets/rs1/bindings/r1/members/m1'


def test_iam_list_resources_unwraps_resources_key(iam):
    session = MagicMock()
    session.get.return_value = make_response({'resources': [{'id': 'res1'}]})
    result = iam.cmd_list_resources(session, BASE_URL, args(resource_set_id='rs1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/resource-sets/rs1/resources'
    assert result == [{'id': 'res1'}]


def test_iam_get_resource_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'res1'})
    iam.cmd_get_resource(session, BASE_URL, args(resource_set_id='rs1', resource_id='res1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/resource-sets/rs1/resources/res1'


def test_iam_list_bundles_unwraps_bundles_key(iam):
    session = MagicMock()
    session.get.return_value = make_response({'bundles': [{'id': 'bun1'}]})
    result = iam.cmd_list_bundles(session, BASE_URL, args(limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/governance/bundles'
    assert result == [{'id': 'bun1'}]


def test_iam_get_bundle_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'bun1'})
    iam.cmd_get_bundle(session, BASE_URL, args(bundle_id='bun1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/governance/bundles/bun1'


def test_iam_list_bundle_entitlements_unwraps_entitlements_key(iam):
    session = MagicMock()
    session.get.return_value = make_response({'entitlements': [{'id': 'ent1'}]})
    result = iam.cmd_list_bundle_entitlements(session, BASE_URL, args(bundle_id='bun1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/governance/bundles/bun1/entitlements'
    assert result == [{'id': 'ent1'}]


def test_iam_list_bundle_entitlement_values_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'entitlementValues': [{'id': 'val1'}]})
    result = iam.cmd_list_bundle_entitlement_values(
        session, BASE_URL, args(bundle_id='bun1', entitlement_id='ent1', limit=None)
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/governance/bundles/bun1/entitlements/ent1/values'
    assert result == [{'id': 'val1'}]


def test_iam_get_opt_in_status_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'optInStatus': 'OPTED_IN'})
    iam.cmd_get_opt_in_status(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/iam/governance/optIn'


def test_iam_list_role_subscriptions_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response([{'notificationType': 'CONNECTOR_AGENT'}])
    result = iam.cmd_list_role_subscriptions(session, BASE_URL, args(role_ref='SUPER_ADMIN'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/roles/SUPER_ADMIN/subscriptions'
    assert result == [{'notificationType': 'CONNECTOR_AGENT'}]


def test_iam_get_role_subscription_calls_correct_url(iam):
    session = MagicMock()
    session.get.return_value = make_response({'notificationType': 'CONNECTOR_AGENT'})
    iam.cmd_get_role_subscription(
        session, BASE_URL, args(role_ref='SUPER_ADMIN', notification_type='CONNECTOR_AGENT')
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/roles/SUPER_ADMIN/subscriptions/CONNECTOR_AGENT'


# ---------------------------------------------------------------------------
# authenticators.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def authenticators():
    return import_script('okta-authenticators', 'authenticators.py')


def test_authenticators_list_calls_correct_url(authenticators):
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'aut1'}])
    result = authenticators.cmd_list(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authenticators'
    assert result == [{'id': 'aut1'}]


def test_authenticators_get_calls_correct_url(authenticators):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'aut1'})
    authenticators.cmd_get(session, BASE_URL, args(authenticator_id='aut1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authenticators/aut1'


def test_authenticators_list_methods_calls_correct_url(authenticators):
    session = MagicMock()
    session.get.return_value = make_response([{'type': 'sms'}])
    result = authenticators.cmd_list_methods(session, BASE_URL, args(authenticator_id='aut1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authenticators/aut1/methods'
    assert result == [{'type': 'sms'}]


def test_authenticators_get_method_calls_correct_url(authenticators):
    session = MagicMock()
    session.get.return_value = make_response({'type': 'sms'})
    authenticators.cmd_get_method(session, BASE_URL, args(authenticator_id='aut1', method_type='sms'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authenticators/aut1/methods/sms'


def test_authenticators_list_aaguids_calls_correct_url(authenticators):
    session = MagicMock()
    session.get.return_value = make_response([{'aaguid': 'abc-123'}])
    result = authenticators.cmd_list_aaguids(session, BASE_URL, args(authenticator_id='aut1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authenticators/aut1/aaguids'
    assert result == [{'aaguid': 'abc-123'}]


def test_authenticators_get_aaguid_calls_correct_url(authenticators):
    session = MagicMock()
    session.get.return_value = make_response({'aaguid': 'abc-123'})
    authenticators.cmd_get_aaguid(session, BASE_URL, args(authenticator_id='aut1', aaguid='abc-123'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authenticators/aut1/aaguids/abc-123'


# ---------------------------------------------------------------------------
# behaviors.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def behaviors():
    return import_script('okta-behaviors', 'behaviors.py')


def test_behaviors_list_calls_correct_url(behaviors):
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'bh1'}])
    result = behaviors.cmd_list(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/behaviors'
    assert result == [{'id': 'bh1'}]


def test_behaviors_get_calls_correct_url(behaviors):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'bh1'})
    behaviors.cmd_get(session, BASE_URL, args(id='bh1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/behaviors/bh1'


# ---------------------------------------------------------------------------
# authorization_servers.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def authorization_servers():
    return import_script('okta-authorization-servers', 'authorization_servers.py')


def test_authorization_servers_list_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'aus1'}])
    result = authorization_servers.cmd_list(session, BASE_URL, args(q=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers'
    assert result == [{'id': 'aus1'}]


def test_authorization_servers_list_passes_q_param(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([])
    authorization_servers.cmd_list(session, BASE_URL, args(q='api', limit=None))
    assert session.get.call_args[1]['params'] == {'q': 'api'}


def test_authorization_servers_get_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'aus1'})
    authorization_servers.cmd_get(session, BASE_URL, args(id='aus1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1'


def test_authorization_servers_list_associated_servers_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([])
    authorization_servers.cmd_list_associated_servers(
        session, BASE_URL, args(id='aus1', trusted=None, q=None, limit=None)
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/associatedServers'


def test_authorization_servers_list_associated_servers_passes_trusted_param(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([])
    authorization_servers.cmd_list_associated_servers(
        session, BASE_URL, args(id='aus1', trusted='true', q=None, limit=None)
    )
    assert session.get.call_args[1]['params'].get('trusted') == 'true'


def test_authorization_servers_list_claims_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'cl1'}])
    result = authorization_servers.cmd_list_claims(session, BASE_URL, args(id='aus1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/claims'
    assert result == [{'id': 'cl1'}]


def test_authorization_servers_list_claims_follows_link_header(authorization_servers):
    session = MagicMock()
    next_url = f'{BASE_URL}/api/v1/authorizationServers/aus1/claims?after=cl1'
    session.get.side_effect = [
        make_response([{'id': 'cl1'}], next_url=next_url),
        make_response([{'id': 'cl2'}]),
    ]
    result = authorization_servers.cmd_list_claims(session, BASE_URL, args(id='aus1', limit=None))
    assert result == [{'id': 'cl1'}, {'id': 'cl2'}]
    assert session.get.call_count == 2


def test_authorization_servers_get_claim_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'cl1'})
    authorization_servers.cmd_get_claim(session, BASE_URL, args(id='aus1', claim_id='cl1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/claims/cl1'


def test_authorization_servers_list_clients_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([{'client_id': 'c1'}])
    result = authorization_servers.cmd_list_clients(session, BASE_URL, args(id='aus1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/clients'
    assert result == [{'client_id': 'c1'}]


def test_authorization_servers_list_tokens_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([])
    authorization_servers.cmd_list_tokens(
        session, BASE_URL, args(id='aus1', client_id='c1', expand=None, limit=None)
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/clients/c1/tokens'


def test_authorization_servers_list_tokens_passes_expand_param(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([])
    authorization_servers.cmd_list_tokens(
        session, BASE_URL, args(id='aus1', client_id='c1', expand='scope', limit=None)
    )
    assert session.get.call_args[1]['params'].get('expand') == 'scope'


def test_authorization_servers_get_token_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 't1'})
    authorization_servers.cmd_get_token(
        session, BASE_URL, args(id='aus1', client_id='c1', token_id='t1', expand=None)
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/clients/c1/tokens/t1'


def test_authorization_servers_list_keys_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([{'kid': 'k1'}])
    result = authorization_servers.cmd_list_keys(session, BASE_URL, args(id='aus1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/credentials/keys'
    assert result == [{'kid': 'k1'}]


def test_authorization_servers_get_key_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response({'kid': 'k1'})
    authorization_servers.cmd_get_key(session, BASE_URL, args(id='aus1', key_id='k1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/credentials/keys/k1'


def test_authorization_servers_list_policies_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'p1'}])
    result = authorization_servers.cmd_list_policies(session, BASE_URL, args(id='aus1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/policies'
    assert result == [{'id': 'p1'}]


def test_authorization_servers_get_policy_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'p1'})
    authorization_servers.cmd_get_policy(session, BASE_URL, args(id='aus1', policy_id='p1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/policies/p1'


def test_authorization_servers_list_policy_rules_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([{'id': 'r1'}])
    result = authorization_servers.cmd_list_policy_rules(
        session, BASE_URL, args(id='aus1', policy_id='p1', limit=None)
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/policies/p1/rules'
    assert result == [{'id': 'r1'}]


def test_authorization_servers_get_policy_rule_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'r1'})
    authorization_servers.cmd_get_policy_rule(
        session, BASE_URL, args(id='aus1', policy_id='p1', rule_id='r1')
    )
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/policies/p1/rules/r1'


def test_authorization_servers_list_resource_server_keys_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([{'kid': 'rsk1'}])
    result = authorization_servers.cmd_list_resource_server_keys(session, BASE_URL, args(id='aus1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/resourceservercredentials/keys'
    assert result == [{'kid': 'rsk1'}]


def test_authorization_servers_get_resource_server_key_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response({'kid': 'rsk1'})
    authorization_servers.cmd_get_resource_server_key(session, BASE_URL, args(id='aus1', key_id='rsk1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/resourceservercredentials/keys/rsk1'


def test_authorization_servers_list_scopes_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([])
    authorization_servers.cmd_list_scopes(session, BASE_URL, args(id='aus1', q=None, filter=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/scopes'


def test_authorization_servers_list_scopes_passes_filter_param(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response([])
    authorization_servers.cmd_list_scopes(
        session, BASE_URL, args(id='aus1', q=None, filter='status eq "ACTIVE"', limit=None)
    )
    assert session.get.call_args[1]['params'].get('filter') == 'status eq "ACTIVE"'


def test_authorization_servers_get_scope_calls_correct_url(authorization_servers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 's1'})
    authorization_servers.cmd_get_scope(session, BASE_URL, args(id='aus1', scope_id='s1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/authorizationServers/aus1/scopes/s1'


# ---------------------------------------------------------------------------
# identity_providers.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def identity_providers():
    return import_script('okta-identity-providers', 'identity_providers.py')


def test_identity_providers_list_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list(session, BASE_URL, args(q=None, type=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps'


def test_identity_providers_list_no_filters_sends_empty_params(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list(session, BASE_URL, args(q=None, type=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_identity_providers_list_passes_q_and_type_params(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list(session, BASE_URL, args(q='Example SAML', type='SAML2', limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'q': 'Example SAML', 'type': 'SAML2'}


def test_identity_providers_get_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'idp1'})
    identity_providers.cmd_get(session, BASE_URL, args(idp_id='idp1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1'


def test_identity_providers_list_keys_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list_keys(session, BASE_URL, args(limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/credentials/keys'


def test_identity_providers_get_key_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response({'kid': 'k1'})
    identity_providers.cmd_get_key(session, BASE_URL, args(kid='k1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/credentials/keys/k1'


def test_identity_providers_list_csrs_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list_csrs(session, BASE_URL, args(idp_id='idp1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1/credentials/csrs'


def test_identity_providers_get_csr_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'csr1'})
    identity_providers.cmd_get_csr(session, BASE_URL, args(idp_id='idp1', idp_csr_id='csr1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1/credentials/csrs/csr1'


def test_identity_providers_list_signing_keys_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list_signing_keys(session, BASE_URL, args(idp_id='idp1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1/credentials/keys'


def test_identity_providers_get_active_signing_key_calls_correct_url(identity_providers):
    session = MagicMock()
    resp = make_response([{'kid': 'k1'}])
    resp.status_code = 200
    session.get.return_value = resp
    result = identity_providers.cmd_get_active_signing_key(session, BASE_URL, args(idp_id='idp1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1/credentials/keys/active'
    assert result == [{'kid': 'k1'}]


def test_identity_providers_get_active_signing_key_handles_204(identity_providers):
    session = MagicMock()
    resp = make_response(None)
    resp.status_code = 204
    session.get.return_value = resp
    result = identity_providers.cmd_get_active_signing_key(session, BASE_URL, args(idp_id='idp1'))
    assert result == []


def test_identity_providers_get_signing_key_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response({'kid': 'k1'})
    identity_providers.cmd_get_signing_key(session, BASE_URL, args(idp_id='idp1', kid='k1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1/credentials/keys/k1'


def test_identity_providers_list_users_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list_users(session, BASE_URL, args(idp_id='idp1', q=None, expand=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1/users'


def test_identity_providers_list_users_no_filters_sends_empty_params(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list_users(session, BASE_URL, args(idp_id='idp1', q=None, expand=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_identity_providers_list_users_passes_q_and_expand_params(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list_users(
        session, BASE_URL, args(idp_id='idp1', q='jackson', expand='user', limit=None)
    )
    params = session.get.call_args[1]['params']
    assert params == {'q': 'jackson', 'expand': 'user'}


def test_identity_providers_get_user_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'u1'})
    identity_providers.cmd_get_user(session, BASE_URL, args(idp_id='idp1', user_id='u1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1/users/u1'


def test_identity_providers_list_tokens_calls_correct_url(identity_providers):
    session = MagicMock()
    session.get.return_value = make_response([])
    identity_providers.cmd_list_tokens(session, BASE_URL, args(idp_id='idp1', user_id='u1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/idps/idp1/users/u1/credentials/tokens'


# ---------------------------------------------------------------------------
# schemas.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def schemas():
    return import_script('okta-schemas', 'schemas.py')


def test_schemas_list_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response([])
    schemas.cmd_list(session, BASE_URL, args(source_id=None, target_id=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/mappings'


def test_schemas_list_no_filters_sends_empty_params(schemas):
    session = MagicMock()
    session.get.return_value = make_response([])
    schemas.cmd_list(session, BASE_URL, args(source_id=None, target_id=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_schemas_list_passes_source_and_target_id(schemas):
    session = MagicMock()
    session.get.return_value = make_response([])
    schemas.cmd_list(session, BASE_URL, args(source_id='oty1', target_id='0oa1', limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'sourceId': 'oty1', 'targetId': '0oa1'}


def test_schemas_get_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'prm1'})
    schemas.cmd_get(session, BASE_URL, args(id='prm1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/mappings/prm1'


def test_schemas_get_app_user_schema_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'schema1'})
    schemas.cmd_get_app_user_schema(session, BASE_URL, args(app_id='0oa1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/schemas/apps/0oa1/default'


def test_schemas_get_group_schema_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'gschema1'})
    schemas.cmd_get_group_schema(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/schemas/group/default'


def test_schemas_list_log_stream_schemas_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response([])
    schemas.cmd_list_log_stream_schemas(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/schemas/logStream'


def test_schemas_get_log_stream_schema_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'lsschema1'})
    schemas.cmd_get_log_stream_schema(session, BASE_URL, args(log_stream_type='aws_eventbridge'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/schemas/logStream/aws_eventbridge'


def test_schemas_list_linked_objects_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response([])
    schemas.cmd_list_linked_objects(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/schemas/user/linkedObjects'


def test_schemas_get_linked_object_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response({'primary': {'name': 'manager'}})
    schemas.cmd_get_linked_object(session, BASE_URL, args(name='manager'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/schemas/user/linkedObjects/manager'


def test_schemas_get_user_schema_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'uschema1'})
    schemas.cmd_get_user_schema(session, BASE_URL, args(schema_id='default'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/schemas/user/default'


def test_schemas_list_user_types_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response([])
    schemas.cmd_list_user_types(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/types/user'


def test_schemas_get_user_type_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'default'})
    schemas.cmd_get_user_type(session, BASE_URL, args(type_id='default'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/types/user/default'


def test_schemas_list_ui_schemas_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response([])
    schemas.cmd_list_ui_schemas(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/uischemas'


def test_schemas_get_ui_schema_calls_correct_url(schemas):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'uis1'})
    schemas.cmd_get_ui_schema(session, BASE_URL, args(id='uis1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/meta/uischemas/uis1'


# ---------------------------------------------------------------------------
# security.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def security():
    return import_script('okta-security', 'security.py')


def test_security_get_threat_insight_config_calls_correct_url(security):
    session = MagicMock()
    session.get.return_value = make_response({'action': 'block'})
    security.cmd_get_threat_insight_config(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/threats/configuration'


def test_security_list_security_events_providers_calls_correct_url(security):
    session = MagicMock()
    session.get.return_value = make_response([])
    security.cmd_list_security_events_providers(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/security-events-providers'


def test_security_get_security_events_provider_calls_correct_url(security):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'sse1'})
    security.cmd_get_security_events_provider(session, BASE_URL, args(id='sse1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/security-events-providers/sse1'


def test_security_get_ssf_streams_calls_correct_url(security):
    session = MagicMock()
    session.get.return_value = make_response([])
    security.cmd_get_ssf_streams(session, BASE_URL, args(stream_id=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/ssf/stream'


def test_security_get_ssf_streams_no_stream_id_sends_no_params(security):
    session = MagicMock()
    session.get.return_value = make_response([])
    security.cmd_get_ssf_streams(session, BASE_URL, args(stream_id=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_security_get_ssf_streams_passes_stream_id(security):
    session = MagicMock()
    session.get.return_value = make_response({'stream_id': 'esc1'})
    security.cmd_get_ssf_streams(session, BASE_URL, args(stream_id='esc1'))
    params = session.get.call_args[1]['params']
    assert params == {'stream_id': 'esc1'}


def test_security_get_ssf_stream_status_calls_correct_url(security):
    session = MagicMock()
    session.get.return_value = make_response({'status': 'enabled'})
    security.cmd_get_ssf_stream_status(session, BASE_URL, args(stream_id='esc1'))
    url = session.get.call_args[0][0]
    params = session.get.call_args[1]['params']
    assert url == f'{BASE_URL}/api/v1/ssf/stream/status'
    assert params == {'stream_id': 'esc1'}


def test_security_get_bot_protection_config_calls_correct_url(security):
    session = MagicMock()
    session.get.return_value = make_response({'mode': 'ENFORCED'})
    security.cmd_get_bot_protection_config(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/bot-protection/configuration'


# ---------------------------------------------------------------------------
# attack_protection.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def attack_protection():
    return import_script('okta-attack-protection', 'attack_protection.py')


def test_attack_protection_get_authenticator_settings_calls_correct_url(attack_protection):
    session = MagicMock()
    session.get.return_value = make_response({'verifyKnowledgeSecondWhen2faRequired': False})
    attack_protection.cmd_get_authenticator_settings(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/attack-protection/api/v1/authenticator-settings'


def test_attack_protection_get_user_lockout_settings_calls_correct_url(attack_protection):
    session = MagicMock()
    session.get.return_value = make_response({'preventBruteForceLockoutFromUnknownDevices': False})
    attack_protection.cmd_get_user_lockout_settings(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/attack-protection/api/v1/user-lockout-settings'


# ---------------------------------------------------------------------------
# device_integrations.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def device_integrations():
    return import_script('okta-device-integrations', 'device_integrations.py')


def test_device_integrations_list_calls_correct_url(device_integrations):
    session = MagicMock()
    session.get.return_value = make_response([])
    device_integrations.cmd_list(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/device-integrations'


def test_device_integrations_get_calls_correct_url(device_integrations):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'din1'})
    device_integrations.cmd_get(session, BASE_URL, args(id='din1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/device-integrations/din1'


# ---------------------------------------------------------------------------
# org_settings.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def org_settings():
    return import_script('okta-org-settings', 'org_settings.py')


def test_org_settings_get_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'org1'})
    org_settings.cmd_get(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org'


def test_org_settings_list_contact_types_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response([])
    org_settings.cmd_list_contact_types(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/contacts'


def test_org_settings_get_contact_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'userId': 'u1'})
    org_settings.cmd_get_contact(session, BASE_URL, args(contact_type='BILLING'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/contacts/BILLING'


def test_org_settings_get_captcha_settings_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({})
    org_settings.cmd_get_captcha_settings(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/captcha'


def test_org_settings_get_third_party_admin_setting_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'thirdPartyAdmin': False})
    org_settings.cmd_get_third_party_admin_setting(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/orgSettings/thirdPartyAdminSetting'


def test_org_settings_get_preferences_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'showEndUserFooter': True})
    org_settings.cmd_get_preferences(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/preferences'


def test_org_settings_get_aerial_consent_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'accountId': 'a1'})
    org_settings.cmd_get_aerial_consent(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/privacy/aerial'


def test_org_settings_get_aerial_consent_returns_none_on_404(org_settings):
    session = MagicMock()
    resp = make_response(None)
    resp.status_code = 404
    session.get.return_value = resp
    result = org_settings.cmd_get_aerial_consent(session, BASE_URL, args())
    assert result is None


def test_org_settings_get_communication_settings_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'optOutEmailUsers': False})
    org_settings.cmd_get_communication_settings(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/privacy/oktaCommunication'


def test_org_settings_get_support_settings_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'support': 'DISABLED'})
    org_settings.cmd_get_support_settings(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/privacy/oktaSupport'


def test_org_settings_list_support_cases_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'supportCases': []})
    org_settings.cmd_list_support_cases(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/privacy/oktaSupport/cases'


def test_org_settings_get_auto_assign_admin_app_setting_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'autoAssignAdminAppSetting': False})
    org_settings.cmd_get_auto_assign_admin_app_setting(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/settings/autoAssignAdminAppSetting'


def test_org_settings_get_client_privileges_setting_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'clientPrivilegesSetting': False})
    org_settings.cmd_get_client_privileges_setting(session, BASE_URL, args())
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/settings/clientPrivilegesSetting'


def test_org_settings_list_yubikey_tokens_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response([])
    org_settings.cmd_list_yubikey_tokens(session, BASE_URL, args(filter=None, limit=None, expand_user=False, sort_by=None, sort_order=None))
    url = session.get.call_args[0][0]
    params = session.get.call_args[1]['params']
    assert url == f'{BASE_URL}/api/v1/org/factors/yubikey_token/tokens'
    assert params == {}


def test_org_settings_list_yubikey_tokens_passes_filter_and_expand(org_settings):
    session = MagicMock()
    session.get.return_value = make_response([])
    org_settings.cmd_list_yubikey_tokens(
        session, BASE_URL, args(filter='status eq "ACTIVE"', limit=None, expand_user=True, sort_by=None, sort_order=None)
    )
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'status eq "ACTIVE"', 'expand': 'user'}


def test_org_settings_get_yubikey_token_calls_correct_url(org_settings):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'yk1'})
    org_settings.cmd_get_yubikey_token(session, BASE_URL, args(id='yk1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/org/factors/yubikey_token/tokens/yk1'


@pytest.fixture(scope='module')
def realms():
    return import_script('okta-realms', 'realms.py')


def test_realms_list_realms_calls_correct_url(realms):
    session = MagicMock()
    session.get.return_value = make_response([])
    realms.cmd_list_realms(session, BASE_URL, args(search=None, sort_by=None, sort_order=None, limit=None))
    url = session.get.call_args[0][0]
    params = session.get.call_args[1]['params']
    assert url == f'{BASE_URL}/api/v1/realms'
    assert params == {}


def test_realms_list_realms_passes_search_and_sort(realms):
    session = MagicMock()
    session.get.return_value = make_response([])
    realms.cmd_list_realms(
        session, BASE_URL, args(search='profile.name co "Partner"', sort_by='profile.name', sort_order='asc', limit=None)
    )
    params = session.get.call_args[1]['params']
    assert params == {'search': 'profile.name co "Partner"', 'sortBy': 'profile.name', 'sortOrder': 'asc'}


def test_realms_get_realm_calls_correct_url(realms):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'guo1'})
    realms.cmd_get_realm(session, BASE_URL, args(id='guo1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/realms/guo1'


def test_realms_list_realm_assignments_calls_correct_url(realms):
    session = MagicMock()
    session.get.return_value = make_response([])
    realms.cmd_list_realm_assignments(session, BASE_URL, args(limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/realm-assignments'


def test_realms_get_realm_assignment_calls_correct_url(realms):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'rul1'})
    realms.cmd_get_realm_assignment(session, BASE_URL, args(id='rul1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/realm-assignments/rul1'


def test_realms_list_realm_assignment_operations_calls_correct_url(realms):
    session = MagicMock()
    session.get.return_value = make_response([])
    realms.cmd_list_realm_assignment_operations(session, BASE_URL, args(limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/realm-assignments/operations'
