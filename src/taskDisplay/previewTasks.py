from datetime import datetime, time, timedelta
from models.task import Task
from taskFetcher.taskSource import TaskSource


def _today():
    return datetime.now().date()


def _days_ago(days: int):
    return _today() - timedelta(days=days)


def _this_week(weekday: int):
    """The date of the given weekday (Monday is 0) in the current week."""
    return _today() - timedelta(days=_today().weekday()) + timedelta(days=weekday)


def _weekly(title: str, weekday: int, **kwargs) -> Task:
    return Task(title, _this_week(weekday), weekly=True, **kwargs)


def _empty() -> list[Task]:
    return []


def _few() -> list[Task]:
    return [
        Task("Book driving lessons", _days_ago(2)),
        Task("Book practical test", _days_ago(2)),
        Task("Buy milk", _today()),
        Task("Call the dentist", _today(), scheduled_time=time(9, 30)),
        _weekly("Clean the bike", 5),
        _weekly("Plan the allotment", 6),
        _weekly("Send the invoice", 4, priority=True),
    ]


def _many() -> list[Task]:
    return ([Task(f"Task number {i}", _days_ago(i % 4)) for i in range(1, 21)]
            + [_weekly(f"Weekly task {i}", i % 7) for i in range(1, 13)])


def _long() -> list[Task]:
    return [
        Task("A very long task title that will not fit on a single line of the display and keeps going", _today()),
        Task("Supercalifragilisticexpialidocious_without_any_spaces_to_break_on_at_all", _today()),
        Task("Short", _days_ago(1)),
        _weekly("A weekly title that is far too long to fit in the narrower column of the display", 3),
        _weekly("Supercalifragilisticexpialidocious_without_any_spaces", 4),
    ]


def _states() -> list[Task]:
    return [
        Task("To do", _today()),
        Task("Priority to do", _today(), priority=True),
        Task("Done", _today(), status=Task.DONE),
        Task("Moved to tomorrow", _today(), status=Task.MOVED),
        Task("Cancelled item", _today(), status=Task.CANCELLED),
        Task("A note", _today(), status=Task.NOTE),
        _weekly("Weekly to do", 2),
        _weekly("Weekly done", 3, status=Task.DONE),
        _weekly("Weekly moved on", 4, status=Task.MOVED),
        _weekly("Weekly cancelled", 5, status=Task.CANCELLED),
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


class FakeSource(TaskSource):
    """Sample tasks for --preview --fake, laid out like the TodoApp source. Not a real source: --source cannot pick it."""
    name = "fake"
    two_columns = True

    def __init__(self, scenario: str):
        self._scenario = scenario

    def fetch(self):
        return fake_tasks(self._scenario)

    def describe_error(self, error: Exception) -> tuple[str, str]:
        return "Sample tasks failed", "This source cannot fail"
