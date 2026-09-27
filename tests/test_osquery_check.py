"""Tests for skills/okta-device-posture/scripts/osquery_check.py."""
import importlib.util
from pathlib import Path

import pytest
import yaml

_SCRIPT_PATH = Path(__file__).parents[1] / 'skills' / 'okta-device-posture' / 'scripts' / 'osquery_check.py'
_spec = importlib.util.spec_from_file_location('osquery_check', _SCRIPT_PATH)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)


# ---------------------------------------------------------------------------
# new_check
# ---------------------------------------------------------------------------

def test_new_check_writes_file_and_returns_id(tmp_path):
    out_path = tmp_path / 'check.yml'
    result = oc.new_check('Title', 'Desc', ['macOS'], ['a@b.com'], [], out_path)
    assert result['written'] == str(out_path)
    assert out_path.is_file()
    assert len(result['id']) == 32
    int(result['id'], 16)  # hex


def test_new_check_refuses_to_overwrite_existing_file(tmp_path):
    out_path = tmp_path / 'check.yml'
    out_path.write_text('existing')
    with pytest.raises(FileExistsError):
        oc.new_check('Title', 'Desc', ['macOS'], ['a@b.com'], [], out_path)


def test_new_check_rejects_unknown_platform(tmp_path):
    with pytest.raises(ValueError, match='unknown platform'):
        oc.new_check('Title', 'Desc', ['Solaris'], ['a@b.com'], [], tmp_path / 'check.yml')


def test_new_check_single_platform_renders_as_scalar(tmp_path):
    out_path = tmp_path / 'check.yml'
    oc.new_check('Title', 'Desc', ['macOS'], ['a@b.com'], [], out_path)
    doc = yaml.safe_load(out_path.read_text())
    assert doc['platform'] == 'macOS'


def test_new_check_multiple_platforms_render_as_list(tmp_path):
    out_path = tmp_path / 'check.yml'
    oc.new_check('Title', 'Desc', ['macOS', 'Windows'], ['a@b.com'], [], out_path)
    doc = yaml.safe_load(out_path.read_text())
    assert doc['platform'] == ['macOS', 'Windows']


def test_new_check_uses_custom_query_when_given(tmp_path):
    out_path = tmp_path / 'check.yml'
    oc.new_check('Title', 'Desc', ['macOS'], ['a@b.com'], [], out_path, query='SELECT 1 AS result;')
    doc = yaml.safe_load(out_path.read_text())
    assert doc['query'].strip() == 'SELECT 1 AS result;'


def test_new_check_round_trips_special_characters(tmp_path):
    out_path = tmp_path / 'check.yml'
    oc.new_check('My: Check', 'Line one.\nLine two.', ['macOS'], ['a@b.com'], ['https://example.com'], out_path)
    doc = yaml.safe_load(out_path.read_text())
    assert doc['title'] == 'My: Check'
    assert doc['description'] == 'Line one.\nLine two.\n'
    assert doc['references'] == ['https://example.com']


def test_new_check_empty_references_render_as_empty_list(tmp_path):
    out_path = tmp_path / 'check.yml'
    oc.new_check('Title', 'Desc', ['macOS'], ['a@b.com'], [], out_path)
    doc = yaml.safe_load(out_path.read_text())
    assert doc['references'] == []


# ---------------------------------------------------------------------------
# validate_check
# ---------------------------------------------------------------------------

def test_validate_check_passes_for_new_check_output(tmp_path):
    out_path = tmp_path / 'check.yml'
    oc.new_check(
        'Title', 'Desc', ['macOS'], ['a@b.com'], [], out_path,
        query='SELECT 1 AS result FROM (SELECT path FROM file WHERE path = "x" LIMIT 1);',
    )
    result = oc.validate_check(out_path)
    assert result == {'valid': True, 'errors': [], 'warnings': []}


def test_validate_check_reports_missing_fields(tmp_path):
    check_path = tmp_path / 'check.yml'
    check_path.write_text('title: Only a title\n')
    result = oc.validate_check(check_path)
    assert result['valid'] is False
    assert any('description' in e for e in result['errors'])
    assert any('query' in e for e in result['errors'])


def test_validate_check_reports_unknown_platform(tmp_path):
    check_path = tmp_path / 'check.yml'
    check_path.write_text(
        'title: T\nid: abc\ndescription: D\nauthor:\n  - a@b.com\nplatform: Solaris\nquery: |\n  SELECT 1;\n'
    )
    result = oc.validate_check(check_path)
    assert any('unknown platform' in e for e in result['errors'])


def test_validate_check_rejects_invalid_yaml(tmp_path):
    check_path = tmp_path / 'check.yml'
    check_path.write_text('title: [unclosed\n')
    result = oc.validate_check(check_path)
    assert result['valid'] is False
    assert 'not valid YAML' in result['errors'][0]


def test_validate_check_warns_on_query_without_select(tmp_path):
    check_path = tmp_path / 'check.yml'
    check_path.write_text(
        'title: T\nid: abc\ndescription: D\nauthor:\n  - a@b.com\nplatform: macOS\nquery: |\n  DELETE FROM file;\n'
    )
    result = oc.validate_check(check_path)
    assert any('no SELECT' in w for w in result['warnings'])


def test_validate_check_reports_non_string_platform_instead_of_crashing(tmp_path):
    check_path = tmp_path / 'check.yml'
    # YAML 1.1 parses bareword `yes` as boolean True, not the string "yes".
    check_path.write_text(
        'title: T\nid: abc\ndescription: D\nauthor:\n  - a@b.com\nplatform: yes\nquery: |\n  SELECT 1;\n'
    )
    result = oc.validate_check(check_path)
    assert result['valid'] is False
    assert any('must be strings' in e for e in result['errors'])


def test_validate_check_warns_when_query_pattern_unrecognized(tmp_path):
    check_path = tmp_path / 'check.yml'
    check_path.write_text(
        'title: T\nid: abc\ndescription: D\nauthor:\n  - a@b.com\nplatform: macOS\nquery: |\n  SELECT * FROM processes;\n'
    )
    result = oc.validate_check(check_path)
    assert any('established pattern' in w for w in result['warnings'])
