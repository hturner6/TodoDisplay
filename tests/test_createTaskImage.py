import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PIL import ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskDisplay.createTaskImage import DEFAULT_MARGINS, Margins, TaskDrawer, parse_margins
from taskFetcher.weather import Weather
from taskDisplay.previewTasks import SCENARIOS, fake_tasks

FONT = str(Path(__file__).resolve().parent.parent / "src/screenDisplay/fonts/Inter-Bold.ttf")
BANNER_FONT = str(Path(__file__).resolve().parent.parent / "src/screenDisplay/fonts/Newsreader-SemiBoldItalic.ttf")


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


def test_no_date_heading_overhangs_the_left_margin():
    # The italic banner's capitals lean out past their origin: every weekday and month must still stay in.
    margins = DEFAULT_MARGINS
    drawer = TaskDrawer(FONT, banner_font_path=BANNER_FONT)

    for offset in range(0, 366, 2):
        image = drawer.create_task_image([], today=datetime(2026, 1, 1).date() + timedelta(days=offset))
        assert image.point(lambda value: 255 - value).getbbox()[0] >= margins.left


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


def test_a_stale_screen_names_the_cause_in_the_footer():
    updated = datetime(2026, 10, 26, 9, 0)
    expired = TaskDrawer(FONT).create_task_image([], updated_at=updated, stale=True, reason="Sign-in expired")
    offline = TaskDrawer(FONT).create_task_image([], updated_at=updated, stale=True, reason="No network")
    plain = TaskDrawer(FONT).create_task_image([], updated_at=updated, stale=True)

    assert len({expired.tobytes(), offline.tobytes(), plain.tobytes()}) == 3


def test_a_stale_footer_with_a_cause_stays_inside_the_margins():
    margins = DEFAULT_MARGINS
    image = TaskDrawer(FONT).create_task_image(
        [], updated_at=datetime(2026, 10, 26, 9, 0), stale=True, reason="Cannot reach TodoApp")

    left, _, right, _ = image.point(lambda value: 255 - value).getbbox()
    assert left >= margins.left and right <= image.width - margins.right


def test_the_drawer_does_not_decide_staleness_from_the_clock():
    # An old update time alone is not stale: the refresh policy decides, and says so.
    old = datetime(2020, 1, 1)

    assert TaskDrawer(FONT).create_task_image([], updated_at=old).tobytes() != \
        TaskDrawer(FONT).create_task_image([], updated_at=old, stale=True).tobytes()


# --- weather ---------------------------------------------------------------------------------------

CONDITIONS = ["clear", "partly", "cloud", "fog", "rain", "snow", "storm"]


def header_pixels(image):
    """The header band (date heading and weather), where nothing else is drawn."""
    return image.crop((0, 0, image.width, 80)).tobytes()


@pytest.mark.parametrize("two_columns", [True, False])
def test_weather_appears_in_the_header_and_nowhere_else(two_columns):
    drawer = TaskDrawer(FONT, two_columns=two_columns)
    plain = drawer.create_task_image(fake_tasks("few"))
    with_weather = drawer.create_task_image(fake_tasks("few"), weather=Weather(12, "rain"))

    assert header_pixels(plain) != header_pixels(with_weather)
    below = (0, 80, plain.width, plain.height)
    assert plain.crop(below).tobytes() == with_weather.crop(below).tobytes()


def test_each_condition_has_its_own_glyph():
    drawer = TaskDrawer(FONT)
    images = {c: header_pixels(drawer.create_task_image([], weather=Weather(12, c))) for c in CONDITIONS}

    assert len(set(images.values())) == len(CONDITIONS)


def test_the_temperature_is_drawn():
    drawer = TaskDrawer(FONT)

    assert header_pixels(drawer.create_task_image([], weather=Weather(12, "clear"))) != \
        header_pixels(drawer.create_task_image([], weather=Weather(-3, "clear")))


@pytest.mark.parametrize("weather", [Weather(-12, "storm"), Weather(38, "partly")])
def test_the_widest_weather_stays_inside_the_margins_and_clear_of_the_date(weather):
    margins = DEFAULT_MARGINS
    drawer = TaskDrawer(FONT, margins=margins)
    today = datetime(2026, 9, 30).date()  # Wednesday 30 September: a long date heading

    image = drawer.create_task_image([], today=today, weather=weather)
    without = drawer.create_task_image([], today=today)

    assert image.point(lambda value: 255 - value).getbbox()[2] <= image.width - margins.right
    band = (0, 0, image.width, 70)
    date_right = without.crop(band).point(lambda value: 255 - value).getbbox()[2]
    added = ImageChops.difference(image.crop(band), without.crop(band)).getbbox()
    assert added[0] > date_right
