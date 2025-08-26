from PIL import Image, ImageDraw, ImageFont
from models.task import Task

fontPath = "screenDisplay/fonts/BitterPro-Regular.ttf"


def create_task_image(tasks: list[Task] = None, width=648, height=480) -> Image:
    if tasks is None:
        tasks = []

    sortedTasks = sorted(tasks, key=lambda x: (x.due_date is None, x.due_date))
    (groupA, groupB) = split_task_groups(sortedTasks)
    # Create a blank image
    titleFont = ImageFont.truetype(fontPath, 24)
    taskFont = ImageFont.truetype(fontPath, 20)
    img = Image.new('L', (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Draw tasks on the image
    draw.text((10, 20), "Todays Tasks:", font=titleFont, fill="black")
    for i, task in enumerate(groupA):
        task_text = task.__str__()
        draw.text((10, 50 + i * 30), task_text, font=taskFont, fill="black")

    # Draw tasks on the image
    if groupB:
        heightToDraw = 400
        for i, task in enumerate(reversed(groupB)):
            task_text = task.__str__()
            draw.text((10, heightToDraw), task_text, font=taskFont, fill="black")
            heightToDraw = heightToDraw - 30
        draw.text((10, heightToDraw), "General Tasks:", font=titleFont, fill="black")

    return img

def split_task_groups(tasks: list[Task]) -> (list[Task], list[Task]):
    if tasks is None:
        return ([], [])

    groupA, groupB = [], []
    for task in tasks:
        groupA.append(task) if task.is_today_or_overdue() else groupB.append(task)

    return (groupA, groupB)
