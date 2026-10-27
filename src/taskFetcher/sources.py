import os
from taskFetcher.taskSource import TaskSource
from taskFetcher.tickTick.tickTickSource import TickTickSource
from taskFetcher.todoApp.todoAppSource import TodoAppSource

ADAPTERS = {"todoapp": TodoAppSource, "ticktick": TickTickSource}
SOURCES = tuple(ADAPTERS)
DEFAULT_SOURCE = "todoapp"


def resolve_source(cli_value=None, env=os.environ) -> TaskSource:
    """The --source flag wins, then TASK_SOURCE from .env (for the systemd service), then the default.

    The source is built from env but not checked: missing settings surface in fetch(), so the screen can say so.
    """
    name = (cli_value or env.get("TASK_SOURCE") or DEFAULT_SOURCE).strip().lower()
    if name not in ADAPTERS:
        raise ValueError(f"Unknown task source '{name}'; choose one of: {', '.join(SOURCES)}")
    return ADAPTERS[name](env)
