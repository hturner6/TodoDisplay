import requests
import os
import base64

redirect_uri = 'https://localhost:3000'
scope = 'tasks:read' 

token_url = 'https://ticktick.com/oauth/token'

def verify_api_key(authorization_code):
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
        print("Access Token:", resp_json.get("access_token"))
        print("Token Type:", resp_json.get("token_type"))
        print("Expires In:", resp_json.get("expires_in"))
    else:
        print("Error verifying API key:", response.text)
