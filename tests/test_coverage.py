"""Guardrail: every cmd_* function in a skill script must have a test in test_scripts.py.

This doesn't check correctness (that's what test_scripts.py itself does) — it
just fails loudly if a new command ships with zero test coverage, instead of
relying on someone noticing during a manual audit.
"""
import ast
from pathlib import Path

_SKILLS_DIR = Path(__file__).parents[1] / 'skills'
_TEST_SCRIPTS_SOURCE = (Path(__file__).parent / 'test_scripts.py').read_text()


def _cmd_functions(script_path):
    tree = ast.parse(script_path.read_text())
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith('cmd_')
    ]


def _skill_scripts():
    for skill_dir in sorted(_SKILLS_DIR.iterdir()):
        scripts_dir = skill_dir / 'scripts'
        if not scripts_dir.is_dir():
            continue
        for script_path in sorted(scripts_dir.glob('*.py')):
            fixture = skill_dir.name.removeprefix('okta-').replace('-', '_')
            yield fixture, script_path


def test_every_cmd_function_has_a_test():
    missing = []
    for fixture, script_path in _skill_scripts():
        for cmd_name in _cmd_functions(script_path):
            if f'{fixture}.{cmd_name}(' not in _TEST_SCRIPTS_SOURCE:
                missing.append(f'{script_path.relative_to(_SKILLS_DIR)}: {cmd_name}')
    assert not missing, 'Untested cmd_* functions (add a test in test_scripts.py):\n' + '\n'.join(missing)
