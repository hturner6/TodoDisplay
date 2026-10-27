from dotenv import load_dotenv
import argparse
from datetime import datetime, timedelta
import os
from pathlib import Path
import time
import schedule
from taskDisplay.createTaskImage import DEFAULT_MARGINS, TaskDrawer, parse_margins
from taskDisplay.quietHours import QuietHours
from taskDisplay.refresh import DrawTasks, Refresher
from taskDisplay.preview import open_file, save_preview
from taskDisplay.previewTasks import SCENARIOS, FakeSource
from taskFetcher.envFiles import permission_warnings
from taskFetcher.sources import SOURCES, DEFAULT_SOURCE, resolve_source
from screenDisplay.draw_bmp import EPaperPanel

# Inter for the text, with Newsreader italic for the date banner alone, as in the TodoApp.
fontPath = "./src/screenDisplay/fonts/Inter-Bold.ttf"
bannerFontPath = "./src/screenDisplay/fonts/Newsreader-SemiBoldItalic.ttf"
# Screens --preview --fake can show beyond the task scenarios.
PREVIEW_SCREENS = ["stale", "error"]
# The screen is left alone overnight; QUIET_HOURS="off" turns that off.
DEFAULT_QUIET_HOURS = "23:00-06:00"
ENV_FILE = Path(__file__).resolve().parent / "taskFetcher" / ".env"

def make_drawer(source):
    return TaskDrawer(fontPath, margins=margins(), two_columns=source.two_columns,
                      banner_font_path=bannerFontPath)

def margins():
    """Frame-safe margins, overridable with DISPLAY_MARGINS="top,right,bottom,left" (pixels)."""
    text = os.getenv("DISPLAY_MARGINS")
    return parse_margins(text) if text else DEFAULT_MARGINS

def make_renderer(source):
    """Turns what the refresh decided to draw into an image."""
    def render(action):
        drawer = make_drawer(source)
        if isinstance(action, DrawTasks):
            return drawer.create_task_image(action.tasks, updated_at=action.updated_at, stale=action.stale, reason=action.reason)
        return drawer.create_message_image(action.heading, action.detail)
    return render

def make_refresher(source, overnight_quiet=False):
    """overnight_quiet leaves the screen alone during QUIET_HOURS; a one-off --task always refreshes."""
    quiet_hours = QuietHours.from_config(os.getenv("QUIET_HOURS") or DEFAULT_QUIET_HOURS) if overnight_quiet else None
    return Refresher(source, make_renderer(source), EPaperPanel(), quiet_hours=quiet_hours)

def refresh_safely(refresher):
    """One refresh that can never end the run loop: a failure is logged and the next interval tries again."""
    try:
        refresher.refresh()
    except Exception as error:
        print(f"Refresh failed, will retry: {type(error).__name__}")

def task_run(refresh_interval_minutes, refresher):
    print(f"Running TodoDisplay every {refresh_interval_minutes} minutes, tasks from {refresher.source.name}")
    refresh_safely(refresher)
    schedule.every(refresh_interval_minutes).minutes.do(refresh_safely, refresher)

    while True:
        schedule.run_pending()
        time.sleep(1)


def task_test(source):
    image = make_drawer(source).create_task_image(source.fetch())
    image.show()

def task_preview(path, source, fake=None, simulate_panel=True, open_after=True, safe_area=False):
    if fake:
        source = FakeSource(fake if fake in SCENARIOS else "few")
    drawer = make_drawer(source)
    if fake == "error":
        image = drawer.create_message_image(*source.describe_error(OSError()))
    elif fake == "stale":
        stale_since = datetime.now() - timedelta(hours=3)
        image = drawer.create_task_image(source.fetch(), updated_at=stale_since, stale=True,
                                         reason=source.describe_error(OSError())[0])
    else:
        image = drawer.create_task_image(source.fetch())
    save_preview(image, path, simulate_panel, safe_area=drawer.margins if safe_area else None)
    print(f"Preview saved to {path}")
    if open_after:
        open_file(path)

def main():
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument('--source', choices=SOURCES,
                        help=f'Where tasks come from (default: TASK_SOURCE in .env, else {DEFAULT_SOURCE})')
    parser.add_argument('--task', action='store_true', help='Displays the task image on an epaper screen')
    parser.add_argument('--test', action='store_true', help='Displays the task image locally')
    parser.add_argument('--clear', action='store_true', help='Clears the display')
    parser.add_argument('--run', type=int, help='Runs the task display with a specified interval (in minutes)')
    parser.add_argument('--preview', nargs='?', const='previews/preview.png', metavar='PATH',
                        help='Saves the task image to a PNG (default previews/preview.png) without using the display')
    parser.add_argument('--fake', choices=sorted(SCENARIOS) + PREVIEW_SCREENS,
                        help='With --preview, use sample tasks instead of fetching; stale and error show those screens')
    parser.add_argument('--no-open', action='store_true', help='With --preview, do not open the PNG afterwards')
    parser.add_argument('--raw', action='store_true', help='With --preview, skip the black/white panel simulation')
    parser.add_argument('--safe-area', action='store_true', help='With --preview, outline the frame-safe area in red')
    args = parser.parse_args()
    load_dotenv(ENV_FILE)
    for warning in permission_warnings([ENV_FILE, os.getenv("TODOAPP_KEY_FILE")]):
        print(warning)
    try:
        source = resolve_source(args.source)
    except ValueError as error:
        parser.error(str(error))

    if args.preview:
        task_preview(args.preview, source, fake=args.fake, simulate_panel=not args.raw, open_after=not args.no_open,
                     safe_area=args.safe_area)
    elif args.run:
        task_run(args.run, make_refresher(source, overnight_quiet=True))
    elif args.task:
        make_refresher(source).refresh()
    elif args.clear:
        EPaperPanel().clear()
    elif args.test:
        task_test(source)
    else:
        print("No valid argument provided. Use --run N, --task, --preview, --test or --clear (see --help).")

if __name__ == "__main__":
    main()
