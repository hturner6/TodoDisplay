import argparse 
from screenDisplay.createImage import resize_image, convert_image_to_BMP
from screenDisplay.draw_bmp import display_bmp

def display_image(image_path):
    resize_image(image_path, "screenDisplay/img/Mockup_resized.png")
    convert_image_to_BMP("screenDisplay/img/Mockup_resized.png", "screenDisplay/img/Mockup_resized.bmp")
    display_bmp("screenDisplay/img/Mockup_resized.bmp")

def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument('--display', type=str, help='Display the mockup image')
    args = parser.parse_args()

    if args.display:
        picturePath = "screenDisplay/img/Mockup.png"
        display_image(picturePath)
    else:
        print("No valid argument provided. Use --image to create and display the mockup image.") 

if __name__ == "__main__":
    main()
