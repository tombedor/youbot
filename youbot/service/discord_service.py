# This example requires the 'message_content' intent.

import logging
import os
from typing import Optional
import uuid
import discord
import os
from sqlalchemy import insert
from sqlalchemy.sql import text
from youbot import DISCORD_USERS, ENGINE


from youbot.memgpt_client import MemGPTClient
from youbot.memgpt_client import MemGPTClient

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
AGENT_NAME = "youbot"

intents = discord.Intents.default()
intents.message_content = True

discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_ready() -> None:
    print(f"We have logged in as {discord_client.user}")


@discord_client.event
async def on_message(message) -> None:
    logging.info(message)
    if message.author == discord_client.user:
        return

    logging.info(message.author.id)
    memgpt_user_id = fetch_memgpt_user_id(message.author.id)
    if memgpt_user_id is None:
        logging.warn(f"no memgpt user found for discord member {str(message.author)}")
        memgpt_user_id = create_and_link_memgpt_user_id(message.author.id)

    reply = MemGPTClient.user_message(agent_name=AGENT_NAME, msg=message.content, user_id=memgpt_user_id)

    await message.channel.send(reply)


def fetch_memgpt_user_id(discord_member_id: int) -> Optional[uuid.UUID]:
    """gets or creates memgpt user for the specified id

    Args:
        discord_member_id (int): discord member id

    Returns:
        str: memgpt uuid for uuser
    """

    # fetch memgpt user id from users table, if it exists
    with ENGINE.connect() as connection:
        result = connection.execute(text(f"SELECT memgpt_user_id FROM discord_users WHERE discord_member_id = '{str(discord_member_id)}'"))
        row = result.fetchone()
        if row is not None:
            return row[0]

        else:
            return None


def create_and_link_memgpt_user_id(discord_member_id: int) -> uuid.UUID:
    memgpt_user_id = uuid.UUID(int=discord_member_id)
    MemGPTClient.create_user(memgpt_user_id)
    with ENGINE.connect() as connection:
        stmt = insert(DISCORD_USERS).values(discord_member_id=str(discord_member_id), memgpt_user_id=memgpt_user_id)
        connection.execute(stmt)
        connection.commit()
    assert isinstance(memgpt_user_id, uuid.UUID)
    return memgpt_user_id


if __name__ == "__main__":
    discord_client.run(DISCORD_TOKEN)
