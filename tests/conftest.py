import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'shared'))


@pytest.fixture
def rsa_key_pair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return key, pem.decode()


@pytest.fixture
def ec_key_pair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return key, pem.decode()


def make_response(data, next_url=None):
    """Return a mock requests.Response with JSON data and optional Link header."""
    resp = MagicMock()
    resp.json.return_value = data
    resp.headers = {'Link': f'<{next_url}>; rel="next"'} if next_url else {}
    return resp


def args(**kwargs):
    """Create a lightweight namespace object to stand in for argparse args."""
    return type('Args', (), kwargs)()
