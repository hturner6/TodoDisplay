import os
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks
from taskFetcher.tickTick.tickTickClient import get_project_data
from taskFetcher.todoApp.todoAppFetcher import fetch_todoapp_tasks

SOURCES = ("todoapp", "ticktick")
DEFAULT_SOURCE = "todoapp"
TICKTICK_PROJECT_ID = "687164e8fb06fe7e7a3d621a"


def resolve_source(cli_value=None, env=os.environ) -> str:
    """The --source flag wins, then TASK_SOURCE from .env (for the systemd service), then the default."""
    name = (cli_value or env.get("TASK_SOURCE") or DEFAULT_SOURCE).strip().lower()
    if name not in SOURCES:
        raise ValueError(f"Unknown task source '{name}'; choose one of: {', '.join(SOURCES)}")
    return name


def fetch_tasks(source: str):
    if source == "todoapp":
        return fetch_todoapp_tasks()
    return parse_project_tasks(get_project_data(TICKTICK_PROJECT_ID))


def uses_columns(source: str) -> bool:
    """TodoApp shows Daily and Weekly Items side by side, so its screen is always two columns."""
    return source == "todoapp"
