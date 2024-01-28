import uuid
from memgpt import MemGPT
from memgpt.agent import Agent

from ..functions.delegates.delegates import TESTER, send_message_to_agent

agent_name = 'testbot'
client = MemGPT()

agent_id = next(entry['id'] for entry in client.list_agents()['agents'] if entry['name'] == agent_name)
agent_state = client.server.get_agent(agent_id=agent_id,user_id=client.user_id)

agent = Agent(agent_state=agent_state,interface=client.interface)

agent.add_function(send_message_to_agent.__name__)

client.user_message(agent_id, f"Use your send_message_to_agent function to converse with an agent called {TESTER}. Understand what it is capable of")
