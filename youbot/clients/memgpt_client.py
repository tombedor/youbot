from typing import List
from uuid import UUID

from memgpt.metadata import MetadataStore
from memgpt.server.server import SyncServer
from memgpt.data_types import User, AgentState, Message
from memgpt.agent import Agent, save_agent as memgpt_save_agent

from youbot.data_models import YoubotUser


metadata_store = MetadataStore()

server = SyncServer()


def create_agent(user_id: UUID) -> AgentState:
    agent_name = "youbot"
    agent_state = AgentState(
        user_id=user_id,
    )
    metadata_store.create_agent(agent_state)
    agent_state = metadata_store.get_agent(agent_name=agent_name, user_id=user_id)
    assert agent_state
    return agent_state


def create_user(user_id: UUID) -> User:
    user = User(user_id)
    metadata_store.create_user(user)
    return user


def get_agent(youbot_user: YoubotUser) -> Agent:
    return server._load_agent(user_id=youbot_user.memgpt_user_id, agent_id=youbot_user.memgpt_agent_id)


def memgpt_user_message(youbot_user: YoubotUser, msg: str) -> List[Message]:
    return server.user_message(user_id=youbot_user.memgpt_user_id, agent_id=youbot_user.memgpt_agent_id, message=msg)


def set_messages(youbot_user: YoubotUser, messages: List[Message]) -> None:
    agent = get_agent(youbot_user)
    agent._messages = messages
    memgpt_save_agent(agent)
