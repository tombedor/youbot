from typing import Optional
from uuid import uuid4
from youbot.data_models import YoubotUser
from youbot.clients.memgpt_client import create_agent, create_user
from youbot.store import create_youbot_user, get_youbot_user_by_phone, get_youbot_user_by_name, get_youbot_user_by_id


def onboard_user(human_name: str, phone: Optional[str]) -> YoubotUser:
    if phone:
        try:
            existing_user = get_youbot_user_by_phone(phone)
            if existing_user:
                raise ValueError(f"User with phone {phone} already exists")
        except KeyError:
            pass  # expected
    else:
        try:
            existing_user = get_youbot_user_by_name(human_name)
        except KeyError:
            pass  # expected

    memgpt_user_id = uuid4()
    create_user(memgpt_user_id)

    agent_state = create_agent(user_id=memgpt_user_id)

    youbot_user = YoubotUser(
        name=human_name,
        memgpt_user_id=memgpt_user_id,
        phone=phone,
        memgpt_agent_id=agent_state.id,
    )  # type: ignore

    user_id = create_youbot_user(youbot_user)
    return get_youbot_user_by_id(user_id)


if __name__ == "__main__":
    pass
