import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import pytest
import schedule
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# `import __main__` would give pytest's own entry point, so the app's is loaded by path.
_spec = importlib.util.spec_from_file_location("todo_display_main", Path(__file__).resolve().parent.parent / "src" / "__main__.py")
app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(app)

from taskDisplay.refresh import DrawMessage, DrawTasks
from taskFetcher.sources import resolve_source

SOURCE = resolve_source("todoapp", env={})


class StopLoop(Exception):
    pass


class FakeRefresher:
    source = SOURCE

    def __init__(self, refresh):
        self.refresh = refresh


@pytest.fixture(autouse=True)
def clean_schedule():
    schedule.clear()
    yield
    schedule.clear()


def run_until_first_tick(monkeypatch, refresh):
    """Runs task_run with refreshes replaced by `refresh`, stopping the endless loop at its first sleep."""
    def stop(_seconds):
        raise StopLoop

    monkeypatch.setattr(app.time, "sleep", stop)
    with pytest.raises(StopLoop):
        app.task_run(30, FakeRefresher(refresh))


def test_run_draws_immediately_instead_of_waiting_for_the_first_interval(monkeypatch):
    refreshes = []
    run_until_first_tick(monkeypatch, lambda: refreshes.append(1))
    assert refreshes == [1]


def test_a_failed_refresh_does_not_end_the_run_loop(monkeypatch):
    def broken():
        raise OSError("display unplugged")

    run_until_first_tick(monkeypatch, broken)


def test_a_failed_scheduled_refresh_does_not_end_the_run_loop(monkeypatch):
    calls = []

    def fails_after_startup():
        calls.append(1)
        if len(calls) > 1:
            raise OSError("display unplugged")

    ticks = []

    def sleep(_seconds):
        ticks.append(1)
        if len(ticks) == 1:
            schedule.jobs[0].next_run = schedule.jobs[0].next_run.replace(year=2000)
        elif len(ticks) == 2:
            raise StopLoop

    monkeypatch.setattr(app.time, "sleep", sleep)
    with pytest.raises(StopLoop):
        app.task_run(30, FakeRefresher(fails_after_startup))
    assert len(calls) == 2


def test_running_with_no_arguments_names_options_that_exist(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["__main__.py"])

    app.main()

    out = capsys.readouterr().out
    assert "--image" not in out
    assert "--run" in out and "--task" in out and "--preview" in out


def test_the_refresher_is_built_for_the_chosen_source():
    assert app.make_refresher(SOURCE).source is SOURCE


def test_what_the_refresh_decided_is_rendered_as_a_panel_sized_image():
    render = app.make_renderer(SOURCE)

    tasks = render(DrawTasks([], datetime(2026, 10, 26, 12, 0)))
    stale = render(DrawTasks([], datetime(2026, 10, 26, 12, 0), stale=True))
    message = render(DrawMessage("Cannot reach TodoApp", "Will keep trying"))

    assert tasks.size == stale.size == message.size == (648, 480)
    assert tasks.tobytes() != stale.tobytes()  # the stale flag reaches the footer
    assert message.tobytes() != tasks.tobytes()


def test_fake_preview_needs_no_real_source(tmp_path):
    out = tmp_path / "fake.png"

    app.task_preview(str(out), SOURCE, fake="few", open_after=False)

    assert Image.open(out).size == (648, 480)
