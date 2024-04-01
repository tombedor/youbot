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
from youbot.persistence.store import Store

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
AGENT_NAME = "youbot"

intents = discord.Intents.default()
intents.message_content = True

discord_client = discord.Client(intents=intents)
store = Store()


@discord_client.event
async def on_ready() -> None:
    print(f"We have logged in as {discord_client.user}")


@discord_client.event
async def on_message(message) -> None:
    logging.info(message)
    if message.author == discord_client.user:
        return

    logging.info(message.author.id)

    youbot_user = store.get_youbot_user(discord_member_id=str(message.author.id))
    if youbot_user is None:
        logging.warn(f"no memgpt user found for discord member {str(message.author)}")
    else:
        reply = MemGPTClient.user_message_new(agent_id=youbot_user.memgpt_agent_id, user_id=youbot_user.memgpt_user_id, msg=message.content)
        await message.channel.send(reply)


if __name__ == "__main__":
    discord_client.run(DISCORD_TOKEN)
