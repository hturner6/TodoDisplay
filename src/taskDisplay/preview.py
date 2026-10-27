import os
import shlex
import subprocess
import sys
from PIL import Image, ImageDraw
from screenDisplay.imageHelpers import resize_image, convert_image_to_BMP


def save_preview(image: Image.Image, path: str, simulate_panel: bool = True, safe_area=None) -> None:
    """Writes the image to a PNG without touching the display or GPIO.

    With simulate_panel, the image goes through the same resize and 1-bit conversion that
    EPaperPanel.show applies, so the PNG shows what the panel will draw. With safe_area (Margins), a red
    rectangle marks the area the picture frame leaves visible.
    """
    if simulate_panel:
        image = convert_image_to_BMP(resize_image(image))
    if safe_area:
        image = image.convert("RGB")
        width, height = image.size
        ImageDraw.Draw(image).rectangle(
            (safe_area.left, safe_area.top, width - safe_area.right - 1, height - safe_area.bottom - 1),
            outline=(255, 0, 0))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    image.save(path)


def open_file(path: str) -> None:
    """Opens the file in the viewer named by $PREVIEW_VIEWER, else the machine's default viewer."""
    viewer = os.environ.get("PREVIEW_VIEWER")
    if viewer:
        command = shlex.split(viewer) + [path]
    elif sys.platform.startswith("win"):
        os.startfile(path)
        return
    else:
        command = ["open" if sys.platform == "darwin" else "xdg-open", path]
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
