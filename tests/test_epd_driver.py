import sys
import types
from pathlib import Path
from PIL import Image, ImageDraw

# The real epdconfig needs Pi hardware libraries, so the driver is imported against a stub.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
stub = types.ModuleType("screenDisplay.displayInterfaces.waveshare_epd.epdconfig")
for name in ("RST_PIN", "DC_PIN", "BUSY_PIN", "CS_PIN"):
    setattr(stub, name, 0)
sys.modules.setdefault("screenDisplay.displayInterfaces.waveshare_epd.epdconfig", stub)
from screenDisplay.displayInterfaces.waveshare_epd import epd5in83_V2  # noqa: E402

WIDTH, HEIGHT = 648, 480


def reference_buffer(image):
    """The per-pixel version the driver used before: a cleared bit for every black pixel."""
    buf = [0xFF] * (WIDTH // 8 * HEIGHT)
    pixels = image.convert('1').load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if pixels[x, y] == 0:
                buf[(x + y * WIDTH) // 8] &= ~(0x80 >> (x % 8))
    return buf


def sample_image():
    img = Image.new('L', (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(img)
    draw.rectangle((3, 5, 200, 90), fill=0)
    draw.line((0, 0, WIDTH - 1, HEIGHT - 1), fill=0, width=3)
    draw.ellipse((300, 200, 340, 260), fill=0)
    return img


def test_getbuffer_matches_the_per_pixel_version():
    image = sample_image()
    assert epd5in83_V2.EPD().getbuffer(image) == reference_buffer(image)


def test_getbuffer_rotates_a_horizontal_image_like_before():
    portrait = sample_image().transpose(Image.ROTATE_270)  # HEIGHT x WIDTH
    assert portrait.size == (HEIGHT, WIDTH)
    assert epd5in83_V2.EPD().getbuffer(portrait) == reference_buffer(sample_image())


def test_display_sends_inverted_bytes():
    sent = []
    epd = epd5in83_V2.EPD()
    epd.send_command = lambda command: sent.append(("cmd", command))
    epd.send_data2 = lambda data: sent.append(("data", list(data)))
    epd.TurnOnDisplay = lambda: sent.append(("refresh",))
    epd.display([0xFF, 0x0F] + [0x00] * (WIDTH * HEIGHT // 8 - 2))
    assert sent[0] == ("cmd", 0x10) and set(sent[1][1]) == {0}
    assert sent[2] == ("cmd", 0x13) and sent[3][1][:3] == [0x00, 0xF0, 0xFF]
    assert sent[4] == ("refresh",)
