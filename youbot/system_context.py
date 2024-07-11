from collections import deque
from copy import deepcopy
from datetime import datetime
from functools import partial, reduce
import json
import logging
import time
from typing import Optional
import uuid
from toolz import pipe, curry, first
from toolz.curried import map, remove
from operator import add


from youbot.clients.google_client import YoubotSpreadsheet, write_data_to_spreadsheet
from youbot.clients.llm_client import count_tokens
from youbot.clients.memgpt_client import get_agent, get_memgpt_messages, set_messages
from youbot.data_models import Fact
from youbot.memory.google_calendar_facts import get_raw_text_summary
from youbot.memory.memory_processing import calculate_ent_fact
from youbot.prompts import (
    CORE_DIRECTIVE,
    PERSONA,
    summarize_for_archival_memory,
    summary_with_background,
    summarize_calendar_text,
    summarize,
)
from youbot.store import get_entity_name_label_texts, get_entity_name_summary, get_recent_and_soon_events, get_youbot_user_by_id
from youbot.prompts import date_to_string
from youbot import REDIS_CLIENT
from memgpt.data_types import Message


WATERMARK_INVALIDATION_SECONDS = 60 * 15
MODEL_CONTEXT_WINDOW = 16384
TOKEN_REFRESH_THRESHOLD = int(MODEL_CONTEXT_WINDOW * 0.66)
TARGET_CONTEXT_REFRESH_TOKENS = int(MODEL_CONTEXT_WINDOW * 0.33)


def get_refreshed_system_message(youbot_user_id: int) -> str:
    conversational_summary = pipe(
        youbot_user_id,
        get_formatted_convo_messages,
        summarize,
        str,
    )

    entity_memories = pipe(
        conversational_summary,
        lambda _: Fact(youbot_user_id, _, datetime.now()),
        calculate_ent_fact,
        map(lambda _: get_entity_name_summary(youbot_user_id, _.entity_name, _.entity_label.name)),
        remove(lambda _: _ is None),
        list,
        "\n".join,
        str,
    )

    event_summaries = pipe(
        youbot_user_id,
        get_recent_and_soon_events,
        map(get_raw_text_summary(youbot_user_id)),
        "\n\n".join,
        summarize_calendar_text,
        list,
        "\n\n".join,
        str,
    )

    return summary_with_background(
        "\n\n".join(
            [CORE_DIRECTIVE, PERSONA, conversational_summary, entity_memories, event_summaries]  # type: ignore
        )  # type: ignore
    )  # type:ignore


@curry
def format_message(youbot_user_id: int, message: Message) -> Optional[str]:
    youbot_user = get_youbot_user_by_id(youbot_user_id)
    datetime_str = date_to_string(message.created_at)
    if message.role == "system":
        return f"SYSTEM ({datetime_str}): {message.text}"
    elif message.role == "user":
        msg_d = json.loads(message.text)
        if "message" in msg_d:
            msg = msg_d["message"]
            return f"{youbot_user.name.upper()} ({datetime_str}): {msg}"
        elif "type" in msg_d and msg_d["type"] in ["heartbeat", "login"]:
            return None
        else:
            raise ValueError(f"Unknown message format: {msg_d}")
    elif message.role == "assistant":
        if message.text:
            return f"YOUBOT ({datetime_str}): {message.text}"
        elif message.tool_calls:
            return f"YOUBOT TOOL CALL ({datetime_str}): {message.tool_calls[0].function['name']}"
        else:
            raise ValueError(f"Expected either message text or tool call: {message}")


def get_formatted_convo_messages(youbot_user_id: int) -> str:
    return pipe(
        youbot_user_id,
        get_memgpt_messages,
        map(format_message(youbot_user_id)),
        remove(lambda _: _ is None),
        list,
        "\n".join,
        str,
    )


def set_context_watermark_seconds(youbot_user_id: int) -> None:
    pipe(youbot_user_id, context_watermark_key, lambda _: REDIS_CLIENT.set(_, int(time.time())))


def get_context_watermark_seconds(youbot_user_id: int) -> Optional[int]:
    return pipe(youbot_user_id, context_watermark_key, REDIS_CLIENT.get, lambda _: int(_) if _ is not None else None)


def context_watermark_key(youbot_user_id: int) -> str:
    return f"youbot_context_watermark_s{youbot_user_id}"


def is_context_refresh_needed(youbot_user_id: int) -> bool:
    token_count = pipe(
        youbot_user_id,
        get_memgpt_messages,
        map(lambda _: _.text),
        remove(lambda _: _ is None),
        map(count_tokens),
        partial(reduce, add),
    )

    if token_count > TOKEN_REFRESH_THRESHOLD:
        logging.info(f"Token count {token_count} exceeds threshold {TOKEN_REFRESH_THRESHOLD}")
        return True
    else:
        logging.info(f"Token count {token_count} does not exceed threshold {TOKEN_REFRESH_THRESHOLD}")

    context_watermark_seconds = get_context_watermark_seconds(youbot_user_id)

    if context_watermark_seconds is None:
        logging.info("No context watermark found")
        return True

    elapsed_time = int(time.time()) - context_watermark_seconds
    if elapsed_time > WATERMARK_INVALIDATION_SECONDS:
        logging.info(f"Context watermark age {elapsed_time} exceeds threshold {WATERMARK_INVALIDATION_SECONDS}")
        return True
    else:
        logging.info(f"Context watermark age {elapsed_time} is below threshold {WATERMARK_INVALIDATION_SECONDS}")

    return False


def _check_is_system_message(msg: Message) -> Message:
    if msg.role != "system":
        raise ValueError(f"Expected system message, got {msg}")
    return msg


@curry
def _clone_with_new_text(new_text: str, msg: Message) -> Message:
    new_msg = deepcopy(msg)
    new_msg.text = new_text
    new_msg.id = uuid.uuid4()
    return new_msg


def refresh_system_and_messages(youbot_user_id: int) -> None:
    """Refreshes context, saving to archival memory and compressing the context window.

    Args:
        youbot_user (YoubotUser): Youbot user to examine.
    """
    logging.info("Refreshing context")

    agent = get_agent(youbot_user_id)
    token_counts = [count_tokens(str(msg)) for msg in agent.messages]

    # Save memory of current conversation
    pipe(
        youbot_user_id,
        get_formatted_convo_messages,
        summarize_for_archival_memory,
        agent.persistence_manager.archival_memory.insert,
    )

    # Calculate and persist new system message
    new_system_message = pipe(
        youbot_user_id,
        get_memgpt_messages,
        first,
        _check_is_system_message,
        _clone_with_new_text(get_refreshed_system_message(youbot_user_id)),
    )
    assert isinstance(new_system_message, Message)

    agent.persistence_manager.persist_messages([new_system_message])

    new_messages = deque()
    current_token_count = count_tokens(new_system_message.text)

    for idx in range(len(agent._messages) - 1, 0, -1):  # skip system message
        # if we have a tool message, we must also include the assistant message that preceded as per openai
        if current_token_count > TARGET_CONTEXT_REFRESH_TOKENS and new_messages[-1].role != "tool":
            break

        # if we encounter a tool message, ensure the previous message had a tool call
        if agent._messages[idx].role == "tool" and agent._messages[idx - 1].tool_calls is None:
            logging.warn(f"Dropping tool message without preceding tool call: {agent._messages[idx].id}")
            continue

        current_msg = agent._messages[idx]
        new_messages.appendleft(current_msg)
        current_token_count += token_counts[idx]
    new_messages.appendleft(new_system_message)

    set_messages(youbot_user_id, list(new_messages))
    set_context_watermark_seconds(youbot_user_id)


def dump_data_to_spreadsheet(youbot_user_id: int) -> None:
    spreadsheet = YoubotSpreadsheet.get_or_create(youbot_user_id, "Youbot Data", ["Context", "Entities"])
    if not spreadsheet:
        logging.info("Could not get or create spreadsheet")
        return

    pipe(
        youbot_user_id,
        get_memgpt_messages,
        first,
        lambda msg: [["Context Message"], [msg.text]],
        write_data_to_spreadsheet(spreadsheet, "Context"),
    )

    pipe(
        youbot_user_id,
        get_entity_name_label_texts,
        sorted,
        lambda data: [["Entity Name", "Entity Label", "Text"]] + data,
        write_data_to_spreadsheet(spreadsheet, "Entities"),
    )
