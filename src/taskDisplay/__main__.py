from taskDisplay.createTaskImage import create_task_image
from models.task import Task

def main():
    tasks = [
        Task(title="Task 1", due_date="2023-09-29", category="Work"),
        Task(title="Task 2", due_date="2023-09-30", category="Personal"),
        Task(title="Task 3", due_date="2023-10-01", category="Work"),
    ]
    image = create_task_image(tasks)
    image.show()

if __name__ == "__main__":
    main()