"""Shared helper for skill scripts that delegate to another script via subprocess."""
import json
import subprocess
import sys

DEFAULT_TIMEOUT = 120


def run_script_json(script_path, args, timeout=DEFAULT_TIMEOUT):
    """Run script_path with `uv run`, falling back to the current interpreter, and parse its JSON stdout.

    Every script in this repo reports its own failures as `{"error": ...}` JSON on stderr with exit
    code 1 (see AGENTS.md), which lets this tell a genuine script failure — raised immediately, never
    retried — apart from `uv` itself failing to launch the script at all (e.g. a broken uv cache),
    which is the only case worth falling back to the plain interpreter for.
    """
    last_error = None
    for interpreter in (['uv', 'run'], [sys.executable]):
        try:
            proc = subprocess.run(
                [*interpreter, str(script_path), *args],
                capture_output=True, text=True, check=False, timeout=timeout,
            )
        except FileNotFoundError:
            continue
        if proc.returncode == 0:
            return json.loads(proc.stdout)
        try:
            error_payload = json.loads(proc.stderr)
        except (json.JSONDecodeError, ValueError):
            error_payload = None
        if error_payload is not None:
            raise RuntimeError(f'{script_path} {" ".join(args)} failed: {error_payload.get("error", proc.stderr.strip())}')
        last_error = proc.stderr.strip()
        if interpreter == ['uv', 'run']:
            continue  # uv itself failed to launch the script (not a script-reported error); try plain python
        raise RuntimeError(f'{script_path} {" ".join(args)} failed: {last_error}')
    raise RuntimeError(f'neither "uv" nor the current Python interpreter could run {script_path}')
