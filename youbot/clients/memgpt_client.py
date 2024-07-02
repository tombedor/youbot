import json
import logging
from typing import List
from uuid import UUID

from memgpt.metadata import MetadataStore
from memgpt.server.server import SyncServer
from memgpt.data_types import User, AgentState, Message
from memgpt.agent import Agent, save_agent as memgpt_save_agent
from requests.exceptions import HTTPError

from youbot.store import get_youbot_user_by_id

from toolz import pipe


metadata_store = MetadataStore()

server = SyncServer()


def create_agent(user_id: UUID) -> AgentState:
    agent_state = AgentState(
        user_id=user_id,
    )
    metadata_store.create_agent(agent_state)
    agent_state = metadata_store.get_agent(user_id=user_id)
    assert agent_state
    return agent_state


def create_user(user_id: UUID) -> User:
    user = User(user_id)
    metadata_store.create_user(user)
    return user


def get_agent(youbot_user_id: int) -> Agent:
    youbot_user = get_youbot_user_by_id(youbot_user_id)
    return server._load_agent(user_id=youbot_user.memgpt_user_id, agent_id=youbot_user.memgpt_agent_id)


def get_memgpt_messages(youbot_user_id: int) -> List[Message]:
    return get_agent(youbot_user_id)._messages


class ToolCallWithoutPrecedingMessageError(Exception):
    pass


def memgpt_user_message(youbot_user_id: int, msg: str) -> List[Message]:
    youbot_user = get_youbot_user_by_id(youbot_user_id)
    try:
        return server.user_message(user_id=youbot_user.memgpt_user_id, agent_id=youbot_user.memgpt_agent_id, message=msg)
    except HTTPError as e:
        error_msg = pipe(
            e.response.text,
            json.loads,
            lambda _: _.get("error", {}).get("message"),
        )
        if error_msg and "Invalid parameter: messages with role" in error_msg:
            raise ToolCallWithoutPrecedingMessageError(error_msg)
        else:
            logging.error("error message = " + error_msg)
            raise e


def set_messages(youbot_user_id: int, messages: List[Message]) -> None:
    agent = get_agent(youbot_user_id)
    agent._messages = messages
    memgpt_save_agent(agent)
