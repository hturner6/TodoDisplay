import sys
from datetime import datetime, time, timedelta
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskDisplay.createTaskImage import Margins, TaskDrawer, parse_margins
from taskDisplay.previewTasks import SCENARIOS, fake_tasks
from taskDisplay.refreshPolicy import REDRAW_AFTER, STALE_AFTER, RefreshPolicy
from taskFetcher.tickTick.tickTickSource import TickTickSource

FONT = str(Path(__file__).resolve().parent.parent / "src/screenDisplay/fonts/DejaVuSans-Bold.ttf")
NOW = datetime(2026, 10, 26, 12, 0)
SOURCE = TickTickSource(env={})


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


# --- refresh policy -------------------------------------------------------------------------

def test_first_success_draws():
    assert RefreshPolicy(SOURCE).on_success([Task("a", NOW.date())], NOW)[0] == "tasks"


def test_unchanged_tasks_are_not_redrawn_until_the_redraw_interval():
    policy = RefreshPolicy(SOURCE)
    tasks = [Task("a", NOW.date())]
    policy.on_success(tasks, NOW)

    assert policy.on_success(list(tasks), NOW + timedelta(minutes=30)) is None
    assert policy.on_success(list(tasks), NOW + REDRAW_AFTER)[0] == "tasks"


def test_changed_tasks_are_redrawn_straight_away():
    policy = RefreshPolicy(SOURCE)
    policy.on_success([Task("a", NOW.date())], NOW)

    assert policy.on_success([Task("b", NOW.date())], NOW + timedelta(minutes=30))[0] == "tasks"


def test_a_change_to_a_task_that_is_not_on_the_screen_does_not_redraw():
    policy = RefreshPolicy(SOURCE)
    far_off = NOW.date() + timedelta(days=30)
    policy.on_success([Task("a", NOW.date()), Task("next month", far_off)], NOW)

    assert policy.on_success([Task("a", NOW.date()), Task("renamed", far_off, priority=True)],
                             NOW + timedelta(minutes=30)) is None


def test_failure_with_nothing_drawn_yet_shows_an_error_once():
    policy = RefreshPolicy(SOURCE)

    first = policy.on_failure(OSError("no network"), NOW)
    again = policy.on_failure(OSError("no network"), NOW + timedelta(minutes=30))

    assert first == ("message", "Cannot reach TickTick", "Will keep trying", None)
    assert again is None


def test_failure_keeps_the_screen_until_the_data_is_stale_then_marks_it_once():
    policy = RefreshPolicy(SOURCE)
    tasks = [Task("a", NOW.date())]
    policy.on_success(tasks, NOW)

    assert policy.on_failure(OSError(), NOW + timedelta(hours=1)) is None
    stale = policy.on_failure(OSError(), NOW + STALE_AFTER + timedelta(minutes=1))
    assert stale == ("tasks", tasks, NOW, True)
    assert policy.on_failure(OSError(), NOW + timedelta(hours=3)) is None


def test_recovery_after_a_stale_screen_redraws():
    policy = RefreshPolicy(SOURCE)
    tasks = [Task("a", NOW.date())]
    policy.on_success(tasks, NOW)
    policy.on_failure(OSError(), NOW + timedelta(hours=3))

    assert policy.on_success(tasks, NOW + timedelta(hours=4))[0] == "tasks"


def test_a_task_changing_state_redraws_the_screen():
    today = datetime.now().date()
    now = datetime(2026, 10, 27, 12, 0)
    policy = RefreshPolicy(SOURCE)
    policy.on_success([Task("a", today)], now)

    assert policy.on_success([Task("a", today, status=Task.DONE)], now + timedelta(minutes=30)) is not None


def test_a_change_of_time_or_week_redraws_the_screen():
    today = datetime.now().date()
    now = datetime(2026, 10, 27, 12, 0)
    policy = RefreshPolicy(SOURCE)
    policy.on_success([Task("a", today)], now)

    assert policy.on_success([Task("a", today, scheduled_time=time(9, 0))], now) is not None
    assert policy.on_success([Task("a", today, scheduled_time=time(9, 0), weekly=True)], now) is not None
    assert policy.on_success([Task("a", today, scheduled_time=time(9, 0), weekly=True)], now) is None


def test_a_stale_screen_says_so_in_the_footer():
    updated = datetime(2026, 10, 26, 9, 0)
    normal = TaskDrawer(FONT).create_task_image([], updated_at=updated)
    stale = TaskDrawer(FONT).create_task_image([], updated_at=updated, stale=True)

    footer = (normal.width // 2, normal.height - 60, normal.width, normal.height)

    def black_pixels(image):
        return sum(1 for value in image.crop(footer).get_flattened_data() if value == 0)

    assert black_pixels(stale) > black_pixels(normal)


def test_the_drawer_does_not_decide_staleness_from_the_clock():
    # An old update time alone is not stale: the refresh policy decides, and says so.
    old = datetime(2020, 1, 1)

    assert TaskDrawer(FONT).create_task_image([], updated_at=old).tobytes() != \
        TaskDrawer(FONT).create_task_image([], updated_at=old, stale=True).tobytes()
