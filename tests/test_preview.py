import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from taskDisplay.createTaskImage import TaskDrawer
from taskDisplay.preview import save_preview
from taskDisplay.previewTasks import SCENARIOS, fake_tasks

FONT = str(Path(__file__).resolve().parent.parent / "src/screenDisplay/fonts/Inter-Bold.ttf")


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_panel_preview_is_a_one_bit_panel_sized_png(scenario, tmp_path):
    image = TaskDrawer(FONT).create_task_image(fake_tasks(scenario))
    out = tmp_path / "preview.png"

    save_preview(image, str(out))

    saved = Image.open(out)
    assert saved.size == (648, 480)
    assert saved.mode == "1"


def test_raw_preview_keeps_the_greyscale_image(tmp_path):
    image = TaskDrawer(FONT).create_task_image(fake_tasks("few"))
    out = tmp_path / "raw.png"

    save_preview(image, str(out), simulate_panel=False)

    assert Image.open(out).mode == "L"
