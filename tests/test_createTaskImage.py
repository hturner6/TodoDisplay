import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskDisplay.createTaskImage import DEFAULT_MARGINS, Margins, TaskDrawer, parse_margins
from taskDisplay.previewTasks import SCENARIOS, fake_tasks

FONT = str(Path(__file__).resolve().parent.parent / "src/screenDisplay/fonts/DejaVuSans-Bold.ttf")


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


def test_a_stale_screen_says_so_in_the_footer():
    updated = datetime(2026, 10, 26, 9, 0)
    normal = TaskDrawer(FONT).create_task_image([], updated_at=updated)
    stale = TaskDrawer(FONT).create_task_image([], updated_at=updated, stale=True)

    footer = (normal.width // 2, normal.height - 60, normal.width, normal.height)

    def black_pixels(image):
        return sum(1 for value in image.crop(footer).get_flattened_data() if value == 0)

    assert black_pixels(stale) > black_pixels(normal)


def test_a_priority_task_has_a_heavy_asterisk_in_the_gutter_left_of_its_bullet():
    today = datetime(2026, 10, 26).date()
    left = DEFAULT_MARGINS.left

    def gutter_pixels(task):
        image = TaskDrawer(FONT).create_task_image([task], today=today)
        gutter = image.crop((left, 0, left + 22, image.height))
        return sum(1 for value in gutter.get_flattened_data() if value == 0)

    plain = gutter_pixels(Task("Pay rent", today))
    priority = gutter_pixels(Task("Pay rent", today, priority=True))

    # The first, small asterisk added 86 pixels; it was too faint on the real panel.
    assert priority - plain >= 130


def test_the_drawer_does_not_decide_staleness_from_the_clock():
    # An old update time alone is not stale: the refresh policy decides, and says so.
    old = datetime(2020, 1, 1)

    assert TaskDrawer(FONT).create_task_image([], updated_at=old).tobytes() != \
        TaskDrawer(FONT).create_task_image([], updated_at=old, stale=True).tobytes()
