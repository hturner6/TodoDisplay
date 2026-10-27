import base64
import json
import shutil
import subprocess
import sys
from datetime import date, time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskFetcher.todoApp import auth
from taskFetcher.todoApp.firestoreClient import list_documents
from taskFetcher.todoApp.todoAppSource import TodoAppSource
from taskFetcher.todoApp.todoItemParser import parse_todo_item, parse_todo_items, select_for_display, week_bounds

WEDNESDAY = date(2026, 10, 28)  # week is Mon 26 Oct to Sun 1 Nov


def synced(value):
    typed = {str: "stringValue", bool: "booleanValue", int: "integerValue"}
    wire = {"nullValue": None} if value is None else {typed[type(value)]: str(value) if isinstance(value, int) and not isinstance(value, bool) else value}
    return {"mapValue": {"fields": {"value": wire, "clock": {"stringValue": "0001"}}}}


def item(title="Buy milk", scheduled=WEDNESDAY, daily=True, state="isTodo", **extra):
    fields = {"title": title, "scheduledDate": scheduled.isoformat(), "onSpecifiedDay": daily,
              "completionState": state, "scheduledTime": None, "priority": False,
              "isNote": False, "deleted": False, **extra}
    return {"name": f"projects/p/databases/(default)/documents/spaces/s/todoItems/{title}",
            "fields": {"version": {"integerValue": "1"}, **{k: synced(v) for k, v in fields.items()}}}


def test_a_daily_item_is_unwrapped_into_a_task():
    task = parse_todo_item(item("Call mum", daily=True, scheduledTime="09:30", priority=True))

    assert (task.title, task.due_date, task.weekly, task.priority) == ("Call mum", WEDNESDAY, False, True)
    assert task.scheduled_time == time(9, 30)
    assert task.status == Task.TODO


def test_a_weekly_item_is_flagged_weekly():
    assert parse_todo_item(item(daily=False)).weekly is True


@pytest.mark.parametrize("state,expected", [("isTodo", Task.TODO), ("isDone", Task.DONE),
                                            ("isCancelled", Task.CANCELLED), ("isMoved", Task.MOVED)])
def test_completion_states_map_to_task_statuses(state, expected):
    assert parse_todo_item(item(state=state)).status == expected


def test_deleted_items_and_notes_are_dropped():
    documents = [item("gone", deleted=True), item("a note", isNote=True), item("kept")]

    assert [t.title for t in parse_todo_items(documents)] == ["kept"]


def test_unreadable_documents_are_skipped_not_fatal():
    broken = [{"fields": {}}, {}, item("bad date", scheduled=WEDNESDAY) | {"fields": {
        **item()["fields"], "scheduledDate": synced("not-a-date")}}]

    assert parse_todo_items(broken + [item("fine")])[0].title == "fine"
    assert len(parse_todo_items(broken + [item("fine")])) == 1


def test_weeks_run_monday_to_sunday():
    assert week_bounds(date(2026, 10, 26)) == (date(2026, 10, 26), date(2026, 11, 1))
    assert week_bounds(date(2026, 11, 1)) == (date(2026, 10, 26), date(2026, 11, 1))


def test_selection_keeps_daily_items_up_to_today_and_this_weeks_weekly_items():
    tasks = parse_todo_items([
        item("today", WEDNESDAY),
        item("overdue", date(2026, 10, 27)),
        item("tomorrow", date(2026, 10, 29)),
        item("this week", date(2026, 10, 30), daily=False),
        item("sunday", date(2026, 11, 1), daily=False),
        item("last week", date(2026, 10, 25), daily=False),
        item("next week", date(2026, 11, 2), daily=False),
    ])

    assert [t.title for t in select_for_display(tasks, WEDNESDAY)] == ["overdue", "today", "this week", "sunday"]


@pytest.mark.parametrize("state", ["isDone", "isCancelled", "isMoved"])
def test_finished_daily_items_from_past_days_are_not_shown(state):
    tasks = parse_todo_items([item("old", date(2026, 10, 20), state=state), item("today", WEDNESDAY, state=state)])

    assert [t.title for t in select_for_display(tasks, WEDNESDAY)] == ["today"]


def test_overdue_daily_items_come_before_todays_whatever_their_time():
    tasks = parse_todo_items([item("today early", WEDNESDAY, scheduledTime="07:00"),
                              item("old late", date(2026, 10, 20), scheduledTime="22:00")])

    assert [t.title for t in select_for_display(tasks, WEDNESDAY)] == ["old late", "today early"]


def test_daily_items_sort_by_time_with_untimed_last():
    tasks = parse_todo_items([item("untimed"), item("late", scheduledTime="18:00"), item("early", scheduledTime="08:00")])

    assert [t.title for t in select_for_display(tasks, WEDNESDAY)] == ["early", "late", "untimed"]


def test_listing_follows_pagination_until_the_last_page():
    pages = [{"documents": [item("a"), item("b")], "nextPageToken": "t1"},
             {"documents": [item("c")], "nextPageToken": "t2"},
             {"documents": [item("d")]}]
    calls = []

    class Response:
        def __init__(self, body): self.body = body
        def raise_for_status(self): pass
        def json(self): return self.body

    def fake_get(url, headers, params, timeout):
        calls.append(params.get("pageToken"))
        return Response(pages[len(calls) - 1])

    documents = list_documents("proj", "space", "todoItems", "tok", get=fake_get)

    assert len(documents) == 4
    assert calls == [None, "t1", "t2"]


def test_an_empty_collection_has_no_documents_key():
    class Response:
        def raise_for_status(self): pass
        def json(self): return {}

    assert list_documents("p", "s", "todoItems", "t", get=lambda *a, **k: Response()) == []


def test_fetch_reports_missing_configuration():
    with pytest.raises(RuntimeError, match="TODOAPP_KEY_FILE"):
        TodoAppSource(env={"TODOAPP_PROJECT_ID": "p", "TODOAPP_SPACE_ID": "s"}).fetch()


@pytest.mark.skipif(shutil.which("openssl") is None, reason="needs openssl")
def test_access_token_is_signed_requested_and_cached(tmp_path):
    pem = subprocess.run(["openssl", "genrsa", "2048"], capture_output=True, check=True, text=True).stdout
    key_file = tmp_path / "key.json"
    key_file.write_text(json.dumps({"client_email": "reader@example.iam", "private_key": pem}))
    auth._cache.clear()
    posted = []

    class Response:
        def raise_for_status(self): pass
        def json(self): return {"access_token": "abc", "expires_in": 3600}

    def fake_post(url, timeout, data):
        posted.append(data)
        return Response()

    clock = [1000.0]
    first = auth.get_access_token(str(key_file), post=fake_post, now=lambda: clock[0])
    second = auth.get_access_token(str(key_file), post=fake_post, now=lambda: clock[0] + 100)
    clock[0] += 3600
    auth.get_access_token(str(key_file), post=fake_post, now=lambda: clock[0])

    assert first == second == "abc"
    assert len(posted) == 2  # the second call hit the cache, the third was after expiry
    header, claims, signature = posted[0]["assertion"].split(".")
    pad = lambda s: s + "=" * (-len(s) % 4)
    assert json.loads(base64.urlsafe_b64decode(pad(claims)))["iss"] == "reader@example.iam"
    assert signature
