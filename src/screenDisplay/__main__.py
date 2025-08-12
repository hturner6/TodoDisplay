from screenDisplay.createImage import resize_image, convert_image_to_BMP
from screenDisplay.draw_bmp import display_bmp

def main():
    resize_image("screenDisplay/img/Mockup.png", "screenDisplay/img/Mockup_resized.jpg")
    convert_image_to_BMP("screenDisplay/img/Mockup_resized.jpg", "screenDisplay/img/Mockup_resized.bmp")
    display_bmp("screenDisplay/img/Mockup_resized.bmp")

if __name__ == "__main__":
    main()
