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

from conftest import make_response, args

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
    users.cmd_list(session, BASE_URL, args(filter=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/users'


def test_users_list_passes_filter_param(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, args(filter='status eq "ACTIVE"', limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'status eq "ACTIVE"'}


def test_users_list_no_filter_sends_empty_params(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_list(session, BASE_URL, args(filter=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_users_get_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'u1'})
    users.cmd_get(session, BASE_URL, args(id='user@example.com'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/users/user@example.com'


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
    users.cmd_get_enrollments(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/authenticator-enrollments'


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
    users.cmd_get_grants(session, BASE_URL, args(id='u1', scope_id=None, limit=None))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/grants'


def test_users_get_grants_passes_scope_id(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_grants(session, BASE_URL, args(id='u1', scope_id='okta.users.read', limit=None))
    assert session.get.call_args[1]['params'].get('scopeId') == 'okta.users.read'


def test_users_get_grants_no_scope_id_sends_empty_params(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_grants(session, BASE_URL, args(id='u1', scope_id=None, limit=None))
    assert session.get.call_args[1]['params'] == {}


def test_users_get_grant_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_grant(session, BASE_URL, args(id='u1', grant_id='g1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/grants/g1'


def test_users_get_risk_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response({})
    users.cmd_get_risk(session, BASE_URL, args(id='u1'))
    assert session.get.call_args[0][0] == f'{BASE_URL}/api/v1/users/u1/risk'


def test_users_get_roles_calls_correct_url(users):
    session = MagicMock()
    session.get.return_value = make_response([])
    users.cmd_get_roles(session, BASE_URL, args(id='u1'))
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


# ---------------------------------------------------------------------------
# policies.py — --type is required by the Okta API
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def policies():
    return import_script('okta-policies', 'policies.py')


def test_policies_list_passes_type_param(policies):
    session = MagicMock()
    session.get.return_value = make_response([])
    policies.cmd_list(session, BASE_URL, args(type='OKTA_SIGN_ON'))
    params = session.get.call_args[1]['params']
    assert params == {'type': 'OKTA_SIGN_ON'}


def test_policies_get_calls_correct_url(policies):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'pol123'})
    policies.cmd_get(session, BASE_URL, args(id='pol123'))
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
    defaults = dict(since=None, until=None, filter=None, q=None, sort_order=None, limit=None)
    defaults.update(kwargs)
    return args(**defaults)


def _failure_args(**kwargs):
    defaults = dict(since=None, until=None, user=None, limit=None)
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
    devices.cmd_list(session, BASE_URL, args(search='status eq "ACTIVE"', limit=None))
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


# ---------------------------------------------------------------------------
# groups.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def groups():
    return import_script('okta-groups', 'groups.py')


def test_groups_list_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter=None, search=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups'


def test_groups_list_passes_filter_param(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter='type eq "OKTA_GROUP"', search=None, limit=None))
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
    groups.cmd_list(session, BASE_URL, args(filter=None, search='profile.name co "Eng"', limit=None))
    params = session.get.call_args[1]['params']
    assert params.get('search') == 'profile.name co "Eng"'


def test_groups_list_no_filter_sends_empty_params(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter=None, search=None, limit=None))
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
    groups.cmd_get_members(session, BASE_URL, args(id='g1'))
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
    groups.cmd_get_apps(session, BASE_URL, args(id='g1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/g1/apps'


def test_groups_get_owners_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_get_owners(session, BASE_URL, args(id='g1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/g1/owners'


def test_groups_list_rules_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list_rules(session, BASE_URL, args(search=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/rules'


def test_groups_list_rules_passes_search_param(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list_rules(session, BASE_URL, args(search='Engineering', limit=None))
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
    groups.cmd_list_roles(session, BASE_URL, args(id='grp1'))
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
    groups.cmd_list_role_app_targets(session, BASE_URL, args(id='grp1', role_id='role1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups/grp1/roles/role1/targets/catalog/apps'


def test_groups_list_role_group_targets_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list_role_group_targets(session, BASE_URL, args(id='grp1', role_id='role1'))
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
    apps.cmd_list(session, BASE_URL, args(filter=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps'


def test_apps_list_passes_filter_param(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list(session, BASE_URL, args(filter='status eq "ACTIVE"', limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'status eq "ACTIVE"'}


def test_apps_list_no_filter_sends_empty_params(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list(session, BASE_URL, args(filter=None, limit=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_apps_get_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'app1'})
    apps.cmd_get(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1'


def test_apps_get_users_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_get_users(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/users'


def test_apps_get_groups_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_get_groups(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/groups'


def test_apps_get_group_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'grp1'})
    apps.cmd_get_group(session, BASE_URL, args(id='app1', group_id='grp1'))
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
    apps.cmd_list_cwo_connections(session, BASE_URL, args(id='app1', limit=None))
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
    apps.cmd_list_grants(session, BASE_URL, args(id='app1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/grants'


def test_apps_get_grant_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'grant1'})
    apps.cmd_get_grant(session, BASE_URL, args(id='app1', grant_id='grant1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/grants/grant1'


def test_apps_list_group_push_mappings_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_group_push_mappings(session, BASE_URL, args(id='app1', limit=None))
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
    assert result == '<EntityDescriptor/>'


def test_apps_list_tokens_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response([])
    apps.cmd_list_tokens(session, BASE_URL, args(id='app1', limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/tokens'


def test_apps_get_token_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'tok1'})
    apps.cmd_get_token(session, BASE_URL, args(id='app1', token_id='tok1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/tokens/tok1'


def test_apps_get_user_calls_correct_url(apps):
    session = MagicMock()
    session.get.return_value = make_response({'id': 'user1'})
    apps.cmd_get_user(session, BASE_URL, args(id='app1', user_id='user1'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/apps/app1/users/user1'


# ---------------------------------------------------------------------------
# network_zones.py — --type is translated into a filter expression
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def network_zones():
    return import_script('okta-network-zones', 'network_zones.py')


def test_network_zones_list_calls_correct_url(network_zones):
    session = MagicMock()
    session.get.return_value = make_response([])
    network_zones.cmd_list(session, BASE_URL, args(type=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/zones'


def test_network_zones_list_no_type_sends_empty_params(network_zones):
    session = MagicMock()
    session.get.return_value = make_response([])
    network_zones.cmd_list(session, BASE_URL, args(type=None))
    params = session.get.call_args[1]['params']
    assert params == {}


def test_network_zones_list_type_builds_filter_expression(network_zones):
    session = MagicMock()
    session.get.return_value = make_response([])
    network_zones.cmd_list(session, BASE_URL, args(type='IP'))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'type eq "IP"'}


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
