from datetime import datetime
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

def days_elapsed(start_date, end_date):
    # Both dates should be datetime.date or datetime.datetime objects
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date).date()
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date).date()
    return (end_date - start_date).days

def parse_due_date(due_date):
    if not due_date:
        return "No due date"
    date = datetime.fromisoformat(due_date).date()
    today = datetime.now().date()
    days = days_elapsed(date, today)
    if date < today:
        return f"Overdue by {abs(days)} days"
    else:
        return format_due_date(date)

def format_due_date(date):
    return f"Due {date.strftime('%d/%m/%Y')}"
