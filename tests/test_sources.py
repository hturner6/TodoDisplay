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
    monkeypatch.setenv("TICKTICK_PROJECT_ID", "p1")
    monkeypatch.setattr(sources, "fetch_todoapp_tasks", lambda: ["from todoapp"])
    monkeypatch.setattr(sources, "get_project_data", lambda project_id: {"project": project_id})
    monkeypatch.setattr(sources, "parse_project_tasks", lambda data: ["from ticktick", data["project"]])

    assert sources.fetch_tasks("todoapp") == ["from todoapp"]
    assert sources.fetch_tasks("ticktick") == ["from ticktick", "p1"]


def test_only_todoapp_always_uses_two_columns():
    assert sources.uses_columns("todoapp") and not sources.uses_columns("ticktick")


def test_ticktick_project_defaults_to_the_one_in_use():
    assert sources.ticktick_project_id(env={}) == "687164e8fb06fe7e7a3d621a"


def test_env_setting_picks_the_ticktick_project():
    assert sources.ticktick_project_id(env={"TICKTICK_PROJECT_ID": "abc123"}) == "abc123"


def test_blank_env_setting_falls_back_to_the_default():
    assert sources.ticktick_project_id(env={"TICKTICK_PROJECT_ID": " "}) == "687164e8fb06fe7e7a3d621a"
