import datetime

class Task:
    def __init__(self, title: str, due_date: str, category: str = None):
        self.title = title
        self.due_date = due_date
        self.category = category

    def __repr__(self):
        return f"Task(title={self.title}, due_date={self.due_date}, category={self.category})"