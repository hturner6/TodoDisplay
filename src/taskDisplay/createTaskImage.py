from PIL import Image, ImageDraw, ImageFont
from models.task import Task

fontPath = "screenDisplay/fonts/BitterPro-Black.ttf"


def create_task_image(tasks: list[Task] = None, width=648, height=480) -> Image:
    if tasks is None:
        tasks = []

    # Create a blank image
    taskFont = ImageFont.truetype(fontPath, 24)
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Draw tasks on the image
    for i, task in enumerate(tasks):
        task_text = f"{task.title} - {task.due_date} - {task.category}"
        draw.text((10, 20 + i * 20), task_text, font=taskFont, fill="black")

    return img