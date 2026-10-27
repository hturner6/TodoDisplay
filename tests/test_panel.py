import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from screenDisplay import draw_bmp
from screenDisplay.draw_bmp import FULL_CLEAR_EVERY, EPaperPanel

START = datetime(2026, 10, 26, 12, 0)


class FakeEpd:
    """Stands in for the driver, recording what the panel was asked to do."""
    calls = []
    fail_display = False

    def init(self):
        self.calls.append("init")

    def Clear(self):
        self.calls.append("clear")

    def getbuffer(self, image):
        return image

    def display(self, buffer):
        if self.fail_display:
            raise OSError("display failed")
        self.calls.append("display")

    def sleep(self):
        self.calls.append("sleep")


@pytest.fixture
def clock(monkeypatch):
    FakeEpd.calls = []
    FakeEpd.fail_display = False
    monkeypatch.setattr(draw_bmp.epd5in83_V2, "EPD", FakeEpd)
    now = [START]

    class Clock:
        @staticmethod
        def now():
            return now[0]

    monkeypatch.setattr(draw_bmp, "datetime", Clock)
    return now


IMAGE = Image.new("L", (648, 480), 255)


def test_showing_an_image_draws_it_and_powers_the_panel_down(clock):
    EPaperPanel().show(IMAGE)

    assert FakeEpd.calls == ["init", "display", "sleep"]


def test_the_panel_is_powered_down_even_if_drawing_fails(clock):
    FakeEpd.fail_display = True

    with pytest.raises(OSError):
        EPaperPanel().show(IMAGE)

    assert FakeEpd.calls[-1] == "sleep"


def test_the_panel_is_wiped_once_a_day_not_on_every_show(clock):
    panel = EPaperPanel()
    panel.show(IMAGE)
    clock[0] = START + FULL_CLEAR_EVERY - timedelta(minutes=1)
    panel.show(IMAGE)
    assert "clear" not in FakeEpd.calls

    clock[0] = START + FULL_CLEAR_EVERY
    panel.show(IMAGE)
    assert FakeEpd.calls.count("clear") == 1

    clock[0] = START + FULL_CLEAR_EVERY + timedelta(hours=1)
    panel.show(IMAGE)
    assert FakeEpd.calls.count("clear") == 1


def test_each_panel_keeps_its_own_clear_timer(clock):
    EPaperPanel().show(IMAGE)
    clock[0] = START + FULL_CLEAR_EVERY

    EPaperPanel().show(IMAGE)

    assert "clear" not in FakeEpd.calls


def test_clearing_wipes_the_panel(clock, monkeypatch):
    monkeypatch.setattr(draw_bmp.time, "sleep", lambda seconds: None)

    EPaperPanel().clear()

    assert FakeEpd.calls == ["init", "clear"]
