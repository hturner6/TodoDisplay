"""Times the e-paper update on the Pi. Run from src/ with the service stopped:

    sudo systemctl stop TodoDisplay
    ../.venv/bin/python -m screenDisplay.benchmark            # CPU only, panel untouched
    ../.venv/bin/python -m screenDisplay.benchmark --panel    # also does one real refresh
    sudo systemctl start TodoDisplay
"""
import sys
import time
from pathlib import Path

from PIL import Image

from taskDisplay.createTaskImage import TaskDrawer
from taskDisplay.previewTasks import fake_tasks

WIDTH, HEIGHT = 648, 480
FONT = str(Path(__file__).resolve().parent / "fonts" / "DejaVuSans-Bold.ttf")


def old_getbuffer(image):
    """The per-pixel loop the driver used before, for comparison."""
    buf = [0xFF] * (WIDTH // 8 * HEIGHT)
    pixels = image.convert('1').load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if pixels[x, y] == 0:
                buf[int((x + y * WIDTH) / 8)] &= ~(0x80 >> (x % 8))
    return buf


def old_invert(buffer):
    inverted = [0x00] * len(buffer)
    for i in range(len(buffer)):
        inverted[i] = ~buffer[i]
    return inverted


def timed(label, function, *args):
    start = time.perf_counter()
    result = function(*args)
    print(f"{label:<28}{time.perf_counter() - start:8.3f} s", flush=True)
    return result


def main():
    image = TaskDrawer(FONT).create_task_image(fake_tasks("many")).convert("1")

    print("-- CPU only --")
    timed("draw image", TaskDrawer(FONT).create_task_image, fake_tasks("many"))
    old = timed("old getbuffer", old_getbuffer, image)
    timed("old invert", old_invert, old)
    new = timed("new getbuffer", lambda i: list(i.convert('1').tobytes()), image)
    timed("new invert", lambda b: [byte ^ 0xFF for byte in b], new)
    print("buffers match:", old == new)

    if "--panel" not in sys.argv:
        return

    from screenDisplay.displayInterfaces.waveshare_epd import epd5in83_V2
    print("-- Real refresh (the screen will flash) --")
    total = time.perf_counter()
    epd = epd5in83_V2.EPD()
    timed("init", epd.init)
    buffer = timed("getbuffer", epd.getbuffer, image)
    timed("display (send + refresh)", epd.display, buffer)
    timed("sleep", epd.sleep)
    print(f"{'total':<28}{time.perf_counter() - total:8.3f} s")


if __name__ == "__main__":
    main()
