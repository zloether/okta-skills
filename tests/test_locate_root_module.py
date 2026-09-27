"""Tests for skills/okta-terraform/scripts/locate_root_module.py."""
import importlib.util
from pathlib import Path

_SCRIPT_PATH = Path(__file__).parents[1] / 'skills' / 'okta-terraform' / 'scripts' / 'locate_root_module.py'
_spec = importlib.util.spec_from_file_location('locate_root_module', _SCRIPT_PATH)
lrm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lrm)


# ---------------------------------------------------------------------------
# find_tf_dirs / _scan_own_tf_files / count_okta_resources
# ---------------------------------------------------------------------------

def test_find_tf_dirs_finds_nested_directories(tmp_path):
    (tmp_path / 'envs' / 'prod').mkdir(parents=True)
    (tmp_path / 'envs' / 'prod' / 'main.tf').write_text('')
    (tmp_path / 'modules' / 'group').mkdir(parents=True)
    (tmp_path / 'modules' / 'group' / 'main.tf').write_text('')
    dirs = lrm.find_tf_dirs(tmp_path)
    assert dirs == sorted([tmp_path / 'envs' / 'prod', tmp_path / 'modules' / 'group'])


def test_scan_own_tf_files_detects_provider_and_backend(tmp_path):
    (tmp_path / 'main.tf').write_text('provider "okta" {\n  org_name = var.org\n}\n')
    (tmp_path / 'versions.tf').write_text('terraform {\n  backend "s3" {\n    bucket = "x"\n  }\n}\n')
    has_provider, has_backend, counts = lrm._scan_own_tf_files(tmp_path)
    assert has_provider is True
    assert has_backend is True
    assert counts == {}


def test_scan_own_tf_files_false_when_absent(tmp_path):
    (tmp_path / 'main.tf').write_text('resource "okta_group" "eng" {}\n')
    has_provider, has_backend, counts = lrm._scan_own_tf_files(tmp_path)
    assert has_provider is False
    assert has_backend is False
    assert counts == {'okta_group': 1}


def test_count_okta_resources(tmp_path):
    (tmp_path / 'main.tf').write_text(
        'resource "okta_group" "eng" {}\n'
        'resource "okta_group" "admins" {}\n'
        'resource "okta_user" "alice" {}\n'
    )
    assert lrm.count_okta_resources(tmp_path) == {'okta_group': 2, 'okta_user': 1}


def test_aggregate_okta_resource_counts_includes_local_module_children(tmp_path):
    root = tmp_path / 'root'
    child = tmp_path / 'modules' / 'apps'
    root.mkdir(parents=True)
    child.mkdir(parents=True)
    (root / 'main.tf').write_text(
        'provider "okta" {}\n'
        'module "apps" {\n  source = "../modules/apps"\n}\n'
        'resource "okta_group" "eng" {}\n'
    )
    (child / 'main.tf').write_text('resource "okta_app_oauth" "a" {}\nresource "okta_app_oauth" "b" {}\n')
    assert lrm.aggregate_okta_resource_counts(root) == {'okta_group': 1, 'okta_app_oauth': 2}


def test_aggregate_okta_resource_counts_ignores_registry_module_sources(tmp_path):
    (tmp_path / 'main.tf').write_text(
        'module "vpc" {\n  source = "terraform-aws-modules/vpc/aws"\n}\n'
        'resource "okta_group" "eng" {}\n'
    )
    assert lrm.aggregate_okta_resource_counts(tmp_path) == {'okta_group': 1}


# ---------------------------------------------------------------------------
# find_module_callers
# ---------------------------------------------------------------------------

def test_find_module_callers_resolves_local_source(tmp_path):
    (tmp_path / 'modules' / 'group').mkdir(parents=True)
    (tmp_path / 'envs' / 'prod').mkdir(parents=True)
    (tmp_path / 'envs' / 'prod' / 'main.tf').write_text(
        'module "group" {\n  source = "../../modules/group"\n}\n'
    )
    callers = lrm.find_module_callers(tmp_path)
    assert (tmp_path / 'modules' / 'group').resolve() in callers


def test_find_module_callers_ignores_registry_sources(tmp_path):
    (tmp_path / 'main.tf').write_text(
        'module "vpc" {\n  source = "terraform-aws-modules/vpc/aws"\n}\n'
    )
    assert lrm.find_module_callers(tmp_path) == set()


# ---------------------------------------------------------------------------
# parse_required_version_constraint / parse_lock_file
# ---------------------------------------------------------------------------

def test_parse_required_version_constraint_found(tmp_path):
    (tmp_path / 'versions.tf').write_text(
        'terraform {\n'
        '  required_providers {\n'
        '    okta = {\n'
        '      source  = "okta/okta"\n'
        '      version = "~> 4.0"\n'
        '    }\n'
        '  }\n'
        '}\n'
    )
    assert lrm.parse_required_version_constraint(tmp_path) == '~> 4.0'


def test_parse_required_version_constraint_ignores_other_providers(tmp_path):
    (tmp_path / 'versions.tf').write_text(
        'terraform {\n'
        '  required_providers {\n'
        '    aws = {\n'
        '      source  = "hashicorp/aws"\n'
        '      version = "~> 5.0"\n'
        '    }\n'
        '  }\n'
        '}\n'
    )
    assert lrm.parse_required_version_constraint(tmp_path) is None


def test_parse_lock_file_found(tmp_path):
    (tmp_path / '.terraform.lock.hcl').write_text(
        'provider "registry.terraform.io/okta/okta" {\n'
        '  version     = "4.13.0"\n'
        '  constraints = "~> 4.0"\n'
        '}\n'
    )
    assert lrm.parse_lock_file(tmp_path) == '4.13.0'


def test_parse_lock_file_missing(tmp_path):
    assert lrm.parse_lock_file(tmp_path) is None


# ---------------------------------------------------------------------------
# list_root_modules
# ---------------------------------------------------------------------------

def test_list_root_modules_ranks_provider_dir_above_child_module(tmp_path):
    root = tmp_path / 'root'
    child = tmp_path / 'modules' / 'group'
    root.mkdir(parents=True)
    child.mkdir(parents=True)
    (root / 'main.tf').write_text(
        'provider "okta" {}\n'
        'module "group" {\n  source = "../modules/group"\n}\n'
    )
    (child / 'main.tf').write_text('resource "okta_group" "eng" {}\n')

    ranked = lrm.list_root_modules(tmp_path)
    assert ranked[0]['dir'] == str(root)
    assert ranked[0]['has_provider_block'] is True
    assert ranked[0]['has_backend_block'] is False
    assert ranked[1]['referenced_as_child_module'] is True


def test_list_root_modules_aggregates_composed_module_counts(tmp_path):
    root = tmp_path / 'root'
    child = tmp_path / 'modules' / 'apps'
    root.mkdir(parents=True)
    child.mkdir(parents=True)
    (root / 'main.tf').write_text(
        'provider "okta" {}\n'
        'module "apps" {\n  source = "../modules/apps"\n}\n'
    )
    (child / 'main.tf').write_text('resource "okta_app_oauth" "a" {}\n')

    ranked = lrm.list_root_modules(tmp_path)
    root_entry = next(c for c in ranked if c['dir'] == str(root))
    assert root_entry['okta_resource_counts'] == {'okta_app_oauth': 1}


def test_list_root_modules_prefers_dir_matching_resource_type(tmp_path):
    envs_a = tmp_path / 'a'
    envs_b = tmp_path / 'b'
    envs_a.mkdir()
    envs_b.mkdir()
    (envs_a / 'main.tf').write_text('provider "okta" {}\nresource "okta_user" "u" {}\n')
    (envs_b / 'main.tf').write_text('provider "okta" {}\nresource "okta_group" "g" {}\n')

    ranked = lrm.list_root_modules(tmp_path, resource_type='okta_group')
    assert ranked[0]['dir'] == str(envs_b)


# ---------------------------------------------------------------------------
# resolve_version
# ---------------------------------------------------------------------------

def test_resolve_version_prefers_lock_file(tmp_path):
    (tmp_path / '.terraform.lock.hcl').write_text(
        'provider "registry.terraform.io/okta/okta" {\n  version = "4.13.0"\n}\n'
    )
    (tmp_path / 'versions.tf').write_text(
        'terraform {\n  required_providers {\n    okta = {\n      source = "okta/okta"\n      version = "~> 4.0"\n    }\n  }\n}\n'
    )
    result = lrm.resolve_version(tmp_path)
    assert result == {'source': 'lock', 'version': '4.13.0'}


def test_resolve_version_falls_back_to_constraint(tmp_path):
    (tmp_path / 'versions.tf').write_text(
        'terraform {\n  required_providers {\n    okta = {\n      source = "okta/okta"\n      version = "~> 4.0"\n    }\n  }\n}\n'
    )
    result = lrm.resolve_version(tmp_path)
    assert result['source'] == 'constraint'
    assert result['constraint'] == '~> 4.0'
    assert 'terraform init' in result['note']


def test_resolve_version_falls_back_to_none(tmp_path):
    result = lrm.resolve_version(tmp_path)
    assert result['source'] == 'none'
    assert 'releases/latest' in result['note']
