import requests
import os
import base64
from datetime import date, timedelta
from pathlib import Path

redirect_uri = 'https://localhost:3000'
scope = 'tasks:read' 

token_url = 'https://ticktick.com/oauth/token'
ENV_FILE = Path(__file__).resolve().parents[1] / '.env'


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
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
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
        "redirect_uri": redirect_uri
    }
    response = requests.post(token_url, headers=headers, data=data,
                             auth=(client_id, client_secret))
    if response.ok:
        resp_json = response.json()
        save_token(resp_json.get("access_token"), env_file)
        expires = date.today() + timedelta(seconds=resp_json.get("expires_in", 0))
        print(f"Saved ACCESS_TOKEN to {env_file}; it expires {expires}. Restart the service to use it.")
    else:
        print("Error verifying API key:", response.text)
