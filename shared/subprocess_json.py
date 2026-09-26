"""Shared helper for skill scripts that delegate to another script via subprocess."""
import json
import subprocess
import sys


def run_script_json(script_path, args):
    """Run script_path with `uv run`, falling back to the current interpreter, and parse its JSON stdout."""
    for interpreter in (['uv', 'run'], [sys.executable]):
        try:
            proc = subprocess.run(
                [*interpreter, str(script_path), *args],
                capture_output=True, text=True, check=False,
            )
        except FileNotFoundError:
            continue
        if proc.returncode == 0:
            return json.loads(proc.stdout)
        if interpreter == ['uv', 'run']:
            continue  # uv not installed or failed to launch; try plain python
        raise RuntimeError(f'{script_path} {" ".join(args)} failed: {proc.stderr.strip()}')
    raise RuntimeError(f'neither "uv" nor the current Python interpreter could run {script_path}')
