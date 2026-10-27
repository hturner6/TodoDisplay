from PIL import Image
import logging
import time
from datetime import datetime, timedelta
from screenDisplay.displayInterfaces.waveshare_epd import epd5in83_V2
from screenDisplay.imageHelpers import resize_image, convert_image_to_BMP

# The panel is wiped to white this often by a long-running process, to clear any ghosting.
# The driver has no partial refresh, so every update is already a full refresh.
FULL_CLEAR_EVERY = timedelta(hours=24)
_last_full_clear = None

def display_bmp(picdir):
    epd = epd5in83_V2.EPD()
    logging.info("init and Clear")
    epd.init()

    logging.info("read bmp file on window")
    Himage = Image.open(picdir)
    epd.display(epd.getbuffer(Himage))
    time.sleep(2)

def display_image(image: Image):
    image = resize_image(image)
    image = convert_image_to_BMP(image)
    epd = epd5in83_V2.EPD()
    logging.info("init and Clear")
    epd.init()
    try:
        global _last_full_clear
        now = datetime.now()
        if _last_full_clear is None:
            _last_full_clear = now
        elif now - _last_full_clear >= FULL_CLEAR_EVERY:
            logging.info("periodic full clear")
            epd.Clear()
            _last_full_clear = now

        logging.info("display image")
        epd.display(epd.getbuffer(image))
    finally:
        # Always power the panel down and release SPI/GPIO, even if drawing failed; the next
        # display_image calls init() again. display() already waits for the panel to finish.
        epd.sleep()

def clear_display():
    epd = epd5in83_V2.EPD()
    logging.info("init and Clear")
    epd.init()
    epd.Clear()
    time.sleep(2)
    logging.info("Display cleared")
