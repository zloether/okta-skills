"""Tests for skills/okta-terraform/scripts/scaffold_project.py."""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SCRIPT_PATH = Path(__file__).parents[1] / 'skills' / 'okta-terraform' / 'scripts' / 'scaffold_project.py'
_spec = importlib.util.spec_from_file_location('scaffold_project', _SCRIPT_PATH)
sp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sp)


# ---------------------------------------------------------------------------
# describe_isolation_groups
# ---------------------------------------------------------------------------

def test_describe_isolation_groups_has_rationale_for_every_group():
    for name, spec in sp.describe_isolation_groups().items():
        assert spec['description'], name
        assert spec['rationale'], name
        assert spec['resource_types'], name


# ---------------------------------------------------------------------------
# shard_by_count
# ---------------------------------------------------------------------------

def test_shard_by_count_empty_list():
    assert sp.shard_by_count([], 60) == []


def test_shard_by_count_single_shard_when_under_max():
    shards = sp.shard_by_count(['Zeta', 'Alpha', 'Mu'], 60)
    assert len(shards) == 1
    assert shards[0] == {'shard': 1, 'count': 3, 'first': 'Alpha', 'last': 'Zeta', 'labels': ['Alpha', 'Mu', 'Zeta']}


def test_shard_by_count_splits_evenly_across_shards():
    labels = [f'app-{i:02d}' for i in range(10)]
    shards = sp.shard_by_count(labels, 4)
    assert len(shards) == 3
    assert sum(s['count'] for s in shards) == 10
    # balanced: no shard should be more than one larger than another
    assert max(s['count'] for s in shards) - min(s['count'] for s in shards) <= 1


def test_shard_by_count_rejects_non_positive_max():
    with pytest.raises(ValueError, match='positive'):
        sp.shard_by_count(['a'], 0)


# ---------------------------------------------------------------------------
# recommend_apps
# ---------------------------------------------------------------------------

def test_recommend_apps_without_pattern_returns_unclassified_note():
    apps = [{'id': 'a1', 'label': 'Salesforce'}, {'id': 'a2', 'label': 'Salesforce Dev'}]
    with patch.object(sp, 'run_read_script', return_value=apps):
        result = sp.recommend_apps()
    assert result['total'] == 2
    assert 'note' in result
    assert result['unclassified_shards'][0]['count'] == 2


def test_recommend_apps_with_pattern_splits_prod_and_shards_nonprod():
    apps = [
        {'id': 'a1', 'label': 'Salesforce Prod'},
        {'id': 'a2', 'label': 'Salesforce Dev'},
        {'id': 'a3', 'label': 'Workday Prod'},
    ]
    with patch.object(sp, 'run_read_script', return_value=apps):
        result = sp.recommend_apps(prod_pattern=r'prod$')
    assert result['prod']['count'] == 2
    assert result['prod']['labels'] == ['Salesforce Prod', 'Workday Prod']
    assert result['nonprod_shards'][0]['labels'] == ['Salesforce Dev']


# ---------------------------------------------------------------------------
# recommend_groups
# ---------------------------------------------------------------------------

def test_recommend_groups_shards_by_profile_name():
    groups = [{'id': 'g1', 'profile': {'name': 'Engineers'}}, {'id': 'g2', 'profile': {'name': 'Admins'}}]
    with patch.object(sp, 'run_read_script', return_value=groups):
        result = sp.recommend_groups(max_per_shard=1)
    assert result['total'] == 2
    assert len(result['shards']) == 2


# ---------------------------------------------------------------------------
# run_read_script
# ---------------------------------------------------------------------------

def test_run_read_script_uses_uv_when_available():
    proc = MagicMock(returncode=0, stdout='[]', stderr='')
    with patch('subprocess.run', return_value=proc) as run:
        assert sp.run_read_script('okta-apps/scripts/apps.py', ['list']) == []
    assert run.call_args[0][0][0:2] == ['uv', 'run']


def test_run_read_script_raises_on_script_failure():
    proc = MagicMock(returncode=1, stdout='', stderr='boom')
    with patch('subprocess.run', side_effect=[FileNotFoundError(), proc]), pytest.raises(RuntimeError, match='boom'):
        sp.run_read_script('okta-apps/scripts/apps.py', ['list'])


# ---------------------------------------------------------------------------
# classify_resource_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('resource_type, expected', [
    ('okta_app_oauth', 'apps'),
    ('okta_app_saml', 'apps'),
    ('okta_group', 'groups'),
    ('okta_user', 'users'),
    ('okta_network_zone', 'network_zones'),
    ('okta_policy_signon', 'auth_policies'),
    ('okta_email_customization', 'other'),
])
def test_classify_resource_type(resource_type, expected):
    assert sp.classify_resource_type(resource_type) == expected


# ---------------------------------------------------------------------------
# review_layout
# ---------------------------------------------------------------------------

def _state(dir_name, counts, has_backend_block=True, has_provider_block=True):
    return {
        'dir': dir_name,
        'has_provider_block': has_provider_block,
        'has_backend_block': has_backend_block,
        'referenced_as_child_module': False,
        'okta_resource_counts': counts,
        'matches_resource_type': None,
    }


def test_review_layout_flags_mixed_isolation_groups():
    modules = [_state('/repo/mixed', {'okta_network_zone': 2, 'okta_policy_signon': 1})]
    with patch.object(sp, 'run_locate_root_module', return_value=modules):
        result = sp.review_layout('/repo')
    assert result['states_reviewed'] == 1
    categories = {f['category'] for f in result['findings']}
    assert 'blast-radius' in categories


def test_review_layout_flags_oversized_app_shard():
    modules = [_state('/repo/apps', {'okta_app_oauth': 70})]
    with patch.object(sp, 'run_locate_root_module', return_value=modules):
        result = sp.review_layout('/repo', max_per_shard=60)
    efficiency = [f for f in result['findings'] if f['category'] == 'efficiency']
    assert len(efficiency) == 1
    assert '70' in efficiency[0]['issue']


def test_review_layout_flags_oversized_group_shard():
    modules = [_state('/repo/groups', {'okta_group': 100})]
    with patch.object(sp, 'run_locate_root_module', return_value=modules):
        result = sp.review_layout('/repo', max_per_shard=60)
    assert any(f['category'] == 'efficiency' and 'okta_group' in f['issue'] for f in result['findings'])


def test_review_layout_flags_missing_backend():
    modules = [_state('/repo/zones', {'okta_network_zone': 1}, has_backend_block=False)]
    with patch.object(sp, 'run_locate_root_module', return_value=modules):
        result = sp.review_layout('/repo')
    assert any(f['category'] == 'testing' and 'backend' in f['issue'] for f in result['findings'])


def test_review_layout_flags_single_apps_state_with_no_prod_split():
    modules = [_state('/repo/apps', {'okta_app_oauth': 5})]
    with patch.object(sp, 'run_locate_root_module', return_value=modules):
        result = sp.review_layout('/repo')
    assert any('prod/non-prod' in f['issue'] for f in result['findings'])


def test_review_layout_no_prod_split_finding_when_apps_already_split():
    modules = [
        _state('/repo/apps-prod', {'okta_app_oauth': 5}),
        _state('/repo/apps-nonprod', {'okta_app_oauth': 5}),
    ]
    with patch.object(sp, 'run_locate_root_module', return_value=modules):
        result = sp.review_layout('/repo')
    assert not any('prod/non-prod' in f['issue'] for f in result['findings'])


def test_review_layout_clean_layout_has_no_findings():
    modules = [
        _state('/repo/network_zones', {'okta_network_zone': 6}),
        _state('/repo/auth_policies', {'okta_policy_signon': 2}),
    ]
    with patch.object(sp, 'run_locate_root_module', return_value=modules):
        result = sp.review_layout('/repo')
    assert result['findings'] == []
    assert result['total_resource_counts'] == {'okta_network_zone': 6, 'okta_policy_signon': 2}


def test_review_layout_falls_back_to_all_dirs_when_none_declare_provider_block():
    modules = [_state('/repo/flat', {'okta_network_zone': 1}, has_provider_block=False)]
    with patch.object(sp, 'run_locate_root_module', return_value=modules):
        result = sp.review_layout('/repo')
    assert result['states_reviewed'] == 1


# ---------------------------------------------------------------------------
# init_layout
# ---------------------------------------------------------------------------

def test_init_layout_creates_versions_and_readme(tmp_path):
    result = sp.init_layout(tmp_path, ['network_zones'])
    assert result == {'created': ['network_zones'], 'skipped': []}
    group_dir = tmp_path / 'network_zones'
    assert (group_dir / 'versions.tf').exists()
    assert 'okta/okta' in (group_dir / 'versions.tf').read_text()
    assert 'network_zones' in (group_dir / 'README.md').read_text()


def test_init_layout_rejects_unknown_group(tmp_path):
    with pytest.raises(ValueError, match='unknown isolation group'):
        sp.init_layout(tmp_path, ['not_a_real_group'])


def test_init_layout_skips_existing_directory(tmp_path):
    (tmp_path / 'network_zones').mkdir()
    result = sp.init_layout(tmp_path, ['network_zones'])
    assert result == {'created': [], 'skipped': ['network_zones']}


def test_init_layout_scaffolds_apps_prod_and_nonprod_shards(tmp_path):
    result = sp.init_layout(tmp_path, [], apps_prod=True, apps_nonprod_shards=2)
    assert set(result['created']) == {'apps-prod', 'apps-nonprod-shard-1', 'apps-nonprod-shard-2'}
    assert (tmp_path / 'apps-prod' / 'versions.tf').exists()
    assert (tmp_path / 'apps-nonprod-shard-2' / 'README.md').exists()


def test_init_layout_scaffolds_group_shards(tmp_path):
    result = sp.init_layout(tmp_path, [], group_shards=3)
    assert set(result['created']) == {'groups-shard-1', 'groups-shard-2', 'groups-shard-3'}
