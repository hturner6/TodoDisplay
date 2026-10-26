from json import JSONEncoder
from datetime import datetime


class Task:
    TODO = "todo"
    DONE = "done"
    CANCELLED = "cancelled"
    MOVED = "moved"
    NOTE = "note"

    def __init__(self, title: str, due_date: datetime, category: str = None,
                 status: str = TODO, priority: bool = False):
        self.title = title
        self.due_date = due_date
        self.category = category
        self.status = status
        self.priority = priority

    def __repr__(self):
        return f"Task(title={self.title}, due_date={self.due_date}, category={self.category})"


    def days_elapsed(start_date, end_date):
        # Both dates should be datetime.date or datetime.datetime objects
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()
        return (end_date - start_date).days

    def format_due_date(date):
        if date is None:
            return "No due date"

        today = datetime.now().date()
        days = Task.days_elapsed(date, today)

        if date == today:
            return "Today"
        elif date < today:
            return f"Overdue by {abs(days)} days"
        else:
            return f"{Task.format_date_string(date)}"

    def short_due_label(self) -> str:
        """Compact due text for the display, e.g. "Today", "2d overdue" or "Fri 30 Oct"."""
        if self.due_date is None:
            return ""

        today = datetime.now().date()
        if self.due_date == today:
            return "Today"
        if self.due_date < today:
            return f"{Task.days_elapsed(self.due_date, today)}d overdue"
        return Task.format_date_string(self.due_date)

    def format_date_string(date):
        return date.strftime('%a %d %b')

    def is_today_or_overdue(self) -> bool:
        if self.due_date is None:
            return False

        today = datetime.now().date()
        return self.due_date <= today


    def toJSON(self):
        return {
            "title": self.title,
            "due_date": self.due_date,
            "category": self.category
        }

    def __str__(self):
        if self.due_date is None:
            return f"* {self.title}"

        return f"* {self.title} - {Task.format_due_date(self.due_date)}"

class TaskEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Task):
            return obj.toJSON()
        return super().default(obj)
