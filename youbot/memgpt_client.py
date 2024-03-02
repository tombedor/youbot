from contextlib import contextmanager
import logging
from typing import Any, Generator
from uuid import UUID
import uuid
from youbot import AGENTS_CONFIG, MEMGPT_CONFIG
from memgpt.agent import Agent
from memgpt.metadata import MetadataStore
from memgpt.config import MemGPTConfig
from memgpt.client.client import LocalClient
from memgpt.server.server import SyncServer
from memgpt.data_types import User


class MemGPTClient:
    metadata_store = MetadataStore(MEMGPT_CONFIG)
    DEFAULT_MEMGPT_USER_ID = UUID(MemGPTConfig.anon_clientid)
    
    session_maker = metadata_store.session_maker # note this is a function
    
    @classmethod
    def create_user(cls, user_id: UUID) -> None:
        cls.metadata_store.create_user(User(user_id))

    @classmethod
    def get_server(cls) -> SyncServer:
        return cls.get_client().server

    # @lru_cache
    @classmethod
    def get_client(cls, user_id: UUID = DEFAULT_MEMGPT_USER_ID) -> LocalClient:
        return LocalClient(auto_save=True, user_id=str(user_id))

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
            agent_state = client.create_agent(**init_state)  # type: ignore
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
                cls.get_server().delete_agent(user_id=user_id, agent_id=agent.agent_state.id)

    @classmethod
    def user_message(cls, agent_name: str, msg: str, user_id=DEFAULT_MEMGPT_USER_ID) -> str:
        agent = cls.get_or_create_agent(agent_name=agent_name, user_id=user_id)
        client = cls.get_client(user_id)
        response_list = client.user_message(str(agent.agent_state.id), msg)
        reply = next(r.get("assistant_message") for r in response_list if r.get("assistant_message"))  # type: ignore
        assert isinstance(reply, str)
        return reply
