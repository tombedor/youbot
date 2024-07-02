import json
import logging
from youbot.clients.memgpt_client import ToolCallWithoutPrecedingMessageError, memgpt_user_message
from toolz import curry

from youbot.memory.memory_processing import refresh_knowledge
from youbot.system_context import dump_data_to_spreadsheet, refresh_system_and_messages


@curry
def get_ai_reply(youbot_user_id: int, msg: str) -> str:
    try:
        response_list = memgpt_user_message(youbot_user_id, msg)
    except ToolCallWithoutPrecedingMessageError:
        logging.warn("Encountered error for tool call without preceding message, attempting context refresh")
        context_refresh(youbot_user_id)
        response_list = memgpt_user_message(youbot_user_id, msg)

    for i in range(len(response_list) - 1, -1, -1):
        response = response_list[i]

        if response.role == "assistant" and response.text:
            return response.text
        elif response.role == "tool":
            logging.info("Tool response found")
            if json.loads(response.text)["status"] == "OK":
                return get_ai_reply(youbot_user, "[Automatic user invisible message] The result of your function call succeeded.")  # type: ignore
            else:
                return get_ai_reply(
                    youbot_user_id, f"[Automatic user invisible message] The result of your function call failed: {response.text}"
                )  # type: ignore
        else:
            logging.warn("unexpecected response: " + str(response))
    raise ValueError("No assistant response found in response list")


def context_refresh(youbot_user_id: int) -> None:
    refresh_knowledge(youbot_user_id)
    refresh_system_and_messages(youbot_user_id)
    dump_data_to_spreadsheet(youbot_user_id)
