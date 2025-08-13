from PIL import Image, ImageDraw, ImageFont

width = 648
height = 480

def resize_image(image: Image):
    """
    Resize the image to fit the 648x480 resolution.
    """
    return image.resize((width, height))

def convert_image_to_BMP(image: Image):
    """
    Convert the image to BMP format.
    """
    return image.convert("1")  # Convert to 1-bit pixels, black and white