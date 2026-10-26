import os
import shlex
import subprocess
import sys
from PIL import Image
from screenDisplay.imageHelpers import resize_image, convert_image_to_BMP


def save_preview(image: Image.Image, path: str, simulate_panel: bool = True) -> None:
    """Writes the image to a PNG without touching the display or GPIO.

    With simulate_panel, the image goes through the same resize and 1-bit conversion that
    display_image applies, so the PNG shows what the panel will draw.
    """
    if simulate_panel:
        image = convert_image_to_BMP(resize_image(image))
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
