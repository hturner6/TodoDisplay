from dotenv import load_dotenv
import argparse
import os
import time
from datetime import datetime
import schedule
from models.task import Task
from taskDisplay.createTaskImage import DEFAULT_MARGINS, TaskDrawer, parse_margins
from taskDisplay.refreshPolicy import RefreshPolicy
from taskDisplay.preview import open_file, save_preview
from taskDisplay.previewTasks import SCENARIOS, fake_tasks
from taskFetcher.tickTick.projectTaskParser import parse_project_tasks
from taskFetcher.tickTick.tickTickClient import get_project_data
from screenDisplay.draw_bmp import display_image, clear_display

fontPath = "./src/screenDisplay/fonts/DejaVuSans-Bold.ttf"
policy = RefreshPolicy()

def margins():
    """Frame-safe margins, overridable with DISPLAY_MARGINS="top,right,bottom,left" (pixels)."""
    text = os.getenv("DISPLAY_MARGINS")
    return parse_margins(text) if text else DEFAULT_MARGINS

def task_run(refresh_interval_minutes):
    print(f"Running TodoDisplay every {refresh_interval_minutes} minutes")
    schedule.every(refresh_interval_minutes).minutes.do(task_image)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
    

def task_image():
    project_id = "687164e8fb06fe7e7a3d621a"
    now = datetime.now()
    try:
        tasks = parse_project_tasks(get_project_data(project_id))
        action = policy.on_success(tasks, now)
    except Exception as error:
        print(f"Could not fetch tasks: {type(error).__name__}")
        action = policy.on_failure(error, now)

    if action is None:
        print("Screen left as it is")
        return

    taskDrawer = TaskDrawer(fontPath, margins=margins())
    if action[0] == "tasks":
        image = taskDrawer.create_task_image(action[1], updated_at=action[2])
    else:
        image = taskDrawer.create_message_image(action[1], action[2], updated_at=action[3])
    display_image(image)

def task_test():
    project_id = "687164e8fb06fe7e7a3d621a"
    rawTasks = get_project_data(project_id)
    tasks = parse_project_tasks(rawTasks)
    taskDrawer = TaskDrawer(fontPath, margins=margins())
    image = taskDrawer.create_task_image(tasks)
    image.show()

def task_preview(path, fake=None, simulate_panel=True, open_after=True, safe_area=False):
    if fake:
        tasks = fake_tasks(fake)
    else:
        project_id = "687164e8fb06fe7e7a3d621a"
        tasks = parse_project_tasks(get_project_data(project_id))
    drawer = TaskDrawer(fontPath, margins=margins())
    image = drawer.create_task_image(tasks)
    save_preview(image, path, simulate_panel, safe_area=drawer.margins if safe_area else None)
    print(f"Preview saved to {path}")
    if open_after:
        open_file(path)

def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument('--task', action='store_true', help='Displays the task image on an epaper screen')
    parser.add_argument('--test', action='store_true', help='Displays the task image locally')
    parser.add_argument('--clear', action='store_true', help='Clears the display')
    parser.add_argument('--run', type=int, help='Runs the task display with a specified interval (in minutes)')
    parser.add_argument('--preview', nargs='?', const='previews/preview.png', metavar='PATH',
                        help='Saves the task image to a PNG (default previews/preview.png) without using the display')
    parser.add_argument('--fake', choices=sorted(SCENARIOS), help='With --preview, use sample tasks instead of fetching')
    parser.add_argument('--no-open', action='store_true', help='With --preview, do not open the PNG afterwards')
    parser.add_argument('--raw', action='store_true', help='With --preview, skip the black/white panel simulation')
    parser.add_argument('--safe-area', action='store_true', help='With --preview, outline the frame-safe area in red')
    args = parser.parse_args()

    if args.preview:
        task_preview(args.preview, fake=args.fake, simulate_panel=not args.raw, open_after=not args.no_open,
                     safe_area=args.safe_area)
    elif args.run:
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
