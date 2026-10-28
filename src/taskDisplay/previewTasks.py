from datetime import date, datetime, time, timedelta
from models.task import Task
from taskFetcher.taskSource import TaskSource


def _days_ago(today: date, days: int):
    return today - timedelta(days=days)


def _this_week(today: date, weekday: int):
    """The date of the given weekday (Monday is 0) in the week containing today."""
    return today - timedelta(days=today.weekday()) + timedelta(days=weekday)


def _weekly(today: date, title: str, weekday: int, **kwargs) -> Task:
    return Task(title, _this_week(today, weekday), weekly=True, **kwargs)


def _empty(today: date) -> list[Task]:
    return []


def _few(today: date) -> list[Task]:
    return [
        Task("Book driving lessons", _days_ago(today, 2)),
        Task("Book practical test", _days_ago(today, 2)),
        Task("Buy milk", today),
        Task("Call the dentist", today, scheduled_time=time(9, 30)),
        _weekly(today, "Clean the bike", 5),
        _weekly(today, "Plan the allotment", 6),
        _weekly(today, "Send the invoice", 4, priority=True),
    ]


def _many(today: date) -> list[Task]:
    return ([Task(f"Task number {i}", _days_ago(today, i % 4)) for i in range(1, 21)]
            + [_weekly(today, f"Weekly task {i}", i % 7) for i in range(1, 13)])


def _long(today: date) -> list[Task]:
    return [
        Task("A very long task title that will not fit on a single line of the display and keeps going", today),
        Task("Supercalifragilisticexpialidocious_without_any_spaces_to_break_on_at_all", today),
        Task("Short", _days_ago(today, 1)),
        _weekly(today, "A weekly title that is far too long to fit in the narrower column of the display", 3),
        _weekly(today, "Supercalifragilisticexpialidocious_without_any_spaces", 4),
    ]


def _states(today: date) -> list[Task]:
    return [
        Task("To do", today),
        Task("Priority to do", today, priority=True),
        Task("Done", today, status=Task.DONE),
        Task("Moved to tomorrow", today, status=Task.MOVED),
        Task("Cancelled item", today, status=Task.CANCELLED),
        Task("A note", today, status=Task.NOTE),
        _weekly(today, "Weekly to do", 2),
        _weekly(today, "Weekly done", 3, status=Task.DONE),
        _weekly(today, "Weekly moved on", 4, status=Task.MOVED),
        _weekly(today, "Weekly cancelled", 5, status=Task.CANCELLED),
    ]


# Layouts worth checking while tuning the look: nothing to show, a typical day, a full screen,
# titles that are too wide for the display, and every completion state. Each is built relative
# to the day it is given, so a screen is the same whenever it is drawn.
SCENARIOS = {
    "empty": _empty,
    "few": _few,
    "many": _many,
    "long": _long,
    "states": _states,
}


def fake_tasks(scenario: str, today: date = None) -> list[Task]:
    """The sample tasks of a scenario, dated relative to today (the real date unless one is given)."""
    return SCENARIOS[scenario](today or datetime.now().date())


class FakeSource(TaskSource):
    """Sample tasks for --preview --fake, laid out like the TodoApp source. Not a real source: --source cannot pick it."""
    name = "fake"
    two_columns = True

    def __init__(self, scenario: str):
        self._scenario = scenario

    def fetch(self):
        return fake_tasks(self._scenario)

    def describe_error(self, error: Exception) -> tuple[str, str]:
        return "Cannot reach TodoApp", "Will keep trying"
