from re import M
from typing import Optional
from uuid import UUID, uuid4
from youbot.memgpt_client import PERSONA, MemGPTClient
from youbot.store import Store
from youbot.persistence.youbot_user import YoubotUser


def onboard_user(
    email: str, human_name: str, human_description: str, discord_member_id: Optional[str], phone_number: Optional[str]
) -> None:
    store = Store()
    existing_user = store.get_user_by_email(email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")

    memgpt_user_id = uuid4()
    MemGPTClient.create_user(memgpt_user_id)

    MemGPTClient.create_human(user_id=memgpt_user_id, human_text=human_description, human_name=human_name)
    MemGPTClient.create_persona(user_id=memgpt_user_id)
    MemGPTClient.create_preset(user_id=memgpt_user_id, human_text=human_description, persona_text=PERSONA)
    agent_state = MemGPTClient.create_agent(user_id=memgpt_user_id, human_name=human_name, preset_name="youbot", persona_name="youbot")

    youbot_user = YoubotUser(
        id=memgpt_user_id,
        memgpt_user_id=memgpt_user_id,
        email=email,
        discord_member_id=discord_member_id,
        phone_number=phone_number,
        human_description=human_description,
        memgpt_agent_id=agent_state.id,
    )

    store.create_user(youbot_user)


if __name__ == "__main__":
    onboard_user(
        email="tombedor@gmail.com",
        discord_member_id="424672110288437250",
        human_description=" Name: Tom Bedor. Software Engineer. Capable of editing code. Dogs Elroy and Rocky. Fiance Justina.",
        human_name="tombedor",
        phone_number="7634398856",
    )
