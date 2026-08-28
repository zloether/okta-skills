"""Shared Okta API client: session setup, auth, and pagination."""
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit


def _bootstrap_venv():
    """Add repo .venv site-packages to sys.path when uv is not managing deps."""
    import glob as _glob
    shared_dir = os.path.dirname(os.path.realpath(__file__))
    repo_dir = os.path.dirname(shared_dir)
    patterns = [
        os.path.join(repo_dir, '.venv', 'lib', 'python*', 'site-packages'),  # POSIX
        os.path.join(repo_dir, '.venv', 'Lib', 'site-packages'),  # Windows
    ]
    for pattern in patterns:
        for sp in _glob.glob(pattern):
            if sp not in sys.path:
                sys.path.insert(0, sp)

_bootstrap_venv()

import requests

try:
    import jwt as _pyjwt
    from cryptography.hazmat.primitives.asymmetric import ec as _ec
    from cryptography.hazmat.primitives.asymmetric import rsa as _rsa
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    _OAUTH_AVAILABLE = True
except ImportError:  # pragma: no cover — exercised only when optional OAuth deps are absent
    _OAUTH_AVAILABLE = False


class _OktaSession(requests.Session):
    """requests.Session subclass that injects a default timeout on every request."""

    def __init__(self, timeout):
        super().__init__()
        self._default_timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', self._default_timeout)
        for attempt in range(4):
            resp = super().request(method, url, **kwargs)
            if resp.status_code != 429 or attempt == 3:
                if resp.status_code == 429:
                    print('[okta-skills] rate limited; giving up after 3 retries', file=sys.stderr)
                return resp
            reset_ts = resp.headers.get('x-rate-limit-reset')
            if reset_ts:
                wait = max(int(reset_ts) - int(time.time()) + 1, 1)
            else:
                wait = max(int(resp.headers.get('Retry-After', 0)), 2 ** (attempt + 2))
            wait = min(wait, 60)  # cap so clock skew or an org-wide throttle can't block indefinitely
            print(f'[okta-skills] rate limited; retrying in {wait}s (attempt {attempt + 1}/3)', file=sys.stderr)
            time.sleep(wait)
        return resp  # pragma: no cover — unreachable, satisfies linters


def _load_private_key(value):
    """Load a private key from a file path, JWK JSON string, or PEM string."""
    if not _OAUTH_AVAILABLE:
        raise RuntimeError(
            'PyJWT and cryptography are required for PrivateKey auth. '
            'Install with: pip install "PyJWT>=2.0" "cryptography>=41.0"'
        )

    value = value.strip()

    # File path: doesn't begin with '{' (JWK) or '-----' (PEM header)
    if not value.startswith('{') and not value.startswith('-----'):
        p = Path(value)
        if not p.exists():
            raise RuntimeError(
                'OKTA_CLIENT_PRIVATEKEY: value is not a valid file path, PEM, or JWK '
                f'(got a {len(value)}-character value starting with "{value[:12]}...")'
            )
        value = p.read_text().strip()

    # JWK JSON
    if value.startswith('{'):
        jwk_data = json.loads(value)
        kty = jwk_data.get('kty', 'RSA')
        if kty == 'EC':
            from jwt.algorithms import ECAlgorithm
            return ECAlgorithm.from_jwk(json.dumps(jwk_data))
        else:
            from jwt.algorithms import RSAAlgorithm
            return RSAAlgorithm.from_jwk(json.dumps(jwk_data))

    # PEM
    pem_bytes = value.encode() if isinstance(value, str) else value
    return load_pem_private_key(pem_bytes, password=None)


def _key_algorithm(private_key):
    """Return the JWT signing algorithm for a given cryptography private key."""
    if not _OAUTH_AVAILABLE:
        raise RuntimeError(
            'PyJWT and cryptography are required for PrivateKey auth. '
            'Install with: pip install "PyJWT>=2.0" "cryptography>=41.0"'
        )
    if isinstance(private_key, _rsa.RSAPrivateKey):
        return 'RS256'
    if isinstance(private_key, _ec.EllipticCurvePrivateKey):
        return 'ES256'
    raise RuntimeError(f'Unsupported key type: {type(private_key).__name__}')


def _fetch_oauth_token(org_url, client_id, private_key, scopes, timeout=30, verify=True):
    """Exchange a private key JWT assertion for an OAuth access token."""
    token_url = f'{org_url}/oauth2/v1/token'
    algorithm = _key_algorithm(private_key)
    now = int(time.time())
    claims = {
        'iss': client_id,
        'sub': client_id,
        'aud': token_url,
        'iat': now,
        'exp': now + 300,  # 5-minute assertion lifetime
        'jti': str(uuid.uuid4()),
    }
    assertion = _pyjwt.encode(claims, private_key, algorithm=algorithm)
    scope_str = scopes if isinstance(scopes, str) else ' '.join(scopes)
    resp = requests.post(
        token_url,
        data={
            'grant_type': 'client_credentials',
            'scope': scope_str,
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion': assertion,
        },
        timeout=timeout,
        verify=verify,
    )
    resp.raise_for_status()
    data = resp.json()
    return data['access_token'], data.get('expires_in', 3600)


def _read_token_cache(cache_path):
    """Return a cached access token if present and not within 60 seconds of expiry."""
    try:
        data = json.loads(Path(cache_path).read_text())
        if data.get('expires_at', 0) > time.time() + 60:
            return data['access_token']
    except Exception:  # noqa: BLE001, S110 — a corrupt/missing cache must fall back to a fresh token fetch
        pass
    return None


def _write_token_cache(cache_path, token, expires_in):
    """Write an access token and its expiry timestamp to the cache file, readable only by the owner."""
    p = Path(cache_path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps({
            'access_token': token,
            'expires_at': time.time() + expires_in,
        }).encode()
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            if hasattr(os, 'fchmod'):
                os.fchmod(fd, 0o600)  # tighten permissions on a pre-existing, more permissive file
            os.write(fd, data)
        finally:
            os.close(fd)
    except Exception:  # noqa: BLE001, S110 — cache write failure must not abort a successfully-authenticated session
        pass


def get_session():
    """Return (session, base_url) configured from environment variables.

    Auth method precedence:
      1. OKTA_CLIENT_AUTHORIZATIONMODE if set ('PrivateKey' or 'SSWS')
      2. PrivateKey if OKTA_CLIENT_CLIENTID + OKTA_CLIENT_PRIVATEKEY are both present
      3. SSWS if OKTA_CLIENT_TOKEN is set
    """
    org_url = os.environ.get('OKTA_CLIENT_ORGURL', '').rstrip('/')
    if not org_url:
        raise RuntimeError('OKTA_CLIENT_ORGURL environment variable is not set')
    if not org_url.startswith('https://'):
        raise RuntimeError(
            f'OKTA_CLIENT_ORGURL must start with "https://" (got "{org_url}"). '
            'A non-HTTPS URL would send credentials in cleartext.'
        )

    connect_timeout = int(os.environ.get('OKTA_CLIENT_CONNECTIONTIMEOUT', '30'))
    request_timeout = int(os.environ.get('OKTA_CLIENT_REQUESTTIMEOUT', '30'))
    user_agent = os.environ.get('OKTA_CLIENT_USERAGENT', '').strip() or None
    ca_bundle = (
        os.environ.get('OKTA_CLIENT_CABUNDLE', '').strip()
        or os.environ.get('REQUESTS_CA_BUNDLE', '').strip()
        or True
    )

    auth_mode = os.environ.get('OKTA_CLIENT_AUTHORIZATIONMODE', '').strip().lower()
    ssws_token = os.environ.get('OKTA_CLIENT_TOKEN', '').strip()
    client_id = os.environ.get('OKTA_CLIENT_CLIENTID', '').strip()
    private_key_value = os.environ.get('OKTA_CLIENT_PRIVATEKEY', '').strip()
    scopes = os.environ.get('OKTA_CLIENT_SCOPES', '').strip()
    cache_path = os.environ.get('OKTA_CLIENT_TOKEN_CACHE_PATH', '').strip() or None

    # Determine auth method
    if auth_mode == 'privatekey':
        use_private_key = True
    elif auth_mode == 'ssws':
        use_private_key = False
    elif auth_mode:
        raise RuntimeError(
            f'OKTA_CLIENT_AUTHORIZATIONMODE: unrecognized value "{auth_mode}". '
            'Expected "PrivateKey" or "SSWS".'
        )
    else:
        use_private_key = bool(client_id and private_key_value)

    if use_private_key:
        if not client_id:
            raise RuntimeError('OKTA_CLIENT_CLIENTID is required for PrivateKey auth')
        if not private_key_value:
            raise RuntimeError('OKTA_CLIENT_PRIVATEKEY is required for PrivateKey auth')
        if not scopes:
            raise RuntimeError('OKTA_CLIENT_SCOPES is required for PrivateKey auth')

        access_token = cache_path and _read_token_cache(cache_path)
        if not access_token:
            private_key = _load_private_key(private_key_value)
            access_token, expires_in = _fetch_oauth_token(
                org_url, client_id, private_key, scopes,
                timeout=(connect_timeout, request_timeout),
                verify=ca_bundle,
            )
            if cache_path:
                _write_token_cache(cache_path, access_token, expires_in)

        auth_header = f'Bearer {access_token}'
    else:
        if not ssws_token:
            raise RuntimeError('OKTA_CLIENT_TOKEN is required for SSWS auth')
        auth_header = f'SSWS {ssws_token}'

    session = _OktaSession(timeout=(connect_timeout, request_timeout))
    session.verify = ca_bundle
    headers = {
        'Authorization': auth_header,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    if user_agent:
        headers['User-Agent'] = user_agent
    session.headers.update(headers)
    return session, org_url


def get_resource(session, url, params=None, allow_empty=False, allow_404=False):
    """Fetch a single (non-paginated) resource; raises on HTTP error.

    If allow_empty is True, a 204 No Content response returns [] instead of
    raising on the empty body (used by endpoints where "no resource" is a
    valid, documented response, e.g. an IdP with no active signing key).

    If allow_404 is True, a 404 Not Found response returns None instead of
    raising (used by endpoints where the resource simply may not exist yet,
    e.g. no Aerial consent granted).
    """
    resp = session.get(url, params=params)
    if allow_404 and resp.status_code == 404:
        return None
    resp.raise_for_status()
    if allow_empty and resp.status_code == 204:
        return []
    return resp.json()


_DEFAULT_PORTS = {'http': 80, 'https': 443}


def _origin(url):
    """Return a (scheme, host, port) tuple with case and default-port normalization."""
    parts = urlsplit(url)
    scheme = (parts.scheme or '').lower()
    host = (parts.hostname or '').lower()
    port = parts.port or _DEFAULT_PORTS.get(scheme)
    return scheme, host, port


def _same_origin(url_a, url_b):
    """True if both URLs share the same scheme and host, ignoring case and
    default-port vs. explicit-port differences (e.g. "example.com" vs. "example.com:443")."""
    return _origin(url_a) == _origin(url_b)


def _check_pagination_origin(next_url, origin_url):
    """Guard against a pagination cursor pointing off-origin, since the same
    authenticated session (and Authorization header) is used to follow it."""
    if next_url and not _same_origin(next_url, origin_url):
        raise RuntimeError(f'pagination link pointed to an unexpected origin: {next_url}')


def paginated_get(session, url, params=None, limit=None):
    """Fetch all pages from a paginated Okta endpoint, up to an optional limit."""
    origin_url = url
    results = []
    while url:
        resp = session.get(url, params=params)
        resp.raise_for_status()
        page = resp.json()
        results.extend(page)
        if not page:  # empty page = caught up to live tail; stop
            break
        if limit and len(results) >= limit:
            return results[:limit]
        params = None  # subsequent URLs are absolute; params only apply to the first request
        url = _next_link(resp.headers.get('Link', ''))
        _check_pagination_origin(url, origin_url)
    return results


def _next_link(link_header):
    """Extract the next-page URL from an Okta Link header, or return None."""
    for match in re.finditer(r'<([^>]*)>\s*;\s*rel="([^"]*)"', link_header):
        if match.group(2) == 'next':
            return match.group(1)
    return None


def paginated_get_wrapped(session, url, key, params=None, limit=None):
    """Fetch all pages from an Okta IAM-style endpoint.

    Unlike the core API's bare-array + `Link` header pagination, the IAM/governance
    endpoints (`/api/v1/iam/...`) wrap results in a named field and paginate via a
    `_links.next.href` cursor embedded in the JSON body.
    """
    origin_url = url
    results = []
    while url:
        resp = session.get(url, params=params)
        resp.raise_for_status()
        page = resp.json()
        items = page.get(key, [])
        results.extend(items)
        if not items:  # empty page = caught up to live tail; stop
            break
        if limit and len(results) >= limit:
            return results[:limit]
        params = None  # subsequent URLs are absolute; params only apply to the first request
        url = ((page.get('_links') or {}).get('next') or {}).get('href')
        _check_pagination_origin(url, origin_url)
    return results
