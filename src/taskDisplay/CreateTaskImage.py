from PIL import Image, ImageDraw
from models.task import Task

def create_task_image(tasks: list[Task] = None, width=648, height=480) -> Image:
    if tasks is None:
        tasks = []

    # Create a blank image
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Draw tasks on the image
    for i, task in enumerate(tasks):
        task_text = f"{task.title} - {task.due_date} - {task.category}"
        draw.text((10, 10 + i * 20), task_text, fill="black")

    # img.save("taskDisplay/img/task_image.png", "PNG")  # Save the image
    return img