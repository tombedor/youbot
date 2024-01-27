# This example requires the 'message_content' intent.

import logging
import os
import discord
import os
from sqlalchemy import create_engine, Table, Column, String, MetaData, insert
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from memgpt import MemGPT
from memgpt.config import MemGPTConfig

intents = discord.Intents.default()
intents.message_content = True

discord_client = discord.Client(intents=intents)
postgres_url = os.getenv('POSTGRES_URL')
engine = create_engine(postgres_url)
metadata = MetaData()

discord_users = Table('discord_users', metadata,
                        Column('discord_member_id', String, primary_key=True),
                        Column('memgpt_user_id', UUID)
                        )
metadata.create_all(engine)

memgpt_client = MemGPT(auto_save=True, config=MemGPTConfig.load())

@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')

@discord_client.event
async def on_message(message):
    print(message)
    if message.author == discord_client.user:
        return
    
    memgpt_id = fetch_memgpt_user_id(message.author.id)
    if memgpt_id is None:
        logging.warn(f"no memgpt user found for discord member {str(message.author)}")

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
        

def fetch_memgpt_user_id(discord_member_id: int) -> str:
    """gets or creates memgpt user for the specified id

    Args:
        discord_member_id (int): discord member id

    Returns:
        str: memgpt uuid for uuser
    """

    # fetch memgpt user id from users table, if it exists
    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT memgpt_user_id FROM discord_users WHERE discord_member_id = '{str(discord_member_id)}'"))
        row = result.fetchone()
        if row is not None:
            return row[0]
            
        else:
            return None


def insert_memgpt_user_id(discord_member_id: int, memgpt_user_id: str):
    with engine.connect() as connection:
        stmt = insert(discord_users).values(discord_member_id=str(discord_member_id), memgpt_user_id=memgpt_user_id)
        connection.execute(stmt)
        connection.commit()
            

if __name__ == '__main__':
    discord_client.run(os.getenv('DISCORD_TOKEN'))

