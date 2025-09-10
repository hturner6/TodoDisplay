from dotenv import load_dotenv
import argparse
import time
import schedule
from models.task import Task
from taskDisplay.createTaskImage import TaskDrawer
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks
from taskFetcher.tickTick.tickTickClient import get_project_data
from screenDisplay.draw_bmp import display_image, clear_display

fontPath = "screenDisplay/fonts/Verdana.ttf"

def task_run(refresh_interval_minutes):
    print(f"Running TodoDisplay every {refresh_interval_minutes} minutes")
    schedule.every(refresh_interval_minutes).minutes.do(task_image)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
    

def task_image():
    project_id = "687164e8fb06fe7e7a3d621a"
    rawTasks = get_project_data(project_id)
    tasks = parse_project_tasks(rawTasks)
    taskDrawer = TaskDrawer(fontPath)
    image = taskDrawer.create_task_image(tasks)
    # image.show()
    display_image(image)

def task_test():
    project_id = "687164e8fb06fe7e7a3d621a"
    rawTasks = get_project_data(project_id)
    tasks = parse_project_tasks(rawTasks)
    taskDrawer = TaskDrawer(fontPath)
    image = taskDrawer.create_task_image(tasks)
    image.show()

def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument('--task', action='store_true', help='Displays the task image on an epaper screen')
    parser.add_argument('--test', action='store_true', help='Displays the task image locally')
    parser.add_argument('--clear', action='store_true', help='Clears the display')
    parser.add_argument('--run', type=int, help='Runs the task display with a specified interval (in minutes)')
    args = parser.parse_args()

    if args.run:
        task_run(args.run)
    elif args.task:
        task_image()
    elif args.clear:
        clear_display()
    elif args.test:
        task_test()
    else:
        print("No valid argument provided. Use --image to create and display the mockup image.")

if __name__ == "__main__":
    main()
