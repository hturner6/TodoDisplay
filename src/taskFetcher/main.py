import argparse 
import os
import json
from dotenv import load_dotenv
from tickTick.apiTokenVerifier import verify_api_key
from tickTick.tickTickClient import get_projects, get_project_data

# TODO: Remove hardcoded values
def create_Url():
    client_id = os.getenv('CLIENT_ID')
    authorize_url = 'https://ticktick.com/oauth/authorize'
    redirect_uri = 'https://localhost:3000'
    scope = 'tasks:read'
    state = 'test'

    authorization_url = (
        f"{authorize_url}?client_id={client_id}"
        f"&scope={scope.replace(' ', '%20')}"
        f"&state={state}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
    )

    print('Open this URL in your browser to authorize the application:');
    print(authorization_url);

# TODO: use redirect url to grab the 'code' query param value

def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument('--user', action='store_true', help='Creates a user auth URL')
    parser.add_argument('--verify', type=str, help='Verifies the specified token')
    parser.add_argument('--list', action='store_true', help='Lists all projects')
    parser.add_argument('--tasks', type=str, help='Lists all the specified project\'s tasks')
    args = parser.parse_args()
    load_dotenv()

    if args.user:
        create_Url()
    if args.verify:
        verify_api_key(args.verify)
    if args.list:
        projects_json = get_projects()
        print(json.dumps(projects_json, indent=2))
    if args.tasks:
        project_data = get_project_data(args.tasks)
        print(json.dumps(project_data, indent=2))


if __name__ == "__main__":
    main()
