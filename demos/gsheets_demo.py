import uuid
from memgpt import MemGPT
from memgpt.agent import Agent

client = MemGPT()

agent_id = next(entry['id'] for entry in client.list_agents()['agents'] if entry['name'] == 'testbot')
agent_state = client.server.get_agent(agent_id=agent_id,user_id=client.user_id)

agent = Agent(agent_state=agent_state,interface=client.interface)

# TODO: add functions and demonstrate.

print('yay')

