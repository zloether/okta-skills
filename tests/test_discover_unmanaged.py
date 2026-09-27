"""Tests for skills/okta-terraform/scripts/discover_unmanaged.py."""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SCRIPT_PATH = Path(__file__).parents[1] / 'skills' / 'okta-terraform' / 'scripts' / 'discover_unmanaged.py'
_spec = importlib.util.spec_from_file_location('discover_unmanaged', _SCRIPT_PATH)
du = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(du)


# ---------------------------------------------------------------------------
# safe_tf_name
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('label, fallback_id, expected', [
    ('Engineering Team!', '00g1', 'engineering_team'),
    (None, '00g1', '_00g1'),
    ('123abc', '00g1', '_123abc'),
    ('already_valid-name', '00g1', 'already_valid-name'),
    ('---', '00g1', '_00g1'),
    ('...', '00g2', '_00g2'),
])
def test_safe_tf_name(label, fallback_id, expected):
    assert du.safe_tf_name(label, fallback_id) == expected


def test_safe_tf_name_punctuation_only_labels_dont_collide():
    first = du.safe_tf_name('---', 'g1')
    second = du.safe_tf_name('...', 'g2')
    assert first != second


# ---------------------------------------------------------------------------
# walk_state_resources
# ---------------------------------------------------------------------------

def test_walk_state_resources_flattens_child_modules():
    module = {
        'resources': [{'type': 'okta_group', 'values': {'id': 'root1'}}],
        'child_modules': [
            {
                'resources': [{'type': 'okta_group', 'values': {'id': 'child1'}}],
                'child_modules': [
                    {'resources': [{'type': 'okta_group', 'values': {'id': 'grandchild1'}}]},
                ],
            },
        ],
    }
    ids = [r['values']['id'] for r in du.walk_state_resources(module)]
    assert ids == ['root1', 'child1', 'grandchild1']


def test_walk_state_resources_handles_empty_module():
    assert list(du.walk_state_resources({})) == []


# ---------------------------------------------------------------------------
# diff_live_vs_managed
# ---------------------------------------------------------------------------

def test_diff_live_vs_managed_excludes_already_managed():
    live = [{'id': 'g1', 'profile': {'name': 'Engineers'}}, {'id': 'g2', 'profile': {'name': 'Admins'}}]
    unmanaged = du.diff_live_vs_managed(live, managed_ids={'g1'}, label_field='profile.name', tf_resource_type='okta_group')
    assert [u['id'] for u in unmanaged] == ['g2']


def test_diff_live_vs_managed_builds_import_block():
    live = [{'id': 'g2', 'profile': {'name': 'Admins'}}]
    unmanaged = du.diff_live_vs_managed(live, managed_ids=set(), label_field='profile.name', tf_resource_type='okta_group')
    assert unmanaged == [{
        'id': 'g2',
        'label': 'Admins',
        'tf_resource_type': 'okta_group',
        'import_block': 'import {\n  to = okta_group.admins\n  id = "g2"\n}',
    }]


def test_diff_live_vs_managed_returns_empty_when_all_managed():
    live = [{'id': 'g1', 'profile': {'name': 'Engineers'}}]
    assert du.diff_live_vs_managed(live, managed_ids={'g1'}, label_field='profile.name', tf_resource_type='okta_group') == []


def test_diff_live_vs_managed_falls_back_to_id_when_label_missing():
    live = [{'id': 'g3'}]
    unmanaged = du.diff_live_vs_managed(live, managed_ids=set(), label_field='profile.name', tf_resource_type='okta_group')
    assert unmanaged[0]['label'] is None
    assert 'okta_group.g3' in unmanaged[0]['import_block']


def test_diff_live_vs_managed_disambiguates_colliding_names():
    live = [{'id': 'g1', 'profile': {'name': 'Admins'}}, {'id': 'g2', 'profile': {'name': 'Admins!'}}]
    unmanaged = du.diff_live_vs_managed(live, managed_ids=set(), label_field='profile.name', tf_resource_type='okta_group')
    names = [u['import_block'].split('to = okta_group.')[1].split('\n')[0] for u in unmanaged]
    assert len(set(names)) == 2


# ---------------------------------------------------------------------------
# read_managed_resources
# ---------------------------------------------------------------------------

def test_read_managed_resources_filters_by_resource_type():
    state_json = (
        '{"values": {"root_module": {"resources": ['
        '{"type": "okta_group", "name": "eng", "values": {"id": "g1"}},'
        '{"type": "okta_user", "name": "alice", "values": {"id": "u1"}}'
        ']}}}'
    )
    proc = MagicMock(returncode=0, stdout=state_json, stderr='')
    with patch('subprocess.run', return_value=proc) as run:
        ids, names = du.read_managed_resources('/some/dir', 'okta_group')
    assert ids == {'g1'}
    assert names == {'eng'}
    run.assert_called_once_with(
        ['terraform', '-chdir=/some/dir', 'show', '-no-color', '-json'],
        capture_output=True, text=True, check=False, timeout=du.TERRAFORM_SHOW_TIMEOUT,
    )


def test_read_managed_resources_raises_on_terraform_failure():
    proc = MagicMock(returncode=1, stdout='', stderr='no configuration files')
    with patch('subprocess.run', return_value=proc), pytest.raises(RuntimeError, match='no configuration files'):
        du.read_managed_resources('/some/dir', 'okta_group')


def test_read_managed_resources_handles_empty_state():
    proc = MagicMock(returncode=0, stdout='', stderr='')
    with patch('subprocess.run', return_value=proc):
        assert du.read_managed_resources('/some/dir', 'okta_group') == (set(), set())


def test_read_managed_resources_excludes_data_resources():
    state_json = (
        '{"values": {"root_module": {"resources": ['
        '{"type": "okta_group", "mode": "managed", "name": "eng", "values": {"id": "g1"}},'
        '{"type": "okta_group", "mode": "data", "name": "other", "values": {"id": "g2"}}'
        ']}}}'
    )
    proc = MagicMock(returncode=0, stdout=state_json, stderr='')
    with patch('subprocess.run', return_value=proc):
        assert du.read_managed_resources('/some/dir', 'okta_group') == ({'g1'}, {'eng'})


# ---------------------------------------------------------------------------
# run_read_script
# ---------------------------------------------------------------------------

def test_run_read_script_uses_uv_when_available():
    proc = MagicMock(returncode=0, stdout='[{"id": "g1"}]', stderr='')
    with patch('subprocess.run', return_value=proc) as run:
        result = du.run_read_script('okta-groups/scripts/groups.py', ['list'])
    assert result == [{'id': 'g1'}]
    assert run.call_args[0][0][0:2] == ['uv', 'run']


def test_run_read_script_falls_back_to_python_when_uv_missing():
    proc = MagicMock(returncode=0, stdout='[]', stderr='')
    with patch('subprocess.run', side_effect=[FileNotFoundError(), proc]) as run:
        result = du.run_read_script('okta-groups/scripts/groups.py', ['list'])
    assert result == []
    assert run.call_count == 2


def test_run_read_script_raises_on_script_failure():
    proc = MagicMock(returncode=1, stdout='', stderr='{"error": "boom"}')
    with patch('subprocess.run', side_effect=[FileNotFoundError(), proc]), pytest.raises(RuntimeError, match='boom'):
        du.run_read_script('okta-groups/scripts/groups.py', ['list'])


# ---------------------------------------------------------------------------
# resolve_resource_id
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('id_or_url, expected', [
    ('00u1a2b3c4d5e6f7g8h9', '00u1a2b3c4d5e6f7g8h9'),
    ('https://example.okta.com/admin/user/profile/view/00u1a2b3c4d5e6f7g8h9', '00u1a2b3c4d5e6f7g8h9'),
    ('https://example.okta.com/api/v1/groups/00g1a2b3c4d5e6f7g8h9', '00g1a2b3c4d5e6f7g8h9'),
    ('https://example.okta.com/api/v1/groups/00g1a2b3c4d5e6f7g8h9?expand=stats', '00g1a2b3c4d5e6f7g8h9'),
])
def test_resolve_resource_id(id_or_url, expected):
    assert du.resolve_resource_id(id_or_url) == expected


def test_resolve_resource_id_raises_on_empty_path():
    with pytest.raises(ValueError, match='could not extract'):
        du.resolve_resource_id('https://example.okta.com/')


# ---------------------------------------------------------------------------
# find_single
# ---------------------------------------------------------------------------

def test_find_single_returns_unmanaged_object():
    with patch.object(du, 'run_read_script', return_value={'id': 'g2', 'profile': {'name': 'Admins'}}) as run_read, \
         patch.object(du, 'read_managed_resources', return_value=(set(), set())):
        result = du.find_single('group', 'g2', '/some/dir')
    run_read.assert_called_once_with('okta-groups/scripts/groups.py', ['get', 'g2'])
    assert result['id'] == 'g2'
    assert result['tf_resource_type'] == 'okta_group'
    assert 'import_block' in result


def test_find_single_reports_already_managed():
    with patch.object(du, 'run_read_script', return_value={'id': 'g1', 'profile': {'name': 'Engineers'}}), \
         patch.object(du, 'read_managed_resources', return_value=({'g1'}, {'engineers'})):
        result = du.find_single('group', 'g1', '/some/dir')
    assert result == {'id': 'g1', 'tf_resource_type': 'okta_group', 'already_managed': True}


def test_find_single_resolves_url_before_fetching():
    with patch.object(du, 'run_read_script', return_value={'id': 'g2'}) as run_read, \
         patch.object(du, 'read_managed_resources', return_value=(set(), set())):
        du.find_single('group', 'https://example.okta.com/admin/group/g2', '/some/dir')
    run_read.assert_called_once_with('okta-groups/scripts/groups.py', ['get', 'g2'])


def test_find_single_uses_multi_word_get_command():
    with patch.object(du, 'run_read_script', return_value={'id': 'r1'}) as run_read, \
         patch.object(du, 'read_managed_resources', return_value=(set(), set())):
        du.find_single('resource_set', 'r1', '/some/dir')
    run_read.assert_called_once_with('okta-iam/scripts/iam.py', ['get-resource-set', 'r1'])


def test_find_single_avoids_name_collision_with_managed_name():
    with patch.object(du, 'run_read_script', return_value={'id': 'g2', 'profile': {'name': 'Admins'}}), \
         patch.object(du, 'read_managed_resources', return_value=(set(), {'admins'})):
        result = du.find_single('group', 'g2', '/some/dir')
    assert 'to = okta_group.admins\n' not in result['import_block']
    assert 'g2' in result['import_block']


# ---------------------------------------------------------------------------
# RESOURCE_TYPES registry sanity
# ---------------------------------------------------------------------------

def test_every_registered_list_script_exists():
    skills_dir = Path(__file__).parents[1] / 'skills'
    for spec in du.RESOURCE_TYPES.values():
        assert (skills_dir / spec['list_script']).is_file(), spec['list_script']


# ---------------------------------------------------------------------------
# describe_registry
# ---------------------------------------------------------------------------

def test_describe_registry_has_three_groups():
    registry = du.describe_registry()
    assert set(registry) == {'auto_discoverable', 'manual_only', 'not_terraform_manageable'}


def test_describe_registry_auto_discoverable_matches_resource_types():
    registry = du.describe_registry()
    assert set(registry['auto_discoverable']) == set(du.RESOURCE_TYPES)
    group_entry = registry['auto_discoverable']['group']
    assert group_entry == {
        'tf_resource_type': 'okta_group',
        'description': 'Groups',
        'high_cardinality': True,
    }


def test_describe_registry_flags_high_cardinality_types_only():
    registry = du.describe_registry()
    flagged = {name for name, spec in registry['auto_discoverable'].items() if spec['high_cardinality']}
    assert flagged == {'user', 'group'}


def test_describe_registry_includes_manual_only_categories():
    registry = du.describe_registry()
    assert 'apps' in registry['manual_only']
    assert 'reason' in registry['manual_only']['apps']
