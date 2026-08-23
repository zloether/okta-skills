"""Tests for shared/okta_client.py."""
import json
import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from conftest import make_response
from okta_client import (
    _next_link,
    _OktaSession,
    _read_token_cache,
    _write_token_cache,
    get_resource,
    get_session,
    paginated_get,
    paginated_get_wrapped,
)

# ---------------------------------------------------------------------------
# get_resource
# ---------------------------------------------------------------------------

def test_get_resource_returns_json():
    session = MagicMock()
    session.get.return_value = make_response({'id': '1'})
    result = get_resource(session, 'https://example.okta.com/api/v1/users/1')
    assert result == {'id': '1'}
    session.get.assert_called_once_with('https://example.okta.com/api/v1/users/1', params=None)


def test_get_resource_passes_params():
    session = MagicMock()
    session.get.return_value = make_response({'id': '1'})
    get_resource(session, 'https://example.okta.com/api/v1/users/1', params={'expand': 'blocks'})
    session.get.assert_called_once_with(
        'https://example.okta.com/api/v1/users/1', params={'expand': 'blocks'}
    )


def test_get_resource_raises_on_http_error():
    session = MagicMock()
    resp = make_response({'errorSummary': 'Not found'})
    resp.raise_for_status.side_effect = Exception('404 Client Error')
    session.get.return_value = resp
    with pytest.raises(Exception, match='404 Client Error'):
        get_resource(session, 'https://example.okta.com/api/v1/users/nope')


# ---------------------------------------------------------------------------
# _next_link
# ---------------------------------------------------------------------------

def test_next_link_returns_next_url():
    header = (
        '<https://example.okta.com/api/v1/users?after=abc>; rel="next", '
        '<https://example.okta.com/api/v1/users>; rel="self"'
    )
    assert _next_link(header) == 'https://example.okta.com/api/v1/users?after=abc'


def test_next_link_no_next_rel_returns_none():
    assert _next_link('<https://example.okta.com/api/v1/users>; rel="self"') is None


def test_next_link_empty_returns_none():
    assert _next_link('') is None


def test_next_link_url_with_comma_still_parses():
    header = '<https://example.okta.com/api/v1/logs?after=x%2Cy>; rel="next"'
    assert _next_link(header) == 'https://example.okta.com/api/v1/logs?after=x%2Cy'


# ---------------------------------------------------------------------------
# paginated_get
# ---------------------------------------------------------------------------

def test_paginated_get_single_page():
    session = MagicMock()
    session.get.return_value = make_response([{'id': '1'}, {'id': '2'}])
    result = paginated_get(session, 'https://example.okta.com/api/v1/users')
    assert result == [{'id': '1'}, {'id': '2'}]
    session.get.assert_called_once()


def test_paginated_get_follows_next_link():
    session = MagicMock()
    session.get.side_effect = [
        make_response([{'id': '1'}], next_url='https://example.okta.com/api/v1/users?after=1'),
        make_response([{'id': '2'}]),
    ]
    result = paginated_get(session, 'https://example.okta.com/api/v1/users')
    assert result == [{'id': '1'}, {'id': '2'}]
    assert session.get.call_count == 2


def test_paginated_get_respects_limit():
    session = MagicMock()
    session.get.return_value = make_response([{'id': str(i)} for i in range(10)])
    result = paginated_get(session, 'https://example.okta.com/api/v1/users', limit=3)
    assert len(result) == 3


def test_paginated_get_stops_on_empty_page():
    # Okta returns an empty page with a next cursor at the live tail — must not follow it
    session = MagicMock()
    session.get.side_effect = [
        make_response([{'id': '1'}], next_url='https://example.okta.com/api/v1/logs?after=x'),
        make_response([], next_url='https://example.okta.com/api/v1/logs?after=x'),
    ]
    result = paginated_get(session, 'https://example.okta.com/api/v1/logs')
    assert result == [{'id': '1'}]
    assert session.get.call_count == 2  # fetched empty page, then stopped


def test_paginated_get_clears_params_on_subsequent_pages():
    session = MagicMock()
    session.get.side_effect = [
        make_response([{'id': '1'}], next_url='https://example.okta.com/api/v1/users?after=1'),
        make_response([{'id': '2'}]),
    ]
    paginated_get(session, 'https://example.okta.com/api/v1/users',
                  params={'filter': 'status eq "ACTIVE"'})
    first_params = session.get.call_args_list[0][1]['params']
    second_params = session.get.call_args_list[1][1]['params']
    assert first_params == {'filter': 'status eq "ACTIVE"'}
    assert second_params is None


# ---------------------------------------------------------------------------
# paginated_get_wrapped
# ---------------------------------------------------------------------------

def test_paginated_get_wrapped_single_page():
    session = MagicMock()
    session.get.return_value = make_response({'roles': [{'id': '1'}, {'id': '2'}]})
    result = paginated_get_wrapped(session, 'https://example.okta.com/api/v1/iam/roles', 'roles')
    assert result == [{'id': '1'}, {'id': '2'}]
    session.get.assert_called_once()


def test_paginated_get_wrapped_follows_next_href():
    session = MagicMock()
    session.get.side_effect = [
        make_response({
            'roles': [{'id': '1'}],
            '_links': {'next': {'href': 'https://example.okta.com/api/v1/iam/roles?after=1'}},
        }),
        make_response({'roles': [{'id': '2'}]}),
    ]
    result = paginated_get_wrapped(session, 'https://example.okta.com/api/v1/iam/roles', 'roles')
    assert result == [{'id': '1'}, {'id': '2'}]
    assert session.get.call_count == 2


def test_paginated_get_wrapped_respects_limit():
    session = MagicMock()
    session.get.return_value = make_response({'roles': [{'id': str(i)} for i in range(10)]})
    result = paginated_get_wrapped(
        session, 'https://example.okta.com/api/v1/iam/roles', 'roles', limit=3
    )
    assert len(result) == 3


def test_paginated_get_wrapped_stops_on_empty_page():
    session = MagicMock()
    session.get.side_effect = [
        make_response({
            'roles': [{'id': '1'}],
            '_links': {'next': {'href': 'https://example.okta.com/api/v1/iam/roles?after=x'}},
        }),
        make_response({
            'roles': [],
            '_links': {'next': {'href': 'https://example.okta.com/api/v1/iam/roles?after=x'}},
        }),
    ]
    result = paginated_get_wrapped(session, 'https://example.okta.com/api/v1/iam/roles', 'roles')
    assert result == [{'id': '1'}]
    assert session.get.call_count == 2


def test_paginated_get_wrapped_clears_params_on_subsequent_pages():
    session = MagicMock()
    session.get.side_effect = [
        make_response({
            'roles': [{'id': '1'}],
            '_links': {'next': {'href': 'https://example.okta.com/api/v1/iam/roles?after=1'}},
        }),
        make_response({'roles': [{'id': '2'}]}),
    ]
    paginated_get_wrapped(
        session, 'https://example.okta.com/api/v1/iam/roles', 'roles', params={'limit': 20}
    )
    first_params = session.get.call_args_list[0][1]['params']
    second_params = session.get.call_args_list[1][1]['params']
    assert first_params == {'limit': 20}
    assert second_params is None


def test_paginated_get_wrapped_missing_key_returns_empty():
    session = MagicMock()
    session.get.return_value = make_response({})
    result = paginated_get_wrapped(session, 'https://example.okta.com/api/v1/iam/roles', 'roles')
    assert result == []


# ---------------------------------------------------------------------------
# Token cache
# ---------------------------------------------------------------------------

def test_write_and_read_token_cache(tmp_path):
    cache_file = str(tmp_path / 'cache.json')
    _write_token_cache(cache_file, 'my_token', expires_in=3600)
    assert _read_token_cache(cache_file) == 'my_token'


def test_read_expired_cache_returns_none(tmp_path):
    cache_file = tmp_path / 'cache.json'
    cache_file.write_text(json.dumps({
        'access_token': 'old_token',
        'expires_at': time.time() - 100,
    }))
    assert _read_token_cache(str(cache_file)) is None


def test_read_missing_cache_returns_none(tmp_path):
    assert _read_token_cache(str(tmp_path / 'nonexistent.json')) is None


@pytest.mark.skipif(sys.platform == 'win32', reason='POSIX permission bits do not apply on Windows')
def test_write_token_cache_is_owner_only_readable(tmp_path):
    cache_file = str(tmp_path / 'cache.json')
    _write_token_cache(cache_file, 'my_token', expires_in=3600)
    mode = os.stat(cache_file).st_mode & 0o777
    assert mode == 0o600


@pytest.mark.skipif(sys.platform == 'win32', reason='POSIX permission bits do not apply on Windows')
def test_write_token_cache_tightens_permissions_on_existing_file(tmp_path):
    cache_file = tmp_path / 'cache.json'
    cache_file.write_text('{}')
    os.chmod(cache_file, 0o644)
    _write_token_cache(str(cache_file), 'my_token', expires_in=3600)
    mode = os.stat(cache_file).st_mode & 0o777
    assert mode == 0o600


# ---------------------------------------------------------------------------
# _load_private_key
# ---------------------------------------------------------------------------

def test_load_private_key_from_pem_string(rsa_key_pair):
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
    from okta_client import _load_private_key
    _, pem_str = rsa_key_pair
    assert isinstance(_load_private_key(pem_str), RSAPrivateKey)


def test_load_private_key_from_pem_file(rsa_key_pair, tmp_path):
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
    from okta_client import _load_private_key
    _, pem_str = rsa_key_pair
    key_file = tmp_path / 'key.pem'
    key_file.write_text(pem_str)
    assert isinstance(_load_private_key(str(key_file)), RSAPrivateKey)


def test_load_private_key_from_jwk_rsa(rsa_key_pair):
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
    from jwt.algorithms import RSAAlgorithm
    from okta_client import _load_private_key
    key, _ = rsa_key_pair
    jwk_str = RSAAlgorithm.to_jwk(key)
    assert isinstance(_load_private_key(jwk_str), RSAPrivateKey)


def test_load_private_key_from_jwk_ec(ec_key_pair):
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
    from jwt.algorithms import ECAlgorithm
    from okta_client import _load_private_key
    key, _ = ec_key_pair
    jwk_str = ECAlgorithm.to_jwk(key)
    assert isinstance(_load_private_key(jwk_str), EllipticCurvePrivateKey)


def test_load_private_key_file_not_found():
    from okta_client import _load_private_key
    with pytest.raises(RuntimeError, match='file not found'):
        _load_private_key('/nonexistent/path/to/key.pem')


def test_load_private_key_raises_when_oauth_deps_unavailable(monkeypatch):
    import okta_client
    from okta_client import _load_private_key
    monkeypatch.setattr(okta_client, '_OAUTH_AVAILABLE', False)
    with pytest.raises(RuntimeError, match='PyJWT and cryptography are required'):
        _load_private_key('-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----')


# ---------------------------------------------------------------------------
# _key_algorithm
# ---------------------------------------------------------------------------

def test_key_algorithm_rsa(rsa_key_pair):
    from okta_client import _key_algorithm
    key, _ = rsa_key_pair
    assert _key_algorithm(key) == 'RS256'


def test_key_algorithm_ec(ec_key_pair):
    from okta_client import _key_algorithm
    key, _ = ec_key_pair
    assert _key_algorithm(key) == 'ES256'


def test_key_algorithm_unsupported_type_raises():
    from okta_client import _key_algorithm
    with pytest.raises(RuntimeError, match='Unsupported key type'):
        _key_algorithm(object())


# ---------------------------------------------------------------------------
# _fetch_oauth_token
# ---------------------------------------------------------------------------

def test_fetch_oauth_token_posts_to_correct_endpoint(rsa_key_pair):
    from okta_client import _fetch_oauth_token
    key, _ = rsa_key_pair
    mock_resp = MagicMock()
    mock_resp.json.return_value = {'access_token': 'tok', 'expires_in': 3600}

    with patch('requests.post', return_value=mock_resp) as mock_post:
        token, expires_in = _fetch_oauth_token(
            'https://example.okta.com', 'client_id', key, 'okta.users.read'
        )

    assert token == 'tok'
    assert expires_in == 3600
    url = mock_post.call_args[0][0]
    assert url == 'https://example.okta.com/oauth2/v1/token'


def test_fetch_oauth_token_payload(rsa_key_pair):
    from okta_client import _fetch_oauth_token
    key, _ = rsa_key_pair
    mock_resp = MagicMock()
    mock_resp.json.return_value = {'access_token': 'tok', 'expires_in': 3600}

    with patch('requests.post', return_value=mock_resp) as mock_post:
        _fetch_oauth_token('https://example.okta.com', 'client_id', key, 'okta.users.read')

    data = mock_post.call_args[1]['data']
    assert data['grant_type'] == 'client_credentials'
    assert data['scope'] == 'okta.users.read'
    assert data['client_assertion_type'] == (
        'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'
    )
    assert 'client_assertion' in data


# ---------------------------------------------------------------------------
# get_session — auth mode selection
# ---------------------------------------------------------------------------

def _clear_oauth_env(monkeypatch):
    for var in ('OKTA_CLIENT_CLIENTID', 'OKTA_CLIENT_PRIVATEKEY',
                'OKTA_CLIENT_SCOPES', 'OKTA_CLIENT_AUTHORIZATIONMODE',
                'OKTA_CLIENT_TOKEN_CACHE_PATH'):
        monkeypatch.delenv(var, raising=False)


def test_get_session_ssws(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    _clear_oauth_env(monkeypatch)
    session, base_url = get_session()
    assert base_url == 'https://example.okta.com'
    assert session.headers['Authorization'] == 'SSWS ssws_tok'


def test_get_session_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com/')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    _clear_oauth_env(monkeypatch)
    _, base_url = get_session()
    assert base_url == 'https://example.okta.com'


def test_get_session_auto_prefers_private_key_when_both_present(monkeypatch, rsa_key_pair):
    _, pem_str = rsa_key_pair
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    monkeypatch.setenv('OKTA_CLIENT_CLIENTID', 'client_id')
    monkeypatch.setenv('OKTA_CLIENT_PRIVATEKEY', pem_str)
    monkeypatch.setenv('OKTA_CLIENT_SCOPES', 'okta.users.read')
    monkeypatch.delenv('OKTA_CLIENT_AUTHORIZATIONMODE', raising=False)
    monkeypatch.delenv('OKTA_CLIENT_TOKEN_CACHE_PATH', raising=False)

    with patch('okta_client._fetch_oauth_token', return_value=('bearer_tok', 3600)):
        session, _ = get_session()

    assert session.headers['Authorization'] == 'Bearer bearer_tok'


def test_get_session_explicit_ssws_mode_ignores_oauth_vars(monkeypatch, rsa_key_pair):
    _, pem_str = rsa_key_pair
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_AUTHORIZATIONMODE', 'SSWS')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    monkeypatch.setenv('OKTA_CLIENT_CLIENTID', 'client_id')
    monkeypatch.setenv('OKTA_CLIENT_PRIVATEKEY', pem_str)
    monkeypatch.setenv('OKTA_CLIENT_SCOPES', 'okta.users.read')
    session, _ = get_session()
    assert session.headers['Authorization'] == 'SSWS ssws_tok'


def test_get_session_uses_token_cache_skips_fetch(monkeypatch, rsa_key_pair, tmp_path):
    _, pem_str = rsa_key_pair
    cache_file = str(tmp_path / 'cache.json')
    _write_token_cache(cache_file, 'cached_tok', expires_in=3600)

    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_CLIENTID', 'client_id')
    monkeypatch.setenv('OKTA_CLIENT_PRIVATEKEY', pem_str)
    monkeypatch.setenv('OKTA_CLIENT_SCOPES', 'okta.users.read')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN_CACHE_PATH', cache_file)
    monkeypatch.delenv('OKTA_CLIENT_TOKEN', raising=False)
    monkeypatch.delenv('OKTA_CLIENT_AUTHORIZATIONMODE', raising=False)

    with patch('okta_client._fetch_oauth_token') as mock_fetch:
        session, _ = get_session()
        mock_fetch.assert_not_called()

    assert session.headers['Authorization'] == 'Bearer cached_tok'


def test_get_session_fetches_new_token_when_cache_expired(monkeypatch, rsa_key_pair, tmp_path):
    _, pem_str = rsa_key_pair
    cache_file = tmp_path / 'cache.json'
    cache_file.write_text(json.dumps({
        'access_token': 'expired_tok',
        'expires_at': time.time() - 100,
    }))

    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_CLIENTID', 'client_id')
    monkeypatch.setenv('OKTA_CLIENT_PRIVATEKEY', pem_str)
    monkeypatch.setenv('OKTA_CLIENT_SCOPES', 'okta.users.read')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN_CACHE_PATH', str(cache_file))
    monkeypatch.delenv('OKTA_CLIENT_TOKEN', raising=False)
    monkeypatch.delenv('OKTA_CLIENT_AUTHORIZATIONMODE', raising=False)

    with patch('okta_client._fetch_oauth_token', return_value=('fresh_tok', 3600)):
        session, _ = get_session()

    assert session.headers['Authorization'] == 'Bearer fresh_tok'


def test_get_session_sets_ca_bundle(monkeypatch, tmp_path):
    ca_file = tmp_path / 'ca.pem'
    ca_file.write_text('fake-cert')
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    monkeypatch.setenv('OKTA_CLIENT_CABUNDLE', str(ca_file))
    _clear_oauth_env(monkeypatch)
    session, _ = get_session()
    assert session.verify == str(ca_file)


def test_get_session_verify_defaults_to_true(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    monkeypatch.delenv('OKTA_CLIENT_CABUNDLE', raising=False)
    monkeypatch.delenv('REQUESTS_CA_BUNDLE', raising=False)
    _clear_oauth_env(monkeypatch)
    session, _ = get_session()
    assert session.verify is True


def test_get_session_falls_back_to_requests_ca_bundle(monkeypatch, tmp_path):
    ca_file = tmp_path / 'ca.pem'
    ca_file.write_text('fake-cert')
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    monkeypatch.delenv('OKTA_CLIENT_CABUNDLE', raising=False)
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', str(ca_file))
    _clear_oauth_env(monkeypatch)
    session, _ = get_session()
    assert session.verify == str(ca_file)


def test_get_session_okta_cabundle_takes_precedence(monkeypatch, tmp_path):
    okta_ca = tmp_path / 'okta-ca.pem'
    requests_ca = tmp_path / 'requests-ca.pem'
    okta_ca.write_text('okta-cert')
    requests_ca.write_text('requests-cert')
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    monkeypatch.setenv('OKTA_CLIENT_CABUNDLE', str(okta_ca))
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', str(requests_ca))
    _clear_oauth_env(monkeypatch)
    session, _ = get_session()
    assert session.verify == str(okta_ca)


def test_get_session_sets_user_agent(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    monkeypatch.setenv('OKTA_CLIENT_USERAGENT', 'my-tool/1.0')
    _clear_oauth_env(monkeypatch)
    session, _ = get_session()
    assert session.headers['User-Agent'] == 'my-tool/1.0'


def test_get_session_missing_orgurl_raises(monkeypatch):
    monkeypatch.delenv('OKTA_CLIENT_ORGURL', raising=False)
    with pytest.raises(RuntimeError, match='OKTA_CLIENT_ORGURL'):
        get_session()


def test_get_session_non_https_orgurl_raises(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'http://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_TOKEN', 'ssws_tok')
    _clear_oauth_env(monkeypatch)
    with pytest.raises(RuntimeError, match='https://'):
        get_session()


def test_get_session_missing_token_ssws_raises(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_AUTHORIZATIONMODE', 'SSWS')
    monkeypatch.delenv('OKTA_CLIENT_TOKEN', raising=False)
    with pytest.raises(RuntimeError, match='OKTA_CLIENT_TOKEN'):
        get_session()


def test_get_session_missing_scopes_oauth_raises(monkeypatch, rsa_key_pair):
    _, pem_str = rsa_key_pair
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_AUTHORIZATIONMODE', 'PrivateKey')
    monkeypatch.setenv('OKTA_CLIENT_CLIENTID', 'client_id')
    monkeypatch.setenv('OKTA_CLIENT_PRIVATEKEY', pem_str)
    monkeypatch.delenv('OKTA_CLIENT_SCOPES', raising=False)
    with pytest.raises(RuntimeError, match='OKTA_CLIENT_SCOPES'):
        get_session()


def test_get_session_explicit_privatekey_mode_missing_clientid_raises(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_AUTHORIZATIONMODE', 'PrivateKey')
    monkeypatch.delenv('OKTA_CLIENT_CLIENTID', raising=False)
    with pytest.raises(RuntimeError, match='OKTA_CLIENT_CLIENTID'):
        get_session()


def test_get_session_explicit_privatekey_mode_missing_privatekey_raises(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_AUTHORIZATIONMODE', 'PrivateKey')
    monkeypatch.setenv('OKTA_CLIENT_CLIENTID', 'client_id')
    monkeypatch.delenv('OKTA_CLIENT_PRIVATEKEY', raising=False)
    with pytest.raises(RuntimeError, match='OKTA_CLIENT_PRIVATEKEY'):
        get_session()


def test_get_session_unrecognized_auth_mode_raises(monkeypatch):
    monkeypatch.setenv('OKTA_CLIENT_ORGURL', 'https://example.okta.com')
    monkeypatch.setenv('OKTA_CLIENT_AUTHORIZATIONMODE', 'oauth2')
    with pytest.raises(RuntimeError, match='OKTA_CLIENT_AUTHORIZATIONMODE'):
        get_session()


def test_fetch_oauth_token_uses_configured_timeout(rsa_key_pair):
    from okta_client import _fetch_oauth_token
    key, _ = rsa_key_pair
    mock_resp = MagicMock()
    mock_resp.json.return_value = {'access_token': 'tok', 'expires_in': 3600}

    with patch('requests.post', return_value=mock_resp) as mock_post:
        _fetch_oauth_token('https://example.okta.com', 'client_id', key, 'okta.users.read',
                           timeout=(5, 10))

    assert mock_post.call_args[1]['timeout'] == (5, 10)


def test_write_token_cache_creates_parent_dirs(tmp_path):
    cache_file = str(tmp_path / 'nested' / 'dir' / 'cache.json')
    _write_token_cache(cache_file, 'tok', 3600)
    assert _read_token_cache(cache_file) == 'tok'


def test_write_token_cache_silently_ignores_write_error(tmp_path):
    cache_file = str(tmp_path / 'cache.json')
    # Should not raise even if the underlying write fails
    with patch('os.open', side_effect=PermissionError('denied')):
        _write_token_cache(cache_file, 'tok', 3600)
    assert _read_token_cache(cache_file) is None


# ---------------------------------------------------------------------------
# _OktaSession timeout injection
# ---------------------------------------------------------------------------

def test_okta_session_injects_default_timeout():
    session = _OktaSession(timeout=(5, 10))
    with patch('requests.Session.request') as mock_request:
        mock_request.return_value = MagicMock()
        session.request('GET', 'https://example.okta.com')
    assert mock_request.call_args[1]['timeout'] == (5, 10)


def test_okta_session_does_not_override_explicit_timeout():
    session = _OktaSession(timeout=(5, 10))
    with patch('requests.Session.request') as mock_request:
        mock_request.return_value = MagicMock()
        session.request('GET', 'https://example.okta.com', timeout=99)
    assert mock_request.call_args[1]['timeout'] == 99


# ---------------------------------------------------------------------------
# _OktaSession 429 retry
# ---------------------------------------------------------------------------

def _make_429(retry_after=None, rate_limit_reset=None):
    resp = MagicMock()
    resp.status_code = 429
    headers = {}
    if retry_after is not None:
        headers['Retry-After'] = str(retry_after)
    if rate_limit_reset is not None:
        headers['x-rate-limit-reset'] = str(rate_limit_reset)
    resp.headers = headers
    return resp


def _make_200():
    resp = MagicMock()
    resp.status_code = 200
    return resp


def test_okta_session_retries_on_429_and_succeeds():
    session = _OktaSession(timeout=(5, 10))
    with patch('requests.Session.request', side_effect=[_make_429(retry_after=1), _make_200()]) as mock_req, \
         patch('time.sleep') as mock_sleep:
        resp = session.request('GET', 'https://example.okta.com')
    assert resp.status_code == 200
    assert mock_req.call_count == 2
    mock_sleep.assert_called_once_with(4)  # max(1, 2**(0+2)) = 4


def test_okta_session_uses_retry_after_header_when_larger_than_minimum():
    session = _OktaSession(timeout=(5, 10))
    with patch('requests.Session.request', side_effect=[_make_429(retry_after=42), _make_200()]), \
         patch('time.sleep') as mock_sleep:
        session.request('GET', 'https://example.okta.com')
    mock_sleep.assert_called_once_with(42)  # max(42, 4) = 42


def test_okta_session_falls_back_to_minimum_backoff_without_retry_after():
    session = _OktaSession(timeout=(5, 10))
    with patch('requests.Session.request', side_effect=[_make_429(), _make_200()]), \
         patch('time.sleep') as mock_sleep:
        session.request('GET', 'https://example.okta.com')
    mock_sleep.assert_called_once_with(4)  # max(0, 2**(0+2)) = 4 on first attempt


def test_okta_session_stops_after_max_retries():
    session = _OktaSession(timeout=(5, 10))
    responses = [_make_429(retry_after=1)] * 4
    with patch('requests.Session.request', side_effect=responses) as mock_req, \
         patch('time.sleep'):
        resp = session.request('GET', 'https://example.okta.com')
    assert resp.status_code == 429
    assert mock_req.call_count == 4  # 1 initial + 3 retries


def test_okta_session_prints_giving_up_message_after_max_retries(capsys):
    session = _OktaSession(timeout=(5, 10))
    with patch('requests.Session.request', side_effect=[_make_429(retry_after=1)] * 4), \
         patch('time.sleep'):
        session.request('GET', 'https://example.okta.com')
    err = capsys.readouterr().err
    assert 'giving up' in err


def test_okta_session_prints_warning_to_stderr_on_retry(capsys):
    session = _OktaSession(timeout=(5, 10))
    with patch('requests.Session.request', side_effect=[_make_429(retry_after=1), _make_200()]), \
         patch('time.sleep'):
        session.request('GET', 'https://example.okta.com')
    err = capsys.readouterr().err
    assert 'rate limited' in err
    assert 'attempt 1/3' in err


def test_okta_session_uses_x_rate_limit_reset_header():
    session = _OktaSession(timeout=(5, 10))
    fake_now = 1_000_000
    with patch('requests.Session.request', side_effect=[_make_429(rate_limit_reset=fake_now + 30), _make_200()]), \
         patch('time.sleep') as mock_sleep, \
         patch('okta_client.time.time', return_value=fake_now):
        session.request('GET', 'https://example.okta.com')
    mock_sleep.assert_called_once_with(31)  # (now+30) - now + 1 buffer


def test_okta_session_x_rate_limit_reset_takes_precedence_over_retry_after():
    session = _OktaSession(timeout=(5, 10))
    fake_now = 1_000_000
    with patch('requests.Session.request', side_effect=[
            _make_429(retry_after=5, rate_limit_reset=fake_now + 20), _make_200()]), \
         patch('time.sleep') as mock_sleep, \
         patch('okta_client.time.time', return_value=fake_now):
        session.request('GET', 'https://example.okta.com')
    mock_sleep.assert_called_once_with(21)  # uses reset header (21), not Retry-After (5)


def test_okta_session_caps_wait_at_60_seconds():
    session = _OktaSession(timeout=(5, 10))
    fake_now = 1_000_000
    with patch('requests.Session.request', side_effect=[
            _make_429(rate_limit_reset=fake_now + 600), _make_200()]), \
         patch('time.sleep') as mock_sleep, \
         patch('okta_client.time.time', return_value=fake_now):
        session.request('GET', 'https://example.okta.com')
    mock_sleep.assert_called_once_with(60)  # 601s reset would block; capped to 60


# ---------------------------------------------------------------------------
# _bootstrap_venv
# ---------------------------------------------------------------------------

def test_bootstrap_venv_adds_site_packages_to_sys_path(tmp_path):
    from okta_client import _bootstrap_venv

    # Structure: tmp_path/shared/okta_client.py (fake), tmp_path/.venv/lib/python3.x/site-packages
    sp = tmp_path / '.venv' / 'lib' / 'python3.11' / 'site-packages'
    sp.mkdir(parents=True)

    original_path = sys.path.copy()
    # Patch only the realpath call inside _bootstrap_venv to point __file__ into tmp_path/shared/
    fake_file = str(tmp_path / 'shared' / 'okta_client.py')
    with patch('okta_client.os.path.realpath', side_effect=lambda p: fake_file if p.endswith('okta_client.py') else os.path.realpath(p)):
        _bootstrap_venv()

    try:
        assert any(
            os.path.realpath(p) == os.path.realpath(str(sp))
            for p in sys.path
        )
    finally:
        sys.path[:] = original_path


def test_bootstrap_venv_no_venv_does_not_raise(tmp_path):
    from okta_client import _bootstrap_venv

    original_path = sys.path.copy()
    fake_file = str(tmp_path / 'shared' / 'okta_client.py')
    with patch('okta_client.os.path.realpath', side_effect=lambda p: fake_file if p.endswith('okta_client.py') else os.path.realpath(p)):
        _bootstrap_venv()  # no .venv present — must not raise

    sys.path[:] = original_path


def test_bootstrap_venv_adds_windows_site_packages_to_sys_path(tmp_path):
    from okta_client import _bootstrap_venv

    # Structure: tmp_path/shared/okta_client.py (fake), tmp_path/.venv/Lib/site-packages
    sp = tmp_path / '.venv' / 'Lib' / 'site-packages'
    sp.mkdir(parents=True)

    original_path = sys.path.copy()
    fake_file = str(tmp_path / 'shared' / 'okta_client.py')
    with patch('okta_client.os.path.realpath', side_effect=lambda p: fake_file if p.endswith('okta_client.py') else os.path.realpath(p)):
        _bootstrap_venv()

    try:
        assert any(
            os.path.realpath(p) == os.path.realpath(str(sp))
            for p in sys.path
        )
    finally:
        sys.path[:] = original_path


def test_bootstrap_venv_does_not_add_duplicate(tmp_path):
    from okta_client import _bootstrap_venv

    sp = tmp_path / '.venv' / 'lib' / 'python3.11' / 'site-packages'
    sp.mkdir(parents=True)

    original_path = sys.path.copy()
    sys.path.insert(0, str(sp))  # pre-load the exact path that glob will return

    fake_file = str(tmp_path / 'shared' / 'okta_client.py')
    with patch('okta_client.os.path.realpath', side_effect=lambda p: fake_file if p.endswith('okta_client.py') else os.path.realpath(p)):
        _bootstrap_venv()

    try:
        assert sys.path.count(str(sp)) == 1
    finally:
        sys.path[:] = original_path
