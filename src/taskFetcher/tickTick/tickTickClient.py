import os
from dotenv import load_dotenv
import requests
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks

BASE_URL = 'https://api.ticktick.com'

def get_projects():
    project_url = f"{BASE_URL}/open/v1/project"
    headers = {
        "Authorization": get_auth_header()
    }
    response = requests.get(project_url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_project_data(project_id):
    project_data_url = f"{BASE_URL}/open/v1/project/{project_id}/data"
    headers = {
        "Authorization": get_auth_header()
    }
    response = requests.get(project_data_url, headers=headers)
    response.raise_for_status()
    return response.json()

def print_project_tasks(tasks_by_column):
    for column_name, task_list in tasks_by_column.items():
        print(f"Column: {column_name}")
        for task in task_list:
            print(f" - {task['title']}, {task['dueDate']}")

def get_auth_header():
    load_dotenv()
    return f"Bearer {os.getenv('ACCESS_TOKEN')}"