from datetime import datetime, timedelta
from models.task import Task

# An unchanged screen is redrawn at least this often, so its 'Updated HH:MM' footer stays honest.
REDRAW_AFTER = timedelta(hours=1)
# A failing fetch leaves the last screen alone until the data is this old, then marks it stale.
STALE_AFTER = timedelta(hours=2)


def describe_error(error: Exception) -> tuple[str, str]:
    """Heading and detail for the on-screen notice. Never includes the error text, which may hold secrets."""
    response = getattr(error, "response", None)
    if getattr(response, "status_code", None) == 401:
        return "Sign-in expired", "The TickTick token needs renewing"
    return "Cannot reach TickTick", "Will keep trying"


class RefreshPolicy:
    """Decides when the e-paper panel is worth redrawing, to limit ghosting and wear.

    Each decision returns None (leave the screen alone) or a tuple describing what to draw:
    ("tasks", tasks, updated_at) or ("message", heading, detail, updated_at).
    """

    def __init__(self):
        self.signature = None
        self.drawn_at = None
        self.last_tasks = None
        self.last_success = None
        self.shown_failure = None

    def on_success(self, tasks: list[Task], now: datetime):
        signature = (now.date(), tuple(repr(task) for task in tasks))
        self.last_tasks = tasks
        self.last_success = now
        self.shown_failure = None
        if signature == self.signature and now - self.drawn_at < REDRAW_AFTER:
            return None
        self.signature = signature
        self.drawn_at = now
        return ("tasks", tasks, now)

    def on_failure(self, error: Exception, now: datetime):
        if self.last_tasks is None:
            heading, detail = describe_error(error)
            if self.shown_failure == heading:
                return None
            self.shown_failure = heading
            return ("message", heading, detail, None)

        if now - self.last_success <= STALE_AFTER or self.shown_failure == "stale":
            return None
        self.shown_failure = "stale"
        self.signature = None
        self.drawn_at = now
        return ("tasks", self.last_tasks, self.last_success)
