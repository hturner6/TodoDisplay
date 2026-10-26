from datetime import datetime, timedelta
from models.task import Task


def _today():
    return datetime.now().date()


def _days_ago(days: int):
    return _today() - timedelta(days=days)


def _empty() -> list[Task]:
    return []


def _few() -> list[Task]:
    return [
        Task("Book driving lessons", _days_ago(2)),
        Task("Book practical test", _days_ago(2)),
        Task("Buy milk", _today()),
    ]


def _many() -> list[Task]:
    return [Task(f"Task number {i}", _days_ago(i % 4)) for i in range(1, 21)]


def _long() -> list[Task]:
    return [
        Task("A very long task title that will not fit on a single line of the display and keeps going", _today()),
        Task("Supercalifragilisticexpialidocious_without_any_spaces_to_break_on_at_all", _today()),
        Task("Short", _days_ago(1)),
    ]


def _states() -> list[Task]:
    return [
        Task("To do", _today()),
        Task("Priority to do", _today(), priority=True),
        Task("Done", _today(), status=Task.DONE),
        Task("Moved to tomorrow", _today(), status=Task.MOVED),
        Task("Cancelled item", _today(), status=Task.CANCELLED),
        Task("A note", _today(), status=Task.NOTE),
    ]


# Layouts worth checking while tuning the look: nothing to show, a typical day, a full screen,
# titles that are too wide for the display, and every completion state.
SCENARIOS = {
    "empty": _empty,
    "few": _few,
    "many": _many,
    "long": _long,
    "states": _states,
}


def fake_tasks(scenario: str) -> list[Task]:
    return SCENARIOS[scenario]()
