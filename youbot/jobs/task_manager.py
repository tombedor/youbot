import uuid


class Task:
    VALID_STATUSES = ["pending", "completed", "failed"]

    def __init__(self, prompt: str):
        self.id = uuid.uuid4()
        self.prompt = prompt
        self.status = "pending"
        self.outcome = None


class TaskManager:
    def __init__(self):
        self.tasks = []
