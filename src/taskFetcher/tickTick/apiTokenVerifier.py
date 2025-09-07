import webbrowser
import requests
import os
import base64

redirect_uri = 'https://localhost:3000'
scope = 'tasks:read' 

token_url = 'https://ticktick.com/oauth/token'

def refresh_token():
    auth_url: str = create_Url()
    webbrowser.open(auth_url, new=0, autoraise=True)
    # TODO: use redirect url to grab the 'code' query param value
    auth_code: str = input('Enter the code: ') 
    access_token: str = verify_api_key(auth_code)
    # TODO: update .env access token

# TODO: Remove hardcoded values
def create_Url() -> str:
    client_id: str = os.getenv('CLIENT_ID')
    authorize_url: str = 'https://ticktick.com/oauth/authorize'
    redirect_uri: str = 'https://localhost:3000'
    scope: str = 'tasks:read'
    state: str = 'test'

    authorization_url: str = (
        f"{authorize_url}?client_id={client_id}"
        f"&scope={scope.replace(' ', '%20')}"
        f"&state={state}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
    )
    return authorization_url


def verify_api_key(authorization_code) -> str:
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
        access_token: str = resp_json.get("access_token")
        print("Access Token:", access_token)
        print("Token Type:", resp_json.get("token_type"))
        print("Expires In:", resp_json.get("expires_in"))
        return access_token 
    else:
        print("Error verifying API key:", response.text)
