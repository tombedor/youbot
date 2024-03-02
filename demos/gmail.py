from youbot.memgpt_client import MemGPTClient
from youbot.memgpt_extensions.functions.gmail import send_email

with MemGPTClient.ephemeral_agent() as agent:
    agent.add_function(send_email.__name__)
    response = MemGPTClient.user_message(
        agent_name=agent.agent_state.name,
        msg="I have added the ability to send the user an email with the function send_email. Send a hello world email.",
    )
    print("foo")


# agent should be deleted
