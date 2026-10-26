import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from PIL import ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskDisplay.createTaskImage import DEFAULT_MARGINS, Margins, TaskDrawer, parse_margins, wrap_text
from taskDisplay.previewTasks import SCENARIOS, fake_tasks
from taskDisplay.refreshPolicy import REDRAW_AFTER, STALE_AFTER, RefreshPolicy, describe_error

FONT = str(Path(__file__).resolve().parent.parent / "src/screenDisplay/fonts/DejaVuSans-Bold.ttf")
NOW = datetime(2026, 10, 26, 12, 0)


@pytest.fixture
def font():
    return ImageFont.truetype(FONT, 27)


def test_short_text_stays_on_one_line(font):
    assert wrap_text(font, "Buy milk", [400], 2) == ["Buy milk"]


def test_long_text_wraps_on_word_boundaries(font):
    lines = wrap_text(font, "Book the practical driving test", [250, 400], 2)

    assert len(lines) == 2
    assert " ".join(lines) == "Book the practical driving test"
    assert all(font.getlength(line) <= 400 for line in lines)


def test_text_cut_after_the_last_line_ends_with_an_ellipsis(font):
    lines = wrap_text(font, "word " * 40, [300], 2)

    assert len(lines) == 2
    assert lines[-1].endswith("…")
    assert all(font.getlength(line) <= 300 for line in lines)


def test_a_word_wider_than_the_line_is_broken(font):
    lines = wrap_text(font, "x" * 80, [200], 3)

    assert all(font.getlength(line) <= 200 for line in lines)
    assert lines[-1].endswith("…")


def test_first_line_can_be_narrower_than_the_rest(font):
    lines = wrap_text(font, "alpha beta gamma delta epsilon", [100, 600], 2)

    assert font.getlength(lines[0]) <= 100
    assert " ".join(lines) == "alpha beta gamma delta epsilon"


def test_parse_margins_reads_top_right_bottom_left():
    assert parse_margins("1,2,3,4") == Margins(top=1, right=2, bottom=3, left=4)


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_every_scenario_draws_only_black_and_white(scenario):
    image = TaskDrawer(FONT).create_task_image(fake_tasks(scenario))

    assert set(image.get_flattened_data()) <= {0, 255}


def test_nothing_is_drawn_inside_the_margins():
    margins = Margins(top=40, right=50, bottom=60, left=70)
    drawer = TaskDrawer(FONT, margins=margins)

    image = drawer.create_task_image(fake_tasks("many"))

    left, top, right, bottom = image.point(lambda value: 255 - value).getbbox()
    assert left >= margins.left
    assert top >= margins.top
    assert right <= image.width - margins.right
    assert bottom <= image.height - margins.bottom


def test_overflowing_tasks_are_counted_not_dropped_silently(monkeypatch):
    drawn = []
    monkeypatch.setattr(ImageDraw.ImageDraw, "text", lambda self, position, text, **kwargs: drawn.append(text))

    TaskDrawer(FONT).create_task_image(fake_tasks("many"))

    assert any(text.startswith("+") and text.endswith("more") for text in drawn)


def test_open_tasks_sort_before_done_ones():
    today = datetime.now().date()
    tasks = [Task("done", today, status=Task.DONE), Task("open", today)]
    drawn = []
    drawer = TaskDrawer(FONT)
    drawer._draw_row = lambda task, *args: drawn.append(task.title)

    drawer.create_task_image(tasks)

    assert drawn == ["open", "done"]


def test_hide_done_leaves_only_open_tasks():
    today = datetime.now().date()
    tasks = [Task("done", today, status=Task.DONE), Task("open", today)]
    drawn = []
    drawer = TaskDrawer(FONT, hide_done=True)
    drawer._draw_row = lambda task, *args: drawn.append(task.title)

    drawer.create_task_image(tasks)

    assert drawn == ["open"]


@pytest.mark.parametrize("tasks, expected", [
    ([], "Nothing planned"),
    ([Task("later", datetime.now().date() + timedelta(days=3))], "All done"),
    ([Task("finished", datetime.now().date(), status=Task.DONE)], "All done"),
])
def test_empty_states_pick_the_right_message(tasks, expected):
    drawn = []
    drawer = TaskDrawer(FONT)
    drawer._draw_message = lambda heading, *args: drawn.append(heading)

    drawer.create_task_image(tasks)

    assert drawn == [expected]


def test_short_due_label():
    today = datetime.now().date()

    assert Task("a", None).short_due_label() == ""
    assert Task("a", today).short_due_label() == "Today"
    assert Task("a", today - timedelta(days=3)).short_due_label() == "3d overdue"


# --- refresh policy -------------------------------------------------------------------------

def test_first_success_draws():
    assert RefreshPolicy().on_success([Task("a", NOW.date())], NOW)[0] == "tasks"


def test_unchanged_tasks_are_not_redrawn_until_the_redraw_interval():
    policy = RefreshPolicy()
    tasks = [Task("a", NOW.date())]
    policy.on_success(tasks, NOW)

    assert policy.on_success(list(tasks), NOW + timedelta(minutes=30)) is None
    assert policy.on_success(list(tasks), NOW + REDRAW_AFTER)[0] == "tasks"


def test_changed_tasks_are_redrawn_straight_away():
    policy = RefreshPolicy()
    policy.on_success([Task("a", NOW.date())], NOW)

    assert policy.on_success([Task("b", NOW.date())], NOW + timedelta(minutes=30))[0] == "tasks"


def test_failure_with_nothing_drawn_yet_shows_an_error_once():
    policy = RefreshPolicy()

    first = policy.on_failure(OSError("no network"), NOW)
    again = policy.on_failure(OSError("no network"), NOW + timedelta(minutes=30))

    assert first == ("message", "Cannot reach TickTick", "Will keep trying", None)
    assert again is None


def test_expired_token_is_named_on_screen():
    class Response:
        status_code = 401

    class Unauthorized(Exception):
        response = Response()

    assert describe_error(Unauthorized("secret detail"))[0] == "Sign-in expired"
    assert "secret detail" not in " ".join(describe_error(Unauthorized("secret detail")))


def test_failure_keeps_the_screen_until_the_data_is_stale_then_marks_it_once():
    policy = RefreshPolicy()
    tasks = [Task("a", NOW.date())]
    policy.on_success(tasks, NOW)

    assert policy.on_failure(OSError(), NOW + timedelta(hours=1)) is None
    stale = policy.on_failure(OSError(), NOW + STALE_AFTER + timedelta(minutes=1))
    assert stale == ("tasks", tasks, NOW)
    assert policy.on_failure(OSError(), NOW + timedelta(hours=3)) is None


def test_recovery_after_a_stale_screen_redraws():
    policy = RefreshPolicy()
    tasks = [Task("a", NOW.date())]
    policy.on_success(tasks, NOW)
    policy.on_failure(OSError(), NOW + timedelta(hours=3))

    assert policy.on_success(tasks, NOW + timedelta(hours=4))[0] == "tasks"
