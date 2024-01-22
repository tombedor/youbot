from memgpt import MemGPT
from memgpt.config import MemGPTConfig
from memgpt.data_types import User, AgentState
from memgpt.metadata import MetadataStore
from copy import deepcopy

TESTBOT_NAME = 'testbot'

_config = vars(MemGPTConfig.load())


client =  MemGPT(config = _config)

client.list_agents()

agent_ids =[d['id'] for d in client.list_agents()['agents'] if d['name'] == TESTBOT_NAME]