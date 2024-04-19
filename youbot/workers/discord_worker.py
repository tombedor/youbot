import logging
import os
import discord
import os


from youbot.clients.memgpt_client import MemGPTClient
from youbot.clients.memgpt_client import MemGPTClient
from youbot.store import Store

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

    youbot_user = store.get_youbot_user_by_discord(discord_member_id=str(message.author.id))
    if youbot_user is None:
        logging.warning(f"no memgpt user found for discord member {str(message.author)}")
    else:
        reply = MemGPTClient.user_message(youbot_user=youbot_user, msg=message.content)
        await message.channel.send(reply)


if __name__ == "__main__":
    discord_client.run(DISCORD_TOKEN)
