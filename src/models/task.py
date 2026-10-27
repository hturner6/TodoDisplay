from datetime import date, time


class Task:
    TODO = "todo"
    DONE = "done"
    CANCELLED = "cancelled"
    MOVED = "moved"
    NOTE = "note"

    def __init__(self, title: str, due_date: date, status: str = TODO, priority: bool = False,
                 scheduled_time: time = None, weekly: bool = False):
        self.title = title
        self.due_date = due_date
        self.status = status
        self.priority = priority
        self.scheduled_time = scheduled_time
        self.weekly = weekly

    def __repr__(self):
        return f"Task(title={self.title}, due_date={self.due_date})"
