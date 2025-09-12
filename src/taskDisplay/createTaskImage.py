from PIL import Image, ImageDraw, ImageFont
from models.task import Task


class TaskDrawer():
    def __init__(self, fontPath, width=648, height=480):
        # Create a blank image
        self.width = width
        self.height = height
        self.img = Image.new('L', (self.width, self.height), color="white")
        self.draw = ImageDraw.Draw(self.img)
        self.heightOffset = 20

        self.titleFont = ImageFont.truetype(fontPath, 24)
        self.taskFont = ImageFont.truetype(fontPath, 20)

    def create_task_image(self, tasks: list[Task] = None) -> Image:
        if tasks is None:
            tasks = []

        dailyTasks = list(filter(Task.is_today_or_overdue, tasks))
        if len(dailyTasks) == 0:
            self.draw_all_completed("Todays Tasks:", titlePosition=self.heightOffset)
        else:
            sortedTasks = sorted(dailyTasks, key=lambda x: (x.due_date is None, x.due_date))
            # Draw tasks on the image
            self.draw_group("Todays Tasks:", titlePosition=self.heightOffset, tasks=sortedTasks)

        return self.img

    # TODO: add image bounding and group bounding
    def draw_group(self, title: str, titlePosition: int, tasks: list[Task]):
        self.draw.text((10, titlePosition), title, font=self.titleFont, fill="black")
        for i, task in enumerate(tasks):
            task_text = task.__str__()
            self.draw.text((10, titlePosition + (i+1) * 30), task_text, font=self.taskFont, fill="black")

    def draw_all_completed(self, title: str, titlePosition: int):
        self.draw.text((10, titlePosition), title, font=self.titleFont, fill="black")
        self.draw.text((10, titlePosition + 30), "* All tasks completed", font=self.taskFont, fill="black")

    def split_task_groups(tasks: list[Task]) -> (list[Task], list[Task]):
        if tasks is None:
            return ([], [])

        groupA, groupB = [], []
        for task in tasks:
            groupA.append(task) if task.is_today_or_overdue() else groupB.append(task)

        return (groupA, groupB)


