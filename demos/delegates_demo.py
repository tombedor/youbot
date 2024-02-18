import uuid
from memgpt import MemGPT
from memgpt.agent import Agent

from youbot.memgpt_extensions.functions.delegates import send_message_to_agent, TESTER

agent_name = "testbot"
client = MemGPT()

agent_id = next(
    entry["id"]
    for entry in client.list_agents()["agents"]
    if entry["name"] == agent_name
)
agent_state = client.server.get_agent(agent_id=agent_id, user_id=client.user_id)
assert agent_state

agent = Agent(agent_state=agent_state, interface=client.interface)

agent.add_function(send_message_to_agent.__name__)

client.user_message(
    agent_id,
    f"Use your send_message_to_agent function to converse with an agent called {TESTER}. Understand what it is capable of",
)
