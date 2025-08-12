from PIL import Image

width = 648
height = 480

def resize_image(image_path, output_path):
    """
    Resize the image to fit the 648x480 resolution.
    """
    with Image.open(image_path) as img:
        img = img.resize((width, height))
        img.save(output_path, "PNG")

def convert_image_to_BMP(image_path, output_path):
    """
    Convert the image to BMP format.
    """
    with Image.open(image_path) as img:
        img = img.convert("1")  # Convert to 1-bit pixels, black and white
        img.save(output_path, "BMP")