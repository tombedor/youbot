from youbot.memgpt_client import MemGPTClient
from memgpt import MemGPT

from youbot.memgpt_extensions.functions.gmail import send_email

with MemGPTClient.ephemeral_agent() as agent:
    client = MemGPT(debug=True)
    agent.add_function(send_email.__name__)
    response = client.user_message(
        agent_id=str(agent.agent_state.id),
        message="I have added the ability to send the user an email with the function send_email. Send a hello world email.",
    )
    print("foo")


# agent should be deleted
