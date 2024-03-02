import os

from dotenv import load_dotenv
from youbot.memgpt_client import MemGPTClient
from youbot.memgpt_extensions.functions.google_calendar import (
    create_calendar_event,
)

# TODO: Need to figure out oauth for multiple users better

load_dotenv()
DEMO_EMAIL = os.getenv("DEMO_USER_EMAIL")

if __name__ == "__main__":
    agent = MemGPTClient.get_or_create_agent("testbot")
    agent.add_function(create_calendar_event.__name__)

    response = MemGPTClient.user_message(
        msg=f"please link the google email {DEMO_EMAIL} to my account",
        agent_name=agent.agent_state.name,
    )

    MemGPTClient.user_message(
        msg='please create a calendar event called "test event" for tomorrow',
        agent_name=agent.agent_state.name,
    )
