import importlib.util
import sys
from pathlib import Path

import pytest
from PIL import Image
import schedule

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# `import __main__` would give pytest's own entry point, so the app's is loaded by path.
_spec = importlib.util.spec_from_file_location("todo_display_main", Path(__file__).resolve().parent.parent / "src" / "__main__.py")
app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(app)

from taskFetcher.sources import resolve_source

SOURCE = resolve_source("todoapp", env={})


class StopLoop(Exception):
    pass


@pytest.fixture(autouse=True)
def clean_schedule():
    schedule.clear()
    yield
    schedule.clear()


def run_until_first_tick(monkeypatch, refresh):
    """Runs task_run with refreshes replaced by `refresh`, stopping the endless loop at its first sleep."""
    monkeypatch.setattr(app, "task_image", refresh)

    def stop(_seconds):
        raise StopLoop

    monkeypatch.setattr(app.time, "sleep", stop)
    with pytest.raises(StopLoop):
        app.task_run(30, SOURCE)


def test_run_draws_immediately_instead_of_waiting_for_the_first_interval(monkeypatch):
    sources = []
    run_until_first_tick(monkeypatch, sources.append)
    assert sources == [SOURCE]


def test_a_failed_refresh_does_not_end_the_run_loop(monkeypatch):
    def broken(_source):
        raise OSError("display unplugged")

    run_until_first_tick(monkeypatch, broken)


def test_a_failed_scheduled_refresh_does_not_end_the_run_loop(monkeypatch):
    calls = []

    def fails_after_startup(source):
        calls.append(source)
        if len(calls) > 1:
            raise OSError("display unplugged")

    monkeypatch.setattr(app, "task_image", fails_after_startup)
    ticks = []

    def sleep(_seconds):
        ticks.append(1)
        if len(ticks) == 1:
            schedule.jobs[0].next_run = schedule.jobs[0].next_run.replace(year=2000)
        elif len(ticks) == 2:
            raise StopLoop

    monkeypatch.setattr(app.time, "sleep", sleep)
    with pytest.raises(StopLoop):
        app.task_run(30, SOURCE)
    assert len(calls) == 2


def test_running_with_no_arguments_names_options_that_exist(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["__main__.py"])

    app.main()

    out = capsys.readouterr().out
    assert "--image" not in out
    assert "--run" in out and "--task" in out and "--preview" in out


# --- a failing fetch never leaks the error text ---------------------------------------------

SECRET = "fake-secret-value"


@pytest.mark.parametrize("module_path, name, source", [
    ("taskFetcher.todoApp.todoAppSource", "get_access_token",
     resolve_source("todoapp", env={"TODOAPP_PROJECT_ID": "p", "TODOAPP_SPACE_ID": "s", "TODOAPP_KEY_FILE": "k"})),
    ("taskFetcher.tickTick.tickTickSource", "get_project_data", resolve_source("ticktick", env={})),
])
def test_a_failed_fetch_prints_and_shows_no_error_text(monkeypatch, capsys, module_path, name, source):
    def fails(*args, **kwargs):
        raise ConnectionError(f"https://example.test/?token={SECRET}")

    monkeypatch.setattr(sys.modules[module_path], name, fails)
    shown = []
    monkeypatch.setattr(app, "display_image", shown.append)
    monkeypatch.setattr(app, "policy", app.RefreshPolicy(source))

    app.task_image(source)

    assert len(shown) == 1  # the error notice was drawn
    assert SECRET not in capsys.readouterr().out


def test_fake_preview_needs_no_real_source(tmp_path):
    out = tmp_path / "fake.png"

    app.task_preview(str(out), SOURCE, fake="few", open_after=False)

    assert Image.open(out).size == (648, 480)
