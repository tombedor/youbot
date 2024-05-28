import json
import logging
from youbot.data_models import YoubotUser
from youbot.clients.memgpt_client import memgpt_user_message


def user_message(youbot_user: YoubotUser, msg: str) -> str:
    response_list = memgpt_user_message(youbot_user, msg)

    for i in range(len(response_list) - 1, -1, -1):
        response = response_list[i]

        if response.role == "assistant" and response.text:
            return response.text
        elif response.role == "tool":
            logging.info("Tool response found")
            if json.loads(response.text)["status"] == "OK":
                return user_message(youbot_user, "[Automatic user invisible message] The result of your function call succeeded.")
            else:
                return user_message(
                    youbot_user, f"[Automatic user invisible message] The result of your function call failed: {response.text}"
                )
        else:
            logging.warn("unexpecected response: " + str(response))
    raise ValueError("No assistant response found in response list")
