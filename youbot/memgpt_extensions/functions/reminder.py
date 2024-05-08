from datetime import datetime
import time
import pytz

from youbot.store import Store

VALID_TIMEZONES = [
    "US/Alaska",
    "US/Arizona",
    "US/Central",
    "US/Eastern",
    "US/Hawaii",
    "US/Mountain",
    "US/Pacific",
]


def enqueue_reminder(self, year: int, month: int, day: int, hour: int, minute: int, timezone_name: str, message: str) -> str:
    """Enqueues a reminder for the given time, with the given message

    Args:
        year (int): year of reminder
        month (int): month of reminder
        day (int): day of reminder
        hour (int): hour of reminder
        minute (int): minut of reminder
        timezone_name (str): timezone name for reminder
        message (str): reminder message

    Raises:
        ValueError: For invalid timezones

    Returns:
        str: Result of the reminder enqueue attempt
    """

    if timezone_name not in VALID_TIMEZONES:
        raise ValueError(f"Invalid timezone. Valid options are: {VALID_TIMEZONES}")
    tz = pytz.timezone(timezone_name)
    reminder_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute, tzinfo=tz).astimezone(pytz.utc)

    store = Store()

    agent_id = self.state.id
    youbot_user = store.get_youbot_user_by_agent_id(agent_id)

    store.create_agent_reminder(youbot_user.id, reminder_time, message)
    return "Reminder enqueued."
