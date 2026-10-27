import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks


def test_a_project_becomes_a_list_of_tasks():
    project = {"project": {"name": "Home"}, "tasks": [{"title": "Buy milk"}, {"title": "Call the dentist", "dueDate": None}]}

    tasks = parse_project_tasks(project)

    assert [(t.title, t.due_date, t.status) for t in tasks] == [("Buy milk", None, Task.TODO),
                                                              ("Call the dentist", None, Task.TODO)]


def test_a_project_with_no_tasks_gives_no_tasks():
    assert parse_project_tasks({}) == []


def test_a_task_prints_its_title_and_date():
    assert repr(Task("Buy milk", None)) == "Task(title=Buy milk, due_date=None)"
