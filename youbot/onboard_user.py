from typing import Optional
from uuid import uuid4
from youbot.data_models import YoubotUser
from youbot.clients.memgpt_client import create_agent, create_human, create_persona, create_preset, create_user
from youbot.store import create_youbot_user, get_youbot_user_by_phone


def onboard_user(phone: str, human_name: str, human_description: str, discord_member_id: Optional[str] = None) -> None:
    try:
        existing_user = get_youbot_user_by_phone(phone)
        if existing_user:
            raise ValueError(f"User with phone {phone} already exists")
    except KeyError:
        pass  # expteded

    memgpt_user_id = uuid4()
    create_user(memgpt_user_id)

    create_human(user_id=memgpt_user_id, human_text=human_description, human_name=human_name)
    create_persona(user_id=memgpt_user_id)
    create_preset(user_id=memgpt_user_id, human_text=human_description)
    agent_state = create_agent(user_id=memgpt_user_id, human_name=human_name)

    youbot_user = YoubotUser(
        name=human_name,
        memgpt_user_id=memgpt_user_id,
        discord_member_id=discord_member_id,
        phone=phone,
        human_description=human_description,
        memgpt_agent_id=agent_state.id,
    )  # type: ignore

    create_youbot_user(youbot_user)


if __name__ == "__main__":
    pass
