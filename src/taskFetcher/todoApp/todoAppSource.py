import os
from taskFetcher.taskSource import TaskSource, http_status
from taskFetcher.todoApp.auth import get_access_token
from taskFetcher.todoApp.firestoreClient import list_documents
from taskFetcher.todoApp.todoItemParser import parse_todo_items

REQUIRED = ('TODOAPP_PROJECT_ID', 'TODOAPP_SPACE_ID', 'TODOAPP_KEY_FILE')


class TodoAppSource(TaskSource):
    """Every Daily and Weekly Item, read with the read-only service account. The screen chooses which to show."""
    name = "todoapp"
    # Daily and Weekly Items sit side by side, so this source's screen is always two columns.
    two_columns = True

    def __init__(self, env=os.environ):
        # Only the values this source needs, never the rest of the environment.
        self._settings = {name: env.get(name) for name in REQUIRED}

    def fetch(self):
        missing = [name for name in REQUIRED if not self._settings[name]]
        if missing:
            raise RuntimeError(f"Missing in .env: {', '.join(missing)}. See README: Connecting the Pi to TodoApp.")

        token = get_access_token(self._settings['TODOAPP_KEY_FILE'])
        documents = list_documents(self._settings['TODOAPP_PROJECT_ID'], self._settings['TODOAPP_SPACE_ID'],
                                   'todoItems', token)
        return parse_todo_items(documents)

    def describe_error(self, error: Exception) -> tuple[str, str]:
        if isinstance(error, RuntimeError):
            return "TodoApp not set up", "See the README"
        if http_status(error) in (400, 401, 403):
            return "Sign-in failed", "The TodoApp key may have been revoked"
        return "Cannot reach TodoApp", "Will keep trying"
