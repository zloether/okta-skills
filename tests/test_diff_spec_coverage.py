import importlib.util
import textwrap
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).parents[1] / 'scripts' / 'diff-spec-coverage.py'
_spec = importlib.util.spec_from_file_location('diff_spec_coverage', _SCRIPT_PATH)
dsc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dsc)


def test_normalize_path_replaces_params():
    assert dsc.normalize_path('/api/v1/users/{userId}/groups') == ('api', 'v1', 'users', '*', 'groups')


def test_parse_skill_prefixes_extracts_multiple_backtick_endpoints():
    table = textwrap.dedent('''
        | okta-users | `skills/okta-users/` | `/api/v1/users` | User profiles |
        | okta-iam | `skills/okta-iam/` | `/api/v1/iam`, `/api/v1/roles` | Roles |
        | okta-filters | `skills/okta-filters/` | — | Reference only |
    ''')
    prefixes = dsc.parse_skill_prefixes(table)
    assert prefixes == {
        'okta-users': [('api', 'v1', 'users')],
        'okta-iam': [('api', 'v1', 'iam'), ('api', 'v1', 'roles')],
    }


def test_match_skill_picks_longest_matching_prefix():
    skill_prefixes = {
        'okta-schemas': [('api', 'v1', 'meta', 'schemas')],
        'okta-users': [('api', 'v1', 'users')],
    }
    path = dsc.normalize_path('/api/v1/meta/schemas/user/default')
    assert dsc.match_skill(path, skill_prefixes) == 'okta-schemas'
    assert dsc.match_skill(dsc.normalize_path('/api/v1/unrelated'), skill_prefixes) is None


def test_extract_implemented_paths_from_fstrings(tmp_path):
    script = tmp_path / 'sample.py'
    script.write_text(textwrap.dedent('''
        def cmd_get(session, base_url, args):
            resp = session.get(f'{base_url}/api/v1/users/{quote(args.id, safe="")}')
            return resp

        def cmd_list(session, base_url, args):
            return paginated_get(session, f'{base_url}/api/v1/users')

        def cmd_nested(session, base_url, args):
            return get_resource(session, '{base}/api/v1/users/{id}/roles/{role_id}', path_params={})

        def not_a_url():
            return f'{base_url} is not a path'
    '''))
    templates = dsc.extract_implemented_paths(script)
    assert templates == {
        ('api', 'v1', 'users', '*'),
        ('api', 'v1', 'users'),
        ('api', 'v1', 'users', '*', 'roles', '*'),
    }


_SPEC = textwrap.dedent('''
    openapi: 3.0.3
    paths:
      /api/v1/users:
        get: {operationId: listUsers, tags: [User]}
      /api/v1/users/{id}:
        get: {operationId: getUser, tags: [User]}
      /api/v1/old:
        get: {operationId: oldOp, deprecated: true, tags: [User]}
      /api/v1/other:
        parameters: []
        post: {operationId: postOnly}
      /api/v1/weird: null
      /api/v1/widgets:
        get: {operationId: listWidgets, tags: [Widget]}
''')

_AGENTS = '| okta-users | `skills/okta-users/` | `/api/v1/users` | Users |\n'


def test_prefix_matches_handles_wildcards_and_short_paths():
    assert dsc.prefix_matches(('api', '*'), ('api', 'v1', 'x'))
    assert not dsc.prefix_matches(('api', 'v1', 'x'), ('api', 'v1'))
    assert not dsc.prefix_matches(('api', 'v2'), ('api', 'v1', 'x'))


def test_parse_spec_get_ops_skips_deprecated_non_get_and_malformed(tmp_path):
    spec = tmp_path / 'spec.yaml'
    spec.write_text(_SPEC)
    ops = {(raw, op_id) for _, raw, op_id, _ in dsc.parse_spec_get_ops(spec)}
    assert ops == {('/api/v1/users', 'listUsers'), ('/api/v1/users/{id}', 'getUser'), ('/api/v1/widgets', 'listWidgets')}


def test_fmt_and_implemented_paths_for_skill(tmp_path, monkeypatch):
    scripts = tmp_path / 'okta-users' / 'scripts'
    scripts.mkdir(parents=True)
    (scripts / 'users.py').write_text("def f(s, base_url):\n    return s.get(f'{base_url}/api/v1/users')\n")
    monkeypatch.setattr(dsc, 'SKILLS_DIR', tmp_path)
    paths = dsc.implemented_paths_for_skill('okta-users')
    assert paths == {('api', 'v1', 'users')}
    assert dsc.fmt(('api', 'v1', 'users')) == '/api/v1/users'


def _setup_main(tmp_path, monkeypatch, spec_files=('spec.yaml',)):
    (tmp_path / 'spec.yaml').write_text(_SPEC)
    agents = tmp_path / 'AGENTS.md'
    agents.write_text(_AGENTS)
    scripts = tmp_path / 'skills' / 'okta-users' / 'scripts'
    scripts.mkdir(parents=True)
    (scripts / 'users.py').write_text("def f(s, base_url):\n    return s.get(f'{base_url}/api/v1/users')\n")
    monkeypatch.setattr(dsc, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(dsc, 'SPEC_FILES', list(spec_files))
    monkeypatch.setattr(dsc, 'AGENTS_MD', agents)
    monkeypatch.setattr(dsc, 'SKILLS_DIR', tmp_path / 'skills')


def test_main_reports_gaps_and_unmapped_areas(tmp_path, monkeypatch, capsys):
    _setup_main(tmp_path, monkeypatch)
    dsc.main()
    out = capsys.readouterr().out
    assert 'okta-users:' in out and 'GET /api/v1/users/{id}  (getUser)' in out
    assert 'GET /api/v1/users  (listUsers)' not in out
    assert '[Widget]' in out and 'GET /api/v1/widgets  (listWidgets)' in out
    assert '1 skills with matching endpoints, 1 of them have gaps' in out
    assert '1 unmapped tags, 1 GET operations total' in out


def test_main_reports_none_when_no_gaps(tmp_path, monkeypatch, capsys):
    _setup_main(tmp_path, monkeypatch)
    (tmp_path / 'spec.yaml').write_text(_SPEC.replace('  /api/v1/users/{id}:\n    get: {operationId: getUser, tags: [User]}\n', ''))
    dsc.main()
    assert '  (none)' in capsys.readouterr().out


def test_main_exits_when_required_spec_missing(tmp_path, monkeypatch):
    _setup_main(tmp_path, monkeypatch, spec_files=('missing.yaml',))
    with pytest.raises(SystemExit, match='run scripts/update-specs.py'):
        dsc.main()


def test_main_warns_when_optional_spec_missing(tmp_path, monkeypatch, capsys):
    _setup_main(tmp_path, monkeypatch, spec_files=('spec.yaml', 'optional.yaml'))
    dsc.main()
    captured = capsys.readouterr()
    assert 'warning: optional.yaml not found' in captured.err
    assert 'optional.yaml' not in captured.out
