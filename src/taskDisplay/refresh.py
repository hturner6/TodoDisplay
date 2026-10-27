from dataclasses import dataclass
from datetime import datetime, timedelta
from models.task import Task
from taskDisplay.screenLayout import select
from taskFetcher.taskSource import TaskSource

# An unchanged screen is redrawn at least this often, so its 'Updated HH:MM' footer stays honest.
REDRAW_AFTER = timedelta(hours=1)
# A failing fetch leaves the last screen alone until the data is this old, then marks it stale.
STALE_AFTER = timedelta(hours=2)


@dataclass(frozen=True)
class DrawTasks:
    tasks: list[Task]
    updated_at: datetime
    stale: bool = False  # the data is old because refreshing keeps failing


@dataclass(frozen=True)
class DrawMessage:
    heading: str
    detail: str


class RefreshPolicy:
    """Decides when the e-paper panel is worth redrawing, to limit ghosting and wear.

    Each decision returns None (leave the screen alone), a DrawTasks or a DrawMessage.
    """

    def __init__(self, source: TaskSource):
        self.source = source
        self.signature = None
        self.drawn_at = None
        self.last_tasks = None
        self.last_success = None
        self.shown_failure = None

    def on_success(self, tasks: list[Task], now: datetime):
        # Everything the screen shows: a task ticked off or moved to another time must redraw, but a
        # change to a Task that is not on the screen must not.
        selected = select(tasks, now.date())
        signature = (now.date(), tuple(tuple((task.title, task.due_date, task.status, task.priority,
                                              task.scheduled_time, task.weekly) for task in group)
                                       for group in selected))
        self.last_tasks = tasks
        self.last_success = now
        self.shown_failure = None
        if signature == self.signature and now - self.drawn_at < REDRAW_AFTER:
            return None
        self.signature = signature
        self.drawn_at = now
        return DrawTasks(tasks, now)

    def on_failure(self, error: Exception, now: datetime):
        if self.last_tasks is None:
            heading, detail = self.source.describe_error(error)
            if self.shown_failure == heading:
                return None
            self.shown_failure = heading
            return DrawMessage(heading, detail)

        if now - self.last_success <= STALE_AFTER or self.shown_failure == "stale":
            return None
        self.shown_failure = "stale"
        self.signature = None
        self.drawn_at = now
        return DrawTasks(self.last_tasks, self.last_success, stale=True)


class Refresher:
    """One refresh of the screen: fetch the tasks, decide whether to redraw, draw, show.

    render turns a DrawTasks or DrawMessage into an image; panel has show(image). A failed fetch
    is handled here, through the policy; anything else (such as the panel failing) is raised.
    """

    def __init__(self, source: TaskSource, render, panel):
        self.source = source
        self._render = render
        self._panel = panel
        self._policy = RefreshPolicy(source)

    def refresh(self, now: datetime = None):
        now = now or datetime.now()
        try:
            action = self._policy.on_success(self.source.fetch(), now)
        except Exception as error:
            print(f"Could not fetch tasks: {type(error).__name__}")
            action = self._policy.on_failure(error, now)

        if action is None:
            print("Screen left as it is")
            return
        self._panel.show(self._render(action))
