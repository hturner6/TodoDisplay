from datetime import date, time, timedelta
from models.task import Task

STATES = {
    'isTodo': Task.TODO,
    'isDone': Task.DONE,
    'isCancelled': Task.CANCELLED,
    'isMoved': Task.MOVED,
}

_MISSING = object()


def _decode(value):
    """A Firestore typed value, e.g. {'stringValue': 'x'}, as a plain Python value."""
    if 'nullValue' in value:
        return None
    if 'integerValue' in value:
        return int(value['integerValue'])
    for kind in ('stringValue', 'booleanValue', 'doubleValue'):
        if kind in value:
            return value[kind]
    return _MISSING


def _field(document, name, default=None):
    """The value of a synced field, which the app stores as {value, clock}."""
    try:
        wrapped = document['fields'][name]['mapValue']['fields']['value']
    except (KeyError, TypeError):
        return default
    decoded = _decode(wrapped)
    return default if decoded is _MISSING else decoded


def parse_todo_item(document):
    """A Task for one todoItems document, or None for one that is deleted, a note or unreadable."""
    if _field(document, 'deleted', False) or _field(document, 'isNote', False):
        return None
    title = _field(document, 'title')
    scheduled = _field(document, 'scheduledDate')
    if not title or not scheduled:
        return None
    try:
        scheduled_date = date.fromisoformat(scheduled)
        scheduled_time = _field(document, 'scheduledTime')
        scheduled_time = time.fromisoformat(scheduled_time) if scheduled_time else None
    except ValueError:
        return None

    return Task(
        title=title,
        due_date=scheduled_date,
        status=STATES.get(_field(document, 'completionState'), Task.TODO),
        priority=bool(_field(document, 'priority', False)),
        scheduled_time=scheduled_time,
        weekly=not _field(document, 'onSpecifiedDay', True),
    )


def parse_todo_items(documents):
    tasks = (parse_todo_item(document) for document in documents)
    return [task for task in tasks if task is not None]


def week_bounds(today):
    """Monday and Sunday of the week containing today."""
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def select_for_display(tasks, today):
    """Today's Daily Items (by time, untimed last) then this week's Weekly Items (by date)."""
    monday, sunday = week_bounds(today)
    daily = [t for t in tasks if not t.weekly and t.due_date == today]
    weekly = [t for t in tasks if t.weekly and monday <= t.due_date <= sunday]
    daily.sort(key=lambda t: (t.scheduled_time is None, t.scheduled_time or time.min, t.title))
    weekly.sort(key=lambda t: (t.due_date, t.title))
    return daily + weekly
