from uuid import UUID

from youbot import get_celery
from youbot.clients.memgpt_client import MemGPTClient
import pytz

app = get_celery(queue="reminders")


@app.task
def process_reminder(agent_id: UUID, user_id: UUID, channel: str, message: str):

    system_message = f"[THIS IS A SYSTEM REMINDER, ENQUEUD BY AGENT]: {message}"
    agent_response = MemGPTClient.user_message(agent_id=agent_id, user_id=user_id, msg=system_message)

    if channel == "discord":
        print(agent_response)
