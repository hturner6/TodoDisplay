import os
from datetime import date
from taskFetcher.todoApp.auth import get_access_token
from taskFetcher.todoApp.firestoreClient import list_documents
from taskFetcher.todoApp.todoItemParser import parse_todo_items, select_for_display

REQUIRED = ('TODOAPP_PROJECT_ID', 'TODOAPP_SPACE_ID', 'TODOAPP_KEY_FILE')


def fetch_todoapp_tasks(today=None, env=os.environ):
    """Today's Daily Items and this week's Weekly Items, read with the read-only service account."""
    missing = [name for name in REQUIRED if not env.get(name)]
    if missing:
        raise RuntimeError(f"Missing in .env: {', '.join(missing)}. See README: Connecting the Pi to TodoApp.")

    token = get_access_token(env['TODOAPP_KEY_FILE'])
    documents = list_documents(env['TODOAPP_PROJECT_ID'], env['TODOAPP_SPACE_ID'], 'todoItems', token)
    return select_for_display(parse_todo_items(documents), today or date.today())
