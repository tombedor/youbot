import uuid
from youbot import MEMGPT_CONFIG
from youbot.memgpt_extensions.functions.meta_functions.meta_functions import (
    load_preset_functions,
)
from youbot.service.discord_service import AGENT_IDS
from memgpt.metadata import MetadataStore
from memgpt.agent import Agent
from memgpt import MemGPT


for user_id, agent_id in AGENT_IDS.items():
    client = MemGPT(user_id=user_id, auto_save=True, debug=True)
    metadata_store = MetadataStore(MEMGPT_CONFIG)
    agent_state = metadata_store.get_agent(agent_id=agent_id, user_id=uuid.UUID(user_id))
    assert agent_state
    agent = Agent(agent_state=agent_state, interface=client.interface)
    load_preset_functions(agent)
    client.save()
