import asyncio
from dotenv import load_dotenv
from models.task import Task
from taskDisplay.createTaskImage import create_task_image
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks
from taskFetcher.tickTick.tickTickClient import get_project_data
from screenDisplay.imageHelpers import resize_image, convert_image_to_BMP
from screenDisplay.draw_bmp import display_image

def main():
    project_id = "687164e8fb06fe7e7a3d621a"
    rawTasks = get_project_data(project_id)
    tasks = parse_project_tasks(rawTasks)
    print(tasks)
    image = create_task_image(tasks)
    # image.show()
    image = resize_image(image)
    image = convert_image_to_BMP(image)
    display_image(image)

if __name__ == "__main__":
    main()