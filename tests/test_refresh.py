import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskDisplay.refresh import REDRAW_AFTER, STALE_AFTER, DrawMessage, DrawTasks, Refresher
from taskFetcher.weather import Weather
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


# --- weather ---------------------------------------------------------------------------------------

class StubWeather:
    """Answers current(now) with whatever is set."""

    def __init__(self, weather=None):
        self.weather = weather

    def current(self, now):
        return self.weather


def weather_screen(weather):
    source, panel = ScriptedSource(), RecordingPanel()
    source.result = [Task("a", TODAY)]
    return source, panel, weather, Refresher(source, lambda action: action, panel, weather=weather)


def test_the_weather_is_drawn_with_the_tasks():
    source, panel, _, refresher = weather_screen(StubWeather(Weather(12, "rain")))

    refresher.refresh(NOW)

    assert panel.shown == [DrawTasks(source.result, NOW, weather=Weather(12, "rain"))]


def test_a_change_in_the_weather_redraws_but_the_same_weather_does_not():
    _, panel, weather, refresher = weather_screen(StubWeather(Weather(12, "rain")))
    refresher.refresh(NOW)

    refresher.refresh(NOW + timedelta(minutes=30))
    assert len(panel.shown) == 1

    weather.weather = Weather(13, "rain")
    refresher.refresh(NOW + timedelta(minutes=30))
    assert len(panel.shown) == 2


def test_no_weather_service_and_no_weather_both_draw_the_tasks_alone():
    _, panel, _, refresher = weather_screen(None)
    refresher.refresh(NOW)

    _, other_panel, _, other = weather_screen(StubWeather(None))
    other.refresh(NOW)

    assert panel.shown[0].weather is None and other_panel.shown[0].weather is None


def test_weather_that_blows_up_never_stops_the_tasks_being_drawn():
    class Broken:
        def current(self, now):
            raise RuntimeError("boom")

    _, panel, _, refresher = weather_screen(Broken())

    refresher.refresh(NOW)

    assert panel.shown[0].weather is None


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
