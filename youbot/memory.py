from collections import deque
from copy import deepcopy
from hashlib import md5
import json
import logging
import time
import uuid

from attr import dataclass

from youbot.clients.llm_client import count_tokens, query_llm
from youbot.clients.memgpt_client import get_agent, set_messages
from youbot.knowledge_base.knowledge_base import NLP
from youbot.prompts import (
    ARCHIVAL_MEMORY_SYSTEM_PROMPT,
    DATETIME_FORMATTER,
    SUMMARIZER_SYSTEM_PROMPT,
    background_info_system_prompt,
    get_system_instruction,
)
from youbot.store import YoubotUser, get_entity_name_text
from youbot import REDIS_CLIENT

INVALIDATION_SECONDS_WITHOUT_NEW_MESSAGE = 60 * 60 * 24
INVALIDATION_SECONDS_AFTER_NEW_MESSAGE = 60 * 15
MODEL_CONTEXT_WINDOW = 16384
TOKEN_REFRESH_THRESHOLD = int(MODEL_CONTEXT_WINDOW * 0.66)
TARGET_CONTEXT_REFRESH_TOKENS = int(MODEL_CONTEXT_WINDOW * 0.33)


def formatted_readable_messages(youbot_user: YoubotUser) -> str:
    agent = get_agent(youbot_user)
    msg_strs = []
    for message in agent._messages:
        datetime_str = message.created_at.strftime(DATETIME_FORMATTER)
        if message.role == "system":
            msg_strs.append(f"SYSTEM ({datetime_str}): {message.text}")
        elif message.role == "user":
            msg_d = json.loads(message.text)
            if "message" in msg_d:
                msg = msg_d["message"]
                msg_strs.append(f"{youbot_user.name.upper()} ({datetime_str}): {msg}")
            elif "type" in msg_d and msg_d["type"] == "heartbeat":
                continue
            else:
                raise ValueError(f"Unknown message format: {msg_d}")
        elif message.role == "assistant":
            if message.text:
                msg_strs.append(f"YOUBOT ({datetime_str}): {message.text}")
            elif message.tool_calls:
                msg_strs.append(f"YOUBOT TOOL CALL ({datetime_str}): {message.tool_calls[0].function['name']}")
            else:
                raise ValueError(f"Expected either message text or tool call: {message}")
        elif message.role == "tool":
            msg_strs.append(f"TOOL ({datetime_str}): {message.text}")
    return "\n".join(msg_strs)


def get_refreshed_context_message(youbot_user: YoubotUser) -> str:
    summary = query_llm(prompt=formatted_readable_messages(youbot_user), system=SUMMARIZER_SYSTEM_PROMPT)

    entities = set()
    for e in NLP.process(summary).ents:
        entities.add((e.text, e.label_))

    background_info = []
    for e in entities:
        entity_info = get_entity_name_text(youbot_user=youbot_user, entity_name=e[0])
        if entity_info:
            background_info.append(entity_info)

    background_info = "\n".join(background_info)

    summary_with_background = query_llm(prompt=summary, system=background_info_system_prompt(background_info))
    return summary_with_background


@dataclass
class WatermarkStatus:
    message_hash: str
    epoch_seconds: int


class ContextWatermark:
    def __init__(self, message_hash: str, epoch_seconds: int):
        self.message_hash = message_hash
        self.epoch_seconds = epoch_seconds

    @classmethod
    def set(cls, youbot_user: YoubotUser):
        message_hash = messages_md5(youbot_user)
        epoch_seconds = int(time.time())

        watermark_key = cls._watermark_key(youbot_user.id)
        watermark_d = {"message_hash": message_hash, "epoch_seconds": epoch_seconds}
        REDIS_CLIENT.set(watermark_key, json.dumps(watermark_d))

    @classmethod
    def get(cls, youbot_user: YoubotUser):
        redis_response = REDIS_CLIENT.get(cls._watermark_key(youbot_user.id))
        if redis_response is None:
            return None
        else:
            assert type(redis_response) == str
            d = json.loads(redis_response)  # type: ignore
            return WatermarkStatus(**d)

    @classmethod
    def _watermark_key(cls, youbot_user_id: int) -> str:
        return f"youbot_context_watermark_{youbot_user_id}"


def messages_md5(youbot_user: YoubotUser) -> str:
    agent = get_agent(youbot_user)
    msgs_str = "_".join([str(msg) for msg in agent.messages])
    return md5(msgs_str.encode()).hexdigest()


def is_context_refresh_needed(youbot_user: YoubotUser) -> bool:
    watermark = ContextWatermark.get(youbot_user)
    agent = get_agent(youbot_user)
    token_counts = [count_tokens(str(msg)) for msg in agent.messages]
    new_message_hash = messages_md5(youbot_user)

    if watermark is None:
        return True

    is_messages_changed = new_message_hash != watermark.message_hash
    elapsed_seconds = int(time.time()) - watermark.epoch_seconds

    logging.info(f"Token count {sum(token_counts)} out of limit {TOKEN_REFRESH_THRESHOLD}")
    if sum(token_counts) > TOKEN_REFRESH_THRESHOLD:
        logging.info("Token count over threshold")
        return True
    elif is_messages_changed and elapsed_seconds > INVALIDATION_SECONDS_AFTER_NEW_MESSAGE:
        logging.info("Message changed, elapsed time over threshold")
        return True
    elif elapsed_seconds > INVALIDATION_SECONDS_WITHOUT_NEW_MESSAGE:
        logging.info("Elapsed time over threshold")
        return True
    else:
        return False


def refresh_context(youbot_user: YoubotUser) -> None:
    """Refreshes context, saving to archival memory and compressing the context window.

    Args:
        youbot_user (YoubotUser): Youbot user to examine.
    """
    logging.info("Refreshing context")

    agent = get_agent(youbot_user)
    token_counts = [count_tokens(str(msg)) for msg in agent.messages]

    archival_memory = query_llm(prompt=formatted_readable_messages(youbot_user), system=ARCHIVAL_MEMORY_SYSTEM_PROMPT)
    agent.persistence_manager.archival_memory.insert(archival_memory)

    system_message = deepcopy(agent._messages[0])
    assert system_message.role == "system"
    new_context = get_refreshed_context_message(youbot_user)
    logging.info(f"New context: {new_context}")
    system_message.text = get_system_instruction(new_context)
    system_message.id = uuid.uuid4()

    agent.persistence_manager.persist_messages([system_message])

    new_messages = deque()
    current_token_count = count_tokens(system_message.text)

    for idx in range(len(agent._messages) - 1, 0, -1):  # skip system message
        # if we have a tool message, we must also include the assistant message that preceded as per openai
        if current_token_count > TARGET_CONTEXT_REFRESH_TOKENS and new_messages[-1].role != "tool":
            break
        current_msg = agent._messages[idx]
        new_messages.appendleft(current_msg)
        current_token_count += token_counts[idx]
    new_messages.appendleft(system_message)

    set_messages(youbot_user, list(new_messages))
    ContextWatermark.set(youbot_user)
