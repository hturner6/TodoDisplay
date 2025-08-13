from PIL import Image
import logging
import time
from screenDisplay.displayInterfaces.waveshare_epd import epd5in83_V2

def display_bmp(picdir):
    epd = epd5in83_V2.EPD()
    logging.info("init and Clear")
    epd.init()

    logging.info("read bmp file on window")
    Himage = Image.open(picdir)
    epd.display(epd.getbuffer(Himage))
    time.sleep(2)
