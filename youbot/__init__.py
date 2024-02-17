import os
from celery import Celery
from dotenv import load_dotenv
from llama_index import ServiceContext
import llama_index
from sqlalchemy import UUID, Column, MetaData, NullPool, String, Table, create_engine
import yaml

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMGPT_CONFIG_FILE = os.path.join(ROOT_DIR, "config", "memgpt_config.yaml")
with open(os.path.join(ROOT_DIR, "config", "agents.yaml"), "r") as file:
    AGENTS_CONFIG = yaml.safe_load(file.read())


for env_var in [
    "OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "POSTGRES_URL",
    "YOUBOT_GOOGLE_EMAIL",
    "YOUBOT_GOOGLE_CREDS_PATH",
]:
    if os.getenv(env_var) is None:
        raise KeyError(f"missing required env var: {env_var}")

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
POSTGRES_URL = os.environ["POSTGRES_URL"]

# This is understood to be the Google email of *the agent* (not the user)
# The agent sends emails and creates events, *inviting the user to them*
# Obviously not a privacy-friendly design, just a placeholder.
GOOGLE_EMAIL = os.getenv("YOUBOT_GOOGLE_EMAIL")
GOOGLE_CREDS_PATH = os.getenv("YOUBOT_GOOGLE_CREDS_PATH")


SECRETS_DIR = os.path.join(ROOT_DIR, ".secrets")

# Expose the config file to memgpt package
os.environ["MEMGPT_CONFIG_PATH"] = MEMGPT_CONFIG_FILE


service_context = ServiceContext.from_defaults()
service_context.llm.model = "gpt-4-0613"
llama_index.global_service_context = service_context

postgres_url = os.getenv("POSTGRES_URL")
ENGINE = create_engine(POSTGRES_URL, poolclass=NullPool)
metadata = MetaData()

GOOGLE_EMAILS = Table(
    "google_emails",
    metadata,
    Column("email", String, primary_key=True),
    Column("memgpt_user_id", UUID),
)

metadata.create_all(ENGINE)


def get_celery(queue: str) -> Celery:
    app = Celery(queue, broker="redis://localhost:6379/0")
    app.conf.update(
        task_serializer="pickle",
        accept_content=["pickle"],  # Ignore other content
        result_serializer="pickle",
    )
    return app
