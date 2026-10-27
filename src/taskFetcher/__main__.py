import argparse
import json
import os
from datetime import date
from dotenv import load_dotenv
from taskFetcher.tickTick.apiTokenVerifier import authorize_url, verify_api_key
from taskFetcher.tickTick.tickTickClient import get_projects, get_project_data
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks
from models.task import TaskEncoder
from taskDisplay.screenLayout import select
from taskFetcher.todoApp.todoAppSource import TodoAppSource

def create_Url():
    print('Open this URL in your browser to authorize the application:')
    print(authorize_url())

# TODO: use redirect url to grab the 'code' query param value

def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument('--user', action='store_true', help='Creates a user auth URL')
    parser.add_argument('--verify', type=str, help='Verifies the specified token')
    parser.add_argument('--list', action='store_true', help='Lists all projects')
    parser.add_argument('--tasks', type=str, help='Lists all the specified project\'s tasks')
    parser.add_argument('--todoapp', action='store_true', help='Lists today\'s Daily Items and this week\'s Weekly Items from TodoApp')
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
        parsed_tasks = parse_project_tasks(project_data)
        print(parsed_tasks)
    if args.todoapp:
        # What the display would show: the fetcher returns everything, the screen's rule chooses.
        for task in sum(select(TodoAppSource(os.environ).fetch(), date.today()), []):
            print(f"{'week' if task.weekly else 'day '} {task.due_date} {task.scheduled_time or '     '} [{task.status}]{' !' if task.priority else ''} {task.title}")

if __name__ == "__main__":
    main()
