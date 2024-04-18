import os
from youbot import DATABASE_URL, ROOT_DIR

from sqlalchemy import UUID, Column, Integer, MetaData, NullPool, String, Table, create_engine
from celery import Celery


def init():
    os.path.join(ROOT_DIR, ".secrets")

    # optional env vars
    os.getenv("YOUBOT_GOOGLE_CREDS_PATH")
    # This is understood to be the Google email of *the agent* (not the user)
    # The agent sends emails and creates events, *inviting the user to them*
    # Obviously not a privacy-friendly design, just a placeholder.
    os.getenv("YOUBOT_GOOGLE_EMAIL")
    os.getenv("YOUBOT_GOOGLE_CREDS_PATH")

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
        Column("phone", String, unique=True),
        Column("discord_username", String, unique=True),
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
