from datetime import datetime, timedelta
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
    "UTC",
]


def enqueue_reminder_by_time_difference_from_now(self, hours: int, minutes: int, message: str) -> str:
    """Enqueues a reminder for the given time difference from now, with the given message.

        hours (int): number of hours from now to enqueue reminder
        minutes (int): number of minutes from now to enqueue reminder
        message (str): The message

    Returns:
        str: Result of the reminder enqueue attempt
    """
    current_time = datetime.now(pytz.utc)
    reminder_time = current_time + timedelta(hours=hours, minutes=minutes)
    return enqueue_reminder(
        self, reminder_time.year, reminder_time.month, reminder_time.day, reminder_time.hour, reminder_time.minute, "UTC", message
    )


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

    agent_id = self.agent_state.id
    youbot_user = store.get_youbot_user_by_agent_id(agent_id)

    store.create_agent_reminder(youbot_user.id, reminder_time, message)
    return "Reminder enqueued."
