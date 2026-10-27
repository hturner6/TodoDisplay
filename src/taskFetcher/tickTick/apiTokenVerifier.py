import requests
import os
import base64
from datetime import date, timedelta
from pathlib import Path

DEFAULT_REDIRECT_URI = 'https://localhost:3000'
scope = 'tasks:read'
authorize_base_url = 'https://ticktick.com/oauth/authorize'

token_url = 'https://ticktick.com/oauth/token'
ENV_FILE = Path(__file__).resolve().parents[1] / '.env'


def redirect_uri(env=os.environ):
    """TICKTICK_REDIRECT_URI from .env; it must match the redirect set on the TickTick app."""
    return (env.get('TICKTICK_REDIRECT_URI') or '').strip() or DEFAULT_REDIRECT_URI


def authorize_url(env=os.environ):
    return (
        f"{authorize_base_url}?client_id={env.get('CLIENT_ID')}"
        f"&scope={scope.replace(' ', '%20')}"
        f"&state=test"
        f"&redirect_uri={redirect_uri(env)}"
        f"&response_type=code"
    )


def save_token(token, env_file=ENV_FILE):
    """Sets ACCESS_TOKEN in the .env file, keeping its other lines, and leaves the file readable only by its owner."""
    env_file = Path(env_file)
    lines = env_file.read_text().splitlines() if env_file.exists() else []
    entry = f"ACCESS_TOKEN={token}"
    if any(line.startswith("ACCESS_TOKEN=") for line in lines):
        lines = [entry if line.startswith("ACCESS_TOKEN=") else line for line in lines]
    else:
        lines.append(entry)
    temp = env_file.with_name(env_file.name + ".tmp")
    temp.unlink(missing_ok=True)  # a leftover file would keep its old, possibly looser, mode
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    os.replace(temp, env_file)

def verify_api_key(authorization_code, env_file=ENV_FILE):
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "code": authorization_code,
        "grant_type": "authorization_code",
        "scope": scope,
        "redirect_uri": redirect_uri()
    }
    response = requests.post(token_url, headers=headers, data=data,
                             auth=(client_id, client_secret))
    if response.ok:
        resp_json = response.json()
        token = resp_json.get("access_token")
        if not token:
            print("Error verifying API key: the response had no access token; .env left unchanged")
            return
        save_token(token, env_file)
        expires_in = resp_json.get("expires_in")
        expiry = f"it expires {date.today() + timedelta(seconds=expires_in)}" if expires_in else "its expiry is unknown"
        print(f"Saved ACCESS_TOKEN to {env_file}; {expiry}. Restart the service to use it.")
    else:
        print("Error verifying API key:", response.text)
