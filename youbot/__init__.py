import os
from celery import Celery
from dotenv import load_dotenv
from sqlalchemy import UUID, Column, Integer, MetaData, NullPool, String, Table, create_engine
import yaml
from memgpt.config import MemGPTConfig
import logging
import sys

load_dotenv()

# Expose memgpt config to MemGPT
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(ROOT_DIR, "storage")

os.environ['USER_FUNCTIONS_DIR'] = os.path.join(ROOT_DIR, 'memgpt_extensions', 'functions')

def log_to_stdout():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

os.environ["MEMGPT_CONFIG_PATH"] = os.path.join(ROOT_DIR, "config", "memgpt_config")
MEMGPT_CONFIG = MemGPTConfig.load()
with open(os.path.join(ROOT_DIR, "config", "agents.yaml"), "r") as file:
    AGENTS_CONFIG = yaml.safe_load(file.read())

SECRETS_DIR = os.path.join(ROOT_DIR, ".secrets")

# required env vars
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

# optional env vars
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GOOGLE_CREDS_PATH = os.getenv("YOUBOT_GOOGLE_CREDS_PATH")
# This is understood to be the Google email of *the agent* (not the user)
# The agent sends emails and creates events, *inviting the user to them*
# Obviously not a privacy-friendly design, just a placeholder.
GOOGLE_EMAIL = os.getenv("YOUBOT_GOOGLE_EMAIL")
GOOGLE_CREDS_PATH = os.getenv("YOUBOT_GOOGLE_CREDS_PATH")

# Set up db tables
ENGINE = create_engine(DATABASE_URL, poolclass=NullPool)
metadata = MetaData()

GOOGLE_EMAILS = Table(
    "google_emails",
    metadata,
    Column("email", String, primary_key=True),
    Column("memgpt_user_id", UUID),
)

DISCORD_USERS = Table(
    "discord_users",
    metadata,
    Column("discord_member_id", String, primary_key=True),
    Column("memgpt_user_id", UUID),
)

SIGNUPS = Table(
    "signups",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("phone_number", String, unique=True),
    Column("discord_username", String, unique=True)
)

metadata.create_all(ENGINE)


# job queue
def get_celery(queue: str) -> Celery:
    app = Celery(queue, broker="redis://localhost:6379/0")
    app.conf.update(
        task_serializer="pickle",
        accept_content=["pickle"],  # Ignore other content
        result_serializer="pickle",
    )
    return app


# accessors for MEMGPT classes
