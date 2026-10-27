import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from taskFetcher import sources
from taskFetcher.tickTick import tickTickSource
from taskFetcher.tickTick.tickTickSource import DEFAULT_PROJECT_ID, TickTickSource
from taskFetcher.todoApp import todoAppSource
from taskFetcher.todoApp.todoAppSource import TodoAppSource

# Obviously fake values: tests never read a real .env.
TODOAPP_ENV = {"TODOAPP_PROJECT_ID": "fake-project", "TODOAPP_SPACE_ID": "fake-space", "TODOAPP_KEY_FILE": "/fake/key.json"}
SECRET = "fake-secret-value"


class Response:
    def __init__(self, status_code):
        self.status_code = status_code


class HttpError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.response = Response(status_code)


def test_todoapp_is_the_default_source():
    assert sources.resolve_source(None, env={}).name == "todoapp"


def test_env_setting_beats_the_default():
    assert sources.resolve_source(None, env={"TASK_SOURCE": "ticktick"}).name == "ticktick"


def test_the_flag_beats_the_env_setting():
    assert sources.resolve_source("todoapp", env={"TASK_SOURCE": "ticktick"}).name == "todoapp"


def test_env_setting_is_forgiving_about_case_and_spaces_and_blank_means_default():
    assert sources.resolve_source(None, env={"TASK_SOURCE": " TickTick "}).name == "ticktick"
    assert sources.resolve_source(None, env={"TASK_SOURCE": ""}).name == "todoapp"


def test_an_unknown_env_source_is_an_error_naming_the_choices():
    with pytest.raises(ValueError, match="todoapp, ticktick"):
        sources.resolve_source(None, env={"TASK_SOURCE": "outlook"})


def test_resolving_does_not_check_the_settings_so_the_screen_can_report_them():
    source = sources.resolve_source("todoapp", env={})

    with pytest.raises(RuntimeError, match="TODOAPP_PROJECT_ID"):
        source.fetch()


def test_only_todoapp_always_uses_two_columns():
    assert TodoAppSource(env={}).two_columns and not TickTickSource(env={}).two_columns


# --- env security ---------------------------------------------------------------------------

@pytest.mark.parametrize("source_class", [TodoAppSource, TickTickSource])
def test_a_source_does_not_hold_the_rest_of_the_environment(source_class):
    source = source_class(env={**TODOAPP_ENV, "ACCESS_TOKEN": SECRET, "UNRELATED": "fake-unrelated"})

    assert "fake-unrelated" not in repr(vars(source))


@pytest.mark.parametrize("source_class", [TodoAppSource, TickTickSource])
def test_printing_a_source_shows_only_its_name(source_class):
    source = source_class(env={**TODOAPP_ENV, "ACCESS_TOKEN": SECRET})

    assert repr(source) == f"<{source.name} source>"
    assert str(source) == repr(source)


@pytest.mark.parametrize("source", [
    TodoAppSource(env=TODOAPP_ENV),
    TickTickSource(env={"ACCESS_TOKEN": SECRET}),
])
@pytest.mark.parametrize("error", [
    RuntimeError(f"bad {SECRET}"), ConnectionError(f"bad {SECRET}"),
    HttpError(f"bad {SECRET}", 400), HttpError(f"bad {SECRET}", 401), HttpError(f"bad {SECRET}", 500),
])
def test_error_wording_never_includes_the_error_text(source, error):
    assert SECRET not in " ".join(source.describe_error(error))


# --- todoapp --------------------------------------------------------------------------------

def test_todoapp_fetch_uses_its_own_settings(monkeypatch):
    calls = []
    monkeypatch.setattr(todoAppSource, "get_access_token", lambda key_file: calls.append(key_file) or "token")
    monkeypatch.setattr(todoAppSource, "list_documents",
                        lambda project, space, table, token: calls.append((project, space, table, token)) or [])

    assert TodoAppSource(env=TODOAPP_ENV).fetch() == []
    assert calls == ["/fake/key.json", ("fake-project", "fake-space", "todoItems", "token")]


def test_todoapp_errors_name_todoapp():
    source = TodoAppSource(env={})

    assert source.describe_error(HttpError("x", 400))[0] == "Sign-in failed"
    assert source.describe_error(RuntimeError("Missing in .env: TODOAPP_KEY_FILE"))[0] == "TodoApp not set up"
    assert source.describe_error(ConnectionError("boom"))[0] == "Cannot reach TodoApp"


# --- ticktick -------------------------------------------------------------------------------

def fetch_ticktick(monkeypatch, env):
    calls = []
    monkeypatch.setattr(tickTickSource, "get_project_data", lambda project_id, token: calls.append((project_id, token)) or {})
    monkeypatch.setattr(tickTickSource, "parse_project_tasks", lambda data: ["from ticktick"])
    assert TickTickSource(env=env).fetch() == ["from ticktick"]
    return calls


def test_ticktick_project_defaults_to_the_one_in_use(monkeypatch):
    assert fetch_ticktick(monkeypatch, {"ACCESS_TOKEN": "t"}) == [(DEFAULT_PROJECT_ID, "t")]


def test_env_setting_picks_the_ticktick_project(monkeypatch):
    assert fetch_ticktick(monkeypatch, {"TICKTICK_PROJECT_ID": "abc123", "ACCESS_TOKEN": "t"}) == [("abc123", "t")]


def test_blank_env_setting_falls_back_to_the_default_project(monkeypatch):
    assert fetch_ticktick(monkeypatch, {"TICKTICK_PROJECT_ID": " ", "ACCESS_TOKEN": "t"}) == [(DEFAULT_PROJECT_ID, "t")]


def test_ticktick_errors_name_ticktick():
    source = TickTickSource(env={})

    assert source.describe_error(HttpError("x", 401))[0] == "Sign-in expired"
    assert source.describe_error(OSError("no network"))[0] == "Cannot reach TickTick"
