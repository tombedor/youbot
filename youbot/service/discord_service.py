# This example requires the 'message_content' intent.

import logging
import os
import uuid
import discord
import os
from sqlalchemy import NullPool, create_engine, Table, Column, String, MetaData, insert
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from memgpt import MemGPT
from memgpt.data_types import User
from memgpt.metadata import MetadataStore

intents = discord.Intents.default()
intents.message_content = True

discord_client = discord.Client(intents=intents)
postgres_url = os.getenv('POSTGRES_URL')
engine = create_engine(postgres_url, poolclass=NullPool)
metadata = MetaData()

discord_users = Table('discord_users', metadata,
                        Column('discord_member_id', String, primary_key=True),
                        Column('memgpt_user_id', UUID)
                        )
metadata.create_all(engine)

memgpt_clients = {} # memgpt_user_id -> MemGPT
memgpt_agents_ids = {} # memgpt_user_id -> memgpt_agent_id

# Will need to make this dynamic
AGENT_IDS= {
    '00000000-0000-0000-0000-72001b73b3ea': uuid.UUID('c4a875b1-6e92-426a-befb-e5bb70ff6e29'), # tom
    '21e0c587-3582-49de-b306-c27d15fcc180': uuid.UUID('155f60de-bd23-4bfd-bcf2-117802af7bce') # justina
}

@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')

@discord_client.event
async def on_message(message):
    print(message)
    if message.author == discord_client.user:
        return
    
    print(message.author.id)
    memgpt_user_id = fetch_memgpt_user_id(message.author.id)
    if memgpt_user_id is None:
        logging.warn(f"no memgpt user found for discord member {str(message.author)}")
        memgpt_user_id = str(create_and_link_memgpt_user_id(message.author.id))
        
        
    global memgpt_clients
    global memgpt_agents_ids
        
    if memgpt_user_id not in memgpt_clients:
        memgpt_clients[memgpt_user_id] = MemGPT(auto_save=True, user_id=memgpt_user_id, debug=True)
        memgpt_client = memgpt_clients[memgpt_user_id]
    else:
        memgpt_client = memgpt_clients[memgpt_user_id]
        
    # if memgpt_user_id not in memgpt_agents_ids:
    #     agent_id = next(entry['id'] for entry in memgpt_client.list_agents()['agents'] if entry['name'] == 'tombot')
    #     if agent_id is None:
    #         memgpt_client.create_agent({'name': 'tombot'})
    #         logging.warn(f"no agent found for memgpt user {memgpt_user_id}")
    #         return
    #     memgpt_agents_ids[memgpt_user_id] = agent_id
        
    
    response_list = memgpt_client.user_message(AGENT_IDS[str(memgpt_user_id)], message.content)
    reply = next(r.get('assistant_message') for r in response_list if r.get('assistant_message'))
    await message.channel.send(reply)


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


def create_and_link_memgpt_user_id(discord_member_id: int) -> UUID:
    user = User()
    ms = MetadataStore()
    ms.create_user(user)
    memgpt_user_id = user.id
    with engine.connect() as connection:
        stmt = insert(discord_users).values(discord_member_id=str(discord_member_id), memgpt_user_id=memgpt_user_id)
        connection.execute(stmt)
        connection.commit()
    return memgpt_user_id
            

if __name__ == '__main__':
   discord_client.run(os.getenv('DISCORD_TOKEN'))

