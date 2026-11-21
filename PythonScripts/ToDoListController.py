from TaskController import TaskController
from Enums import Priority
from datetime import datetime


class ToDoListController(TaskController):
    def __init__(self, name: str):
        # Just initialise the parent TaskController

        super().__init__(name)

    # BASIC GETTERS
    def get_tasks_by_status(self, status: str):
        status = status.lower()
        tasks = self.get_all_tasks()

        if status == "completed":
            return [t for t in tasks if t.complete]

        if status == "pending":
            return [t for t in tasks if not t.complete]

        return []

    def get_tasks_by_priority(self, priority: Priority):
        return [t for t in self.get_all_tasks() if t.priority == priority]

    def get_tasks_by_tag(self, tag: str):
        tag = tag.lower()
        return [
            t for t in self.get_all_tasks()
            if any(tag in tg.lower() for tg in t.tags)
        ]

    def get_todays_calendar_tasks(self, calendar_controller):
        today = datetime.today()
        return calendar_controller.get_tasks_for_day(today)

    # STATUS UPDATES

    def mark_task_complete(self, task_id: str):
        return self.edit_task(task_id, {"complete": True})

    # SORTING (UI ONLY – returns sorted copies, does not mutate self.tasks)

    def sort_tasks(self, criteria: str):
        criteria = criteria.lower()
        tasks = self.get_all_tasks()

        if criteria == "priority":
            return sorted(tasks, key=lambda t: t.priority.value)

        if criteria == "due":
            return sorted(tasks, key=lambda t: t.due_date or datetime.max)

        if criteria == "title":
            return sorted(tasks, key=lambda t: t.title.lower())

        return tasks

    # AI QUICK WINS SORT (UI ONLY)

    def quick_wins_sort(self):
        tasks = self.get_all_tasks()
        return sorted(
            tasks,
            key=lambda t: (t.priority.value, t.due_date or datetime.max)
        )