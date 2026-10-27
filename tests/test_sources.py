import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from taskFetcher import sources


def test_todoapp_is_the_default_source():
    assert sources.resolve_source(None, env={}) == "todoapp"


def test_env_setting_beats_the_default():
    assert sources.resolve_source(None, env={"TASK_SOURCE": "ticktick"}) == "ticktick"


def test_the_flag_beats_the_env_setting():
    assert sources.resolve_source("todoapp", env={"TASK_SOURCE": "ticktick"}) == "todoapp"


def test_env_setting_is_forgiving_about_case_and_spaces_and_blank_means_default():
    assert sources.resolve_source(None, env={"TASK_SOURCE": " TickTick "}) == "ticktick"
    assert sources.resolve_source(None, env={"TASK_SOURCE": ""}) == "todoapp"


def test_an_unknown_env_source_is_an_error_naming_the_choices():
    with pytest.raises(ValueError, match="todoapp, ticktick"):
        sources.resolve_source(None, env={"TASK_SOURCE": "outlook"})


def test_each_source_uses_its_own_fetcher(monkeypatch):
    monkeypatch.setattr(sources, "fetch_todoapp_tasks", lambda: ["from todoapp"])
    monkeypatch.setattr(sources, "get_project_data", lambda project_id: {"project": project_id})
    monkeypatch.setattr(sources, "parse_project_tasks", lambda data: ["from ticktick", data["project"]])

    assert sources.fetch_tasks("todoapp") == ["from todoapp"]
    assert sources.fetch_tasks("ticktick") == ["from ticktick", sources.TICKTICK_PROJECT_ID]


def test_only_todoapp_always_uses_two_columns():
    assert sources.uses_columns("todoapp") and not sources.uses_columns("ticktick")
