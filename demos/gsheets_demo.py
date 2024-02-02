import logging
from uuid import UUID
from memgpt import MemGPT
from memgpt.agent import Agent
from memgpt.metadata import MetadataStore
from sqlalchemy import text
from memgpt.agent_store.db import get_db_model, PostgresStorageConnector
from memgpt.agent_store.storage import TableType, RECALL_TABLE_NAME, ARCHIVAL_TABLE_NAME

client = MemGPT()

agent_id = next(entry['id'] for entry in client.list_agents()['agents'] if entry['name'] == 'testbot')
agent_state = client.server.get_agent(agent_id=agent_id,user_id=client.user_id)

agent = Agent(agent_state=agent_state,interface=client.interface)

# TODO: add functions and demonstrate.


def todo(self):
    pass