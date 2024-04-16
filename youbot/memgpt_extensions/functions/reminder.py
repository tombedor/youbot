from datetime import datetime

from youbot import get_celery


def enqueue_reminder(year: int, month: int, day: int, hour: int, minute: int, tzname: str):

    app = get_celery(queue="reminders")
    if not is_valid_timezone:
        raise ValueError(f"tzinfo must be valid, got {tzname}")

    app.send_task(**args)
