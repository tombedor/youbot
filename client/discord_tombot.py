# This example requires the 'message_content' intent.

import os
import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    print(message)
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    else:
        print('not responding')
        
        
import os
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, insert
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

def setup_discord_users_table():
    # Get the Postgres URL from the environment variable
    postgres_url = os.getenv('POSTGRES_URL')

    # Create an engine that will interface with the Postgres database
    engine = create_engine(postgres_url)

    # Create a metadata instance
    metadata = MetaData()

    # Define the discord_users table
    discord_users = Table('discord_users', metadata,
                          Column('discord_member_id', Integer, primary_key=True),
                          Column('memgpt_user_id', UUID)
                          )

    # Create the table
    metadata.create_all(engine)

    return discord_users

def add_user(discord_member_id, memgpt_user_id, discord_users, engine):
    # Insert a new user into the discord_users table
    stmt = insert(discord_users).values(discord_member_id=discord_member_id, memgpt_user_id=memgpt_user_id)

    # Execute the statement
    with engine.connect() as connection:
        result = connection.execute(stmt)

    return result.inserted_primary_key


client.run(os.getenv('DISCORD_TOKEN'))
