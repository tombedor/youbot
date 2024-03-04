from youbot.jobs.task_manager import TaskManager


def _get_task_manager(self):
    if "task_manager" not in vars(self):
        self.task_manager = TaskManager()


def get_task_stats(self) -> str:
    self._get_task_manager().tasks
    return f"Total tasks: {len(self.task_manager.tasks)}"
