import os

from dotenv import load_dotenv
from youbot.memgpt_client import MemGPTClient
from youbot.memgpt_extensions.functions.google_calendar import (
    create_calendar_event,
)
from memgpt import MemGPT

# TODO: Need to figure out oauth for multiple users better

load_dotenv()
DEMO_EMAIL = os.getenv("DEMO_USER_EMAIL")

if __name__ == "__main__":
    agent = MemGPTClient.get_or_create_agent("testbot")
    agent.add_function(create_calendar_event.__name__)

    client = MemGPT()
    response = client.user_message(
        message=f"please link the google email {DEMO_EMAIL} to my account",
        agent_id=str(agent.agent_state.id),
    )

    client.user_message(
        message='please create a calendar event called "test event" for tomorrow',
        agent_id=str(agent.agent_state.id),
    )
