import importlib.util
import sys
from pathlib import Path

import pytest
import schedule

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# `import __main__` would give pytest's own entry point, so the app's is loaded by path.
_spec = importlib.util.spec_from_file_location("todo_display_main", Path(__file__).resolve().parent.parent / "src" / "__main__.py")
app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(app)


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
        app.task_run(30, "todoapp")


def test_run_draws_immediately_instead_of_waiting_for_the_first_interval(monkeypatch):
    sources = []
    run_until_first_tick(monkeypatch, sources.append)
    assert sources == ["todoapp"]


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
        app.task_run(30, "todoapp")
    assert len(calls) == 2


def test_running_with_no_arguments_names_options_that_exist(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["__main__.py"])

    app.main()

    out = capsys.readouterr().out
    assert "--image" not in out
    assert "--run" in out and "--task" in out and "--preview" in out
