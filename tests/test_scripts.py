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


def test_policies_get_rules_calls_correct_url(policies):
    session = MagicMock()
    session.get.return_value = make_response([])
    policies.cmd_get_rules(session, BASE_URL, args(id='pol123'))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/policies/pol123/rules'


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


def test_login_failures_makes_two_requests(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args())
    assert session.get.call_count == 2


def test_login_failures_queries_failure_and_deny_outcomes(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args())
    filters = [call[1]['params']['filter'] for call in session.get.call_args_list]
    assert any('FAILURE' in f for f in filters)
    assert any('DENY' in f for f in filters)


def test_login_failures_defaults_to_24h_window(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args())
    since = session.get.call_args_list[0][1]['params']['since']
    assert since is not None


def test_login_failures_respects_explicit_since(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args(since='2024-01-01T00:00:00Z'))
    since = session.get.call_args_list[0][1]['params']['since']
    assert since == '2024-01-01T00:00:00Z'


def test_login_failures_adds_user_filter(logs):
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_login_failures(session, BASE_URL, _failure_args(user='user@example.com'))
    filters = [call[1]['params']['filter'] for call in session.get.call_args_list]
    assert all('actor.alternateId eq "user@example.com"' in f for f in filters)


def test_login_failures_groups_by_event_type(logs):
    events = [
        {'eventType': 'user.session.start', 'outcome': {'result': 'FAILURE'}},
        {'eventType': 'user.session.start', 'outcome': {'result': 'FAILURE'}},
        {'eventType': 'policy.evaluate_sign_on', 'outcome': {'result': 'DENY'}},
    ]
    session = MagicMock()
    session.get.side_effect = [make_response(events[:2]), make_response(events[2:])]
    result = logs.cmd_login_failures(session, BASE_URL, _failure_args())
    assert result['summary']['by_event_type']['user.session.start'] == 2
    assert result['summary']['by_event_type']['policy.evaluate_sign_on'] == 1
    assert result['summary']['by_outcome']['FAILURE'] == 2
    assert result['summary']['by_outcome']['DENY'] == 1
    assert result['summary']['total'] == 3


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


# ---------------------------------------------------------------------------
# groups.py
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def groups():
    return import_script('okta-groups', 'groups.py')


def test_groups_list_calls_correct_url(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter=None, limit=None))
    url = session.get.call_args[0][0]
    assert url == f'{BASE_URL}/api/v1/groups'


def test_groups_list_passes_filter_param(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter='type eq "OKTA_GROUP"', limit=None))
    params = session.get.call_args[1]['params']
    assert params == {'filter': 'type eq "OKTA_GROUP"'}


def test_groups_list_no_filter_sends_empty_params(groups):
    session = MagicMock()
    session.get.return_value = make_response([])
    groups.cmd_list(session, BASE_URL, args(filter=None, limit=None))
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
