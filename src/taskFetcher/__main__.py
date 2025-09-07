import argparse
import os
import json
from dotenv import load_dotenv
from taskFetcher.tickTick.apiTokenVerifier import verify_api_key, create_Url, refresh_token_main
from taskFetcher.tickTick.tickTickClient import get_projects, get_project_data
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks
from models.task import TaskEncoder


def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument('--user', action='store_true', help='Creates a user auth URL')
    parser.add_argument('--verify', type=str, help='Verifies the specified token')
    parser.add_argument('--refresh', action='store_true', help='Refreshes the api token')
    parser.add_argument('--list', action='store_true', help='Lists all projects')
    parser.add_argument('--tasks', type=str, help='Lists all the specified project\'s tasks')
    args = parser.parse_args()
    load_dotenv()

    
    if args.refresh:
        refresh_token()
    elif args.user:
        authorization_url = create_Url()
        print('Open this URL in your browser to authorize the application:');
        print(authorization_url);
    elif args.verify:
        verify_api_key(args.verify)
    elif args.list:
        projects_json = get_projects()
        print(json.dumps(projects_json, indent=2))
    elif args.tasks:
        project_data = get_project_data(args.tasks)
        parsed_tasks = parse_project_tasks(project_data)
        print(parsed_tasks)

if __name__ == "__main__":
    main()
