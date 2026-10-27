import os
from taskFetcher.taskSource import TaskSource, http_status
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks
from taskFetcher.tickTick.tickTickClient import get_project_data

DEFAULT_PROJECT_ID = "687164e8fb06fe7e7a3d621a"


class TickTickSource(TaskSource):
    """The tasks in one TickTick project, as a single list."""
    name = "ticktick"

    def __init__(self, env=os.environ):
        # Only the values this source needs, never the rest of the environment.
        # TICKTICK_PROJECT_ID falls back to the project the display has always shown.
        self._project_id = (env.get("TICKTICK_PROJECT_ID") or "").strip() or DEFAULT_PROJECT_ID
        self._token = env.get("ACCESS_TOKEN")

    def fetch(self):
        return parse_project_tasks(get_project_data(self._project_id, self._token))

    def describe_error(self, error: Exception) -> tuple[str, str]:
        if http_status(error) == 401:
            return "Sign-in expired", "The TickTick token needs renewing"
        return "Cannot reach TickTick", "Will keep trying"
