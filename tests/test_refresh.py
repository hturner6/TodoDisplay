import sys
from datetime import datetime, time, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskDisplay.quietHours import QuietHours
from taskDisplay.refresh import REDRAW_AFTER, STALE_AFTER, DrawMessage, DrawTasks, Refresher
from taskFetcher.sources import resolve_source
from taskFetcher.taskSource import TaskSource
from taskFetcher.tickTick import tickTickSource
from taskFetcher.todoApp import todoAppSource

NOW = datetime(2026, 10, 26, 12, 0)
TODAY = NOW.date()
SECRET = "fake-secret-value"


class ScriptedSource(TaskSource):
    """Returns whatever result is set: a list of Tasks, or an exception to raise."""
    name = "scripted"

    def __init__(self):
        self.result = []

    def fetch(self):
        if isinstance(self.result, Exception):
            raise self.result
        return list(self.result)

    def describe_error(self, error):
        return "Cannot reach it", "Will keep trying"


class RecordingPanel:
    def __init__(self):
        self.shown = []

    def show(self, image):
        self.shown.append(image)


def screen(source=None, panel=None):
    """A Refresher whose renderer is the identity, so what the panel shows is what was decided."""
    source = source or ScriptedSource()
    panel = panel or RecordingPanel()
    return source, panel, Refresher(source, lambda action: action, panel)


def test_the_first_refresh_draws_the_tasks():
    source, panel, refresher = screen()
    source.result = [Task("a", TODAY)]

    refresher.refresh(NOW)

    assert panel.shown == [DrawTasks(source.result, NOW)]


def test_unchanged_tasks_are_not_redrawn_until_the_redraw_interval():
    source, panel, refresher = screen()
    source.result = [Task("a", TODAY)]
    refresher.refresh(NOW)

    refresher.refresh(NOW + timedelta(minutes=30))
    assert len(panel.shown) == 1

    refresher.refresh(NOW + REDRAW_AFTER)
    assert len(panel.shown) == 2


def test_changed_tasks_are_redrawn_straight_away():
    source, panel, refresher = screen()
    source.result = [Task("a", TODAY)]
    refresher.refresh(NOW)

    source.result = [Task("b", TODAY)]
    refresher.refresh(NOW + timedelta(minutes=30))

    assert len(panel.shown) == 2


def test_a_change_to_a_task_that_is_not_on_the_screen_does_not_redraw():
    source, panel, refresher = screen()
    far_off = TODAY + timedelta(days=30)
    source.result = [Task("a", TODAY), Task("next month", far_off)]
    refresher.refresh(NOW)

    source.result = [Task("a", TODAY), Task("renamed", far_off, priority=True)]
    refresher.refresh(NOW + timedelta(minutes=30))

    assert len(panel.shown) == 1


def test_a_task_changing_state_redraws_the_screen():
    source, panel, refresher = screen()
    source.result = [Task("a", TODAY)]
    refresher.refresh(NOW)

    source.result = [Task("a", TODAY, status=Task.DONE)]
    refresher.refresh(NOW + timedelta(minutes=30))

    assert len(panel.shown) == 2


def test_a_change_of_time_or_week_redraws_the_screen():
    source, panel, refresher = screen()
    source.result = [Task("a", TODAY)]
    refresher.refresh(NOW)

    source.result = [Task("a", TODAY, scheduled_time=NOW.time())]
    refresher.refresh(NOW)
    assert len(panel.shown) == 2

    source.result = [Task("a", TODAY, scheduled_time=NOW.time(), weekly=True)]
    refresher.refresh(NOW)
    assert len(panel.shown) == 3

    refresher.refresh(NOW)
    assert len(panel.shown) == 3


def test_a_failure_with_nothing_drawn_yet_shows_the_sources_error_once():
    source, panel, refresher = screen()
    source.result = OSError("no network")

    refresher.refresh(NOW)
    refresher.refresh(NOW + timedelta(minutes=30))

    assert panel.shown == [DrawMessage("Cannot reach it", "Will keep trying")]


def test_a_failure_keeps_the_screen_until_the_data_is_stale_then_marks_it_once():
    source, panel, refresher = screen()
    source.result = [Task("a", TODAY)]
    refresher.refresh(NOW)
    tasks = source.result
    source.result = OSError("no network")

    refresher.refresh(NOW + timedelta(hours=1))
    assert len(panel.shown) == 1

    refresher.refresh(NOW + STALE_AFTER + timedelta(minutes=1))
    assert panel.shown[-1] == DrawTasks(tasks, NOW, stale=True)

    refresher.refresh(NOW + timedelta(hours=3))
    assert len(panel.shown) == 2


def test_recovery_after_a_stale_screen_redraws():
    source, panel, refresher = screen()
    source.result = [Task("a", TODAY)]
    refresher.refresh(NOW)
    source.result = OSError("no network")
    refresher.refresh(NOW + timedelta(hours=3))

    source.result = [Task("a", TODAY)]
    refresher.refresh(NOW + timedelta(hours=4))

    assert panel.shown[-1] == DrawTasks(source.result, NOW + timedelta(hours=4))


def test_a_panel_failure_is_raised_for_the_run_loop_to_guard():
    class BrokenPanel:
        def show(self, image):
            raise OSError("GPIO busy")

    source, _, refresher = screen(panel=BrokenPanel())
    source.result = [Task("a", TODAY)]

    with pytest.raises(OSError, match="GPIO busy"):
        refresher.refresh(NOW)


def test_refreshing_without_a_time_uses_the_clock():
    source, panel, refresher = screen()
    source.result = [Task("a", datetime.now().date())]

    refresher.refresh()

    assert abs(panel.shown[0].updated_at - datetime.now()) < timedelta(seconds=5)


# --- quiet hours ----------------------------------------------------------------------------------

class CountingSource(ScriptedSource):
    def __init__(self):
        super().__init__()
        self.fetches = 0

    def fetch(self):
        self.fetches += 1
        return super().fetch()


def quiet_screen():
    source = CountingSource()
    panel = RecordingPanel()
    quiet = QuietHours.parse("23:00-06:00")
    return source, panel, Refresher(source, lambda action: action, panel, quiet_hours=quiet)


def test_nothing_is_fetched_or_drawn_during_quiet_hours():
    source, panel, refresher = quiet_screen()
    source.result = [Task("a", TODAY)]

    refresher.refresh(datetime(2026, 10, 26, 2, 0))

    assert source.fetches == 0 and panel.shown == []


def test_the_first_refresh_after_quiet_hours_draws_even_if_nothing_changed():
    source, panel, refresher = quiet_screen()
    source.result = [Task("a", TODAY)]
    refresher.refresh(datetime(2026, 10, 26, 22, 30))

    refresher.refresh(datetime(2026, 10, 27, 5, 59))
    assert len(panel.shown) == 1

    refresher.refresh(datetime(2026, 10, 27, 6, 0))
    assert len(panel.shown) == 2


@pytest.mark.parametrize("moment, quiet", [
    (time(22, 59), False), (time(23, 0), True), (time(0, 0), True), (time(5, 59), True), (time(6, 0), False),
])
def test_a_window_that_crosses_midnight_is_quiet_late_and_early(moment, quiet):
    assert QuietHours.parse("23:00-06:00").contains(moment) is quiet


@pytest.mark.parametrize("moment, quiet", [(time(0, 59), False), (time(1, 0), True), (time(5, 59), True), (time(6, 0), False)])
def test_a_window_within_one_day_is_quiet_only_inside_it(moment, quiet):
    assert QuietHours.parse("01:00-06:00").contains(moment) is quiet


@pytest.mark.parametrize("text, expected", [
    ("off", None), ("", None), (None, None), (" 22:30 - 07:15 ", QuietHours(time(22, 30), time(7, 15))),
])
def test_quiet_hours_config_text(text, expected):
    assert QuietHours.from_config(text) == expected


def test_unreadable_quiet_hours_config_is_an_error_not_a_silent_default():
    with pytest.raises(ValueError):
        QuietHours.from_config("late-ish")


# --- a failing fetch never leaks the error text -------------------------------------------------

@pytest.mark.parametrize("module, name, source", [
    (todoAppSource, "get_access_token",
     resolve_source("todoapp", env={"TODOAPP_PROJECT_ID": "p", "TODOAPP_SPACE_ID": "s", "TODOAPP_KEY_FILE": "k"})),
    (tickTickSource, "get_project_data", resolve_source("ticktick", env={})),
])
def test_a_failed_fetch_prints_and_shows_no_error_text(monkeypatch, capsys, module, name, source):
    def fails(*args, **kwargs):
        raise ConnectionError(f"https://example.test/?token={SECRET}")

    monkeypatch.setattr(module, name, fails)
    _, panel, refresher = screen(source=source)

    refresher.refresh(NOW)

    (message,) = panel.shown
    assert isinstance(message, DrawMessage)
    assert SECRET not in repr(message) and SECRET not in capsys.readouterr().out
