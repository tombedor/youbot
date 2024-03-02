from contextlib import contextmanager
from functools import lru_cache
import logging
from typing import Any, Generator
from uuid import UUID
import uuid
from youbot import AGENTS_CONFIG
from memgpt import MemGPT
from memgpt.agent import Agent
from memgpt.metadata import MetadataStore
from memgpt.config import MemGPTConfig


class AgentManager:
    metadata_store = MetadataStore()
    DEFAULT_MEMGPT_USER_ID = UUID(MemGPTConfig.anon_clientid)
    SERVER = MemGPT().server

    # @lru_cache
    @classmethod
    def get_client(cls, user_id: UUID = DEFAULT_MEMGPT_USER_ID) -> MemGPT:
        return MemGPT(user_id=str(user_id))

    # @lru_cache
    @classmethod
    def get_or_create_agent(cls, agent_name: str, user_id: UUID = DEFAULT_MEMGPT_USER_ID) -> Agent:
        client = cls.get_client(user_id)
        if not client.agent_exists(agent_name=agent_name):
            if agent_name not in AGENTS_CONFIG:
                agent_key = "youbot"
                logging.warning(f"defaulting to {agent_key} agent profile")
            else:
                agent_key = agent_name
            init_state = {"name": agent_name, **AGENTS_CONFIG[agent_key]}
            agent_state = client.create_agent(init_state)
        else:
            agent_state = cls.metadata_store.get_agent(agent_name=agent_name, user_id=user_id)
            if agent_state is None:
                raise ValueError(f"Agent state for {agent_name} not found.")
        return Agent(agent_state=agent_state, interface=client.interface)

    @classmethod
    @contextmanager
    def ephemeral_agent(cls) -> Generator[Agent, Any, None]:
        agent = None
        user_id = cls.DEFAULT_MEMGPT_USER_ID
        try:
            agent_name = "emphemeral_" + str(uuid.uuid4())
            agent = cls.get_or_create_agent(agent_name, user_id)
            yield agent
        finally:
            if agent is not None:
                cls.SERVER.delete_agent(user_id=user_id, agent_id=agent.agent_state.id)

    @classmethod
    def user_message(cls, agent_name: str, msg: str, user_id=DEFAULT_MEMGPT_USER_ID) -> str:
        agent = cls.get_or_create_agent(agent_name=agent_name, user_id=user_id)
        client = cls.get_client(user_id)
        response_list = client.user_message(str(agent.agent_state.id), msg)
        reply = next(r.get("assistant_message") for r in response_list if r.get("assistant_message"))  # type: ignore
        assert isinstance(reply, str)
        return reply
