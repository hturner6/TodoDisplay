from PIL import Image
from screenDisplay.imageHelpers import resize_image, convert_image_to_BMP


def save_preview(image: Image.Image, path: str, simulate_panel: bool = True) -> None:
    """Writes the image to a PNG without touching the display or GPIO.

    With simulate_panel, the image goes through the same resize and 1-bit conversion that
    display_image applies, so the PNG shows what the panel will draw.
    """
    if simulate_panel:
        image = convert_image_to_BMP(resize_image(image))
    image.save(path)
