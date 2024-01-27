from memgpt import MemGPT
from memgpt.config import MemGPTConfig
from memgpt.data_types import User, AgentState
from memgpt.metadata import MetadataStore
from copy import deepcopy
import os
import discord

memgpt_client = MemGPT(config=vars(MemGPTConfig.load()))


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
    
    tombot_id = next(a['name'] for a in memgpt_client.list_agents()['agents'] if a['name'] == 'tombot')
    response = memgpt_client.user_message(

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    else:
        print('not responding')



client.run(os.getenv('DISCORD_TOKEN'))

