import importlib.util
import textwrap
from pathlib import Path

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

        def not_a_url():
            return f'{base_url} is not a path'
    '''))
    templates = dsc.extract_implemented_paths(script)
    assert templates == {
        ('api', 'v1', 'users', '*'),
        ('api', 'v1', 'users'),
    }
