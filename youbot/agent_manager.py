from contextlib import contextmanager
import uuid
from youbot import AGENTS_CONFIG, ROOT_DIR
from memgpt import MemGPT
from memgpt.agent import Agent
from memgpt.metadata import MetadataStore


class AgentManager:
    client = MemGPT()
    metadata_store = MetadataStore()
    user_id = client.user_id

    @classmethod
    def get_or_create_agent(cls, agent_name: str, allow_default: bool = False) -> Agent:
        if not cls.client.agent_exists(agent_name=agent_name):
            if agent_name not in AGENTS_CONFIG:
                if allow_default:
                    agent_key = "youbot"
                else:
                    raise ValueError(
                        f"Agent name {agent_name} not found in AGENTS_CONFIG, values found: {list(AGENTS_CONFIG.keys())}"
                    )
            else:
                agent_key = agent_name
            init_state = {"name": agent_name, **AGENTS_CONFIG[agent_key]}
            agent_state = cls.client.create_agent(init_state)
        else:
            agent_state = cls.metadata_store.get_agent(
                agent_name=agent_name, user_id=cls.user_id
            )
            if agent_state is None:
                raise ValueError(f"Agent state for {agent_name} not found.")
        return Agent(agent_state=agent_state, interface=cls.client.interface)

    @classmethod
    @contextmanager
    def ephemeral_agent(cls):
        agent = None
        try:
            agent_name = "emphemeral_" + str(uuid.uuid4())
            agent = cls.get_or_create_agent(agent_name, allow_default=True)
            yield agent
        finally:
            if agent is not None:
                cls.client.server.delete_agent(
                    user_id=cls.user_id, agent_id=agent.agent_state.id
                )
