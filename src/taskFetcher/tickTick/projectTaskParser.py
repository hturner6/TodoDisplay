from datetime import datetime, timezone
from models.task import Task

def parse_project_tasks(project_json):
    tasks = project_json.get('tasks', [])
    columns = project_json.get('columns', [])
    project_name = project_json.get('project', {}).get('name', 'Unknown')
    print(f"{len(tasks)} tasks in project {project_name}:")
    columns_map = {column['id']: column['name'] for column in columns}
    parsedTasks = []

    for task in tasks:
        parsed_task = parse_task(task, columns_map)
        parsedTasks.append(parsed_task)
    return parsedTasks

def parse_task(task_json, columns_map):
    return Task(
        title=task_json.get('title'),
        due_date=parse_due_date(task_json.get('dueDate')),
        category=columns_map.get(task_json.get('columnId'), 'No Category'),
    )

def parse_due_date(due_date):
    if not due_date:
        return None
    # Ticktick sets the due date to start of day and converts local timezone to UTC
    # we need to convert back to localtimezone for the correct date
    return datetime.fromisoformat(due_date).astimezone().date()