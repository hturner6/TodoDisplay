import base64
import json
import subprocess
import tempfile
import time
import requests

TOKEN_URL = 'https://oauth2.googleapis.com/token'
SCOPE = 'https://www.googleapis.com/auth/datastore'
LIFETIME = 3600
# Refresh a little early so a token never expires mid-request.
EXPIRY_MARGIN = 60

_cache = {}


def _b64(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b'=')


def _sign(private_key_pem: str, message: bytes) -> bytes:
    # openssl ships with Raspberry Pi OS, so this avoids a crypto package on the Pi Zero.
    with tempfile.NamedTemporaryFile('w') as pem:  # created with mode 600
        pem.write(private_key_pem)
        pem.flush()
        result = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', pem.name],
                                input=message, capture_output=True, check=True)
    return result.stdout


def build_assertion(key: dict, now: float) -> str:
    """The signed JWT that is exchanged for an access token."""
    header = _b64(json.dumps({'alg': 'RS256', 'typ': 'JWT'}).encode())
    claims = _b64(json.dumps({
        'iss': key['client_email'], 'scope': SCOPE, 'aud': TOKEN_URL,
        'iat': int(now), 'exp': int(now) + LIFETIME,
    }).encode())
    signing_input = header + b'.' + claims
    return (signing_input + b'.' + _b64(_sign(key['private_key'], signing_input))).decode()


def get_access_token(key_path: str, post=requests.post, now=time.time) -> str:
    """A bearer token for the service account in key_path, cached until shortly before expiry."""
    cached = _cache.get(key_path)
    if cached and cached[1] > now() + EXPIRY_MARGIN:
        return cached[0]

    with open(key_path) as key_file:
        key = json.load(key_file)
    response = post(TOKEN_URL, timeout=30, data={
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': build_assertion(key, now()),
    })
    response.raise_for_status()
    body = response.json()
    _cache[key_path] = (body['access_token'], now() + body.get('expires_in', LIFETIME))
    return body['access_token']
