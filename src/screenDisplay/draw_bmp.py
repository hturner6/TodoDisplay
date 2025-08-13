from PIL import Image
import logging
import time
from screenDisplay.displayInterfaces.waveshare_epd import epd5in83_V2
from screenDisplay.imageHelpers import resize_image, convert_image_to_BMP

def display_bmp(picdir):
    epd = epd5in83_V2.EPD()
    logging.info("init and Clear")
    epd.init()

    logging.info("read bmp file on window")
    Himage = Image.open(picdir)
    epd.display(epd.getbuffer(Himage))
    time.sleep(2)

def display_image(image: Image):
    image = resize_image(image, width=648, height=480)
    image = convert_image_to_BMP(image)
    epd = epd5in83_V2.EPD()
    logging.info("init and Clear")
    epd.init()

    logging.info("display image")
    epd.display(epd.getbuffer(image))
    time.sleep(2)
