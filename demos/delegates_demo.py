from memgpt import MemGPT
from memgpt.config import MemGPTConfig

TESTBOT_NAME = 'testbot'

_config = MemGPTConfig.load()


client =  MemGPT()

client.list_agents()

agent_ids =[d['id'] for d in client.list_agents()['agents'] if d['name'] == TESTBOT_NAME]