from dotenv import load_dotenv
import argparse
from models.task import Task
from taskDisplay.createTaskImage import create_task_image
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks
from taskFetcher.tickTick.tickTickClient import get_project_data
from screenDisplay.draw_bmp import display_image, clear_display

def task_image():
    project_id = "687164e8fb06fe7e7a3d621a"
    rawTasks = get_project_data(project_id)
    tasks = parse_project_tasks(rawTasks)
    image = create_task_image(tasks)
    # image.show()
    display_image(image)

def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument('--task', action='store_true', help='Displays the task image')
    parser.add_argument('--clear', action='store_true', help='Clears the display')
    args = parser.parse_args()

    if args.task:
        task_image()
    elif args.clear:
        clear_display()
    else:
        print("No valid argument provided. Use --image to create and display the mockup image.") 

if __name__ == "__main__":
    main()
