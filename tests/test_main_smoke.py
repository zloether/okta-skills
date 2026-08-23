"""Smoke tests: invoke each script's real main() end to end.

test_scripts.py exercises cmd_* functions directly, which skips main()'s
argparse-building code and the shared cli.run() dispatch/print/error-handling
path entirely. These tests invoke main() with a real argv for one subcommand
per script so that code is exercised too. Response shape (list vs dict) is
chosen per-script to match whether the target command calls paginated_get
(list) or paginated_get_wrapped/get_resource (dict).
"""
import json
import sys
from unittest.mock import MagicMock, patch

import pytest
from conftest import make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'

# (skill, script_filename, argv-after-prog, mock .json() response, expected printed output)
CASES = [
    ('okta-attack-protection', 'attack_protection.py', ['get-authenticator-settings'], {}, {}),
    ('okta-security', 'security.py', ['get-threat-insight-config'], {}, {}),
    ('okta-org-settings', 'org_settings.py', ['get'], {}, {}),
    ('okta-authenticators', 'authenticators.py', ['list'], [], []),
    ('okta-api-tokens', 'api_tokens.py', ['list'], [], []),
    ('okta-device-assurance', 'device_assurance.py', ['list'], [], []),
    ('okta-device-integrations', 'device_integrations.py', ['list'], [], []),
    ('okta-device-posture', 'device_posture.py', ['list'], [], []),
    ('okta-sessions', 'sessions.py', ['get', 'sess123'], {}, {}),
    ('okta-behaviors', 'behaviors.py', ['list'], [], []),
    ('okta-iam', 'iam.py', ['list'], {'roles': []}, []),
    ('okta-devices', 'devices.py', ['list'], [], []),
    ('okta-logs', 'logs.py', ['list'], [], []),
    ('okta-network-zones', 'network_zones.py', ['list'], [], []),
    ('okta-identity-providers', 'identity_providers.py', ['list'], [], []),
    ('okta-realms', 'realms.py', ['list-realms'], [], []),
    ('okta-schemas', 'schemas.py', ['list'], [], []),
    ('okta-authorization-servers', 'authorization_servers.py', ['list'], [], []),
    ('okta-users', 'users.py', ['get-apps', '00us8whbc8nFfqQ1o697'], [], []),
]


@pytest.mark.parametrize(
    'skill, script_filename, argv, response_data, expected_output',
    CASES,
    ids=[c[1] for c in CASES],
)
def test_main_smoke(skill, script_filename, argv, response_data, expected_output, capsys):
    module = import_script(skill, script_filename)
    session = MagicMock()
    session.get.return_value = make_response(response_data)

    old_argv = sys.argv
    sys.argv = [script_filename, *argv]
    try:
        with patch('cli.get_session', return_value=(session, BASE_URL)):
            module.main()
    finally:
        sys.argv = old_argv

    out = json.loads(capsys.readouterr().out)
    assert out == expected_output
