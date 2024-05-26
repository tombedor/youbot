from datetime import UTC, datetime
import json
import logging
import os
import re
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import field_validator
from sqlalchemy import NullPool, UniqueConstraint, create_engine
from sqlmodel import SQLModel, Field
from memgpt.agent_store.storage import RecallMemoryModel, ArchivalMemoryModel

from sqlalchemy.orm import sessionmaker, declarative_base


Base = declarative_base()

MAX_EMBEDDING_DIM = 4096  # maximum supported embeding size - do NOT change or else DBs will need to be reset


# raw signup table from web
class Signup(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    name: str = Field(..., description="The name of the user")
    discord_member_id: Optional[str] = Field(None, description="The discord member id for the user")
    phone: Optional[str] = Field(None, description="The phone number for the user")


class YoubotUser(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    name: str = Field(..., description="The name of the user")
    memgpt_user_id: UUID = Field(..., description="The unique identifier for the user in the memgpt system")
    memgpt_agent_id: UUID = Field(..., description="The unique identifier for the user's agent in the memgpt system")
    discord_member_id: Optional[str] = Field(None, description="The discord member id for the user")
    phone: str = Field(str, description="The phone number for the user")
    human_description: str = Field(..., description="Text description of th user to be provided to the MemGPT agent")

    @field_validator("phone")
    def phone_is_e164(cls, phone: str) -> str:
        if not bool(re.match(r"^\+\d{1,15}$", phone)):
            raise ValueError("Invalid phone number format")
        return phone


class SmsWebhookLog(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    source: str = Field(..., description="Where the webhook came from")
    info: str = Field(..., description="The information from the webhook")


class AgentReminder(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    youbot_user_id: int = Field(..., description="Youbot user whose assistant is being reminded")
    state: str = Field("pending", description="The state of the reminder")
    reminder_time_utc: datetime = Field(..., description="Time to remind the user")
    reminder_message: str = Field(..., description="Message to remind the agent with")


class MemroyEntity(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    youbot_user_id: int = Field(..., description="Youbot user whose assistant is being reminded")
    entity_name: str = Field(..., description="The name of the entity")
    entity_label: str = Field(..., description="The label of the entity")
    text: str = Field(..., description="The text of the entity")
    UniqueConstraint("youbot_user_id", "entity_name", "entity_label")
    # embedding = mapped_column(Vector(MAX_EMBEDDING_DIM))
    # embedding_dim: int = Field(..., description="The dimension of the embedding")
    # embedding_model: str = Field(..., description="The model used to generate the embedding")


ENGINE = create_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
Base.metadata.create_all(
    ENGINE,
    tables=[
        Signup.__table__,
        YoubotUser.__table__,
        SmsWebhookLog.__table__,
        AgentReminder.__table__,
        MemroyEntity.__table__,
    ],
)
SESSION_MAKER = sessionmaker(bind=ENGINE)


def create_signup(name: str, phone: str, discord_member_id: Optional[str]) -> None:
    with SESSION_MAKER() as session:
        session.add(Signup(name=name, phone=phone, discord_member_id=discord_member_id))  # type: ignore
        session.commit()


def create_youbot_user(user: YoubotUser) -> None:
    with SESSION_MAKER() as session:
        session.add(user)
        session.commit()


def get_youbot_user_by_phone(phone: str) -> YoubotUser:
    with SESSION_MAKER() as session:
        user = session.query(YoubotUser).filter_by(phone=phone).first()
        if user:
            return user
        else:
            raise KeyError(f"User with phone {phone} not found")


def get_youbot_user_by_agent_id(agent_id: UUID) -> YoubotUser:
    with SESSION_MAKER() as session:
        user = session.query(YoubotUser).filter_by(memgpt_agent_id=agent_id).first()
        if user:
            return user
        else:
            raise KeyError(f"User with agent id {agent_id} not found")


def create_agent_reminder(youbot_user_id: int, reminder_time_utc: datetime, reminder_message: str) -> None:
    with SESSION_MAKER() as session:
        reminder = AgentReminder(youbot_user_id=youbot_user_id, reminder_time_utc=reminder_time_utc, reminder_message=reminder_message)  # type: ignore
        session.add(reminder)
        session.commit()


def create_sms_webhook_log(source: str, msg: str) -> None:
    with SESSION_MAKER() as session:
        webhook_log = SmsWebhookLog(source=source, info=msg)  # type: ignore
        session.add(webhook_log)
        session.commit()


# all pending state reminders where the reminder time is in the past
def get_pending_reminders() -> List[AgentReminder]:
    with SESSION_MAKER() as session:
        reminders = (
            session.query(AgentReminder)
            .filter(AgentReminder.state == "pending", AgentReminder.reminder_time_utc < datetime.now(UTC))  # type: ignore
            .all()
        )
    return reminders


def update_reminder_state(reminder_id: int, new_state: str) -> None:
    with SESSION_MAKER() as session:
        reminder = session.query(AgentReminder).filter_by(id=reminder_id).first()
        assert reminder
        reminder.state = new_state
        session.commit()


def get_youbot_user_by_discord(discord_member_id: str) -> YoubotUser:
    with SESSION_MAKER() as session:
        user = session.query(YoubotUser).filter_by(discord_member_id=discord_member_id).first()
    if user:
        return user
    else:
        raise KeyError(f"User with discord member id {discord_member_id} not found")


def get_youbot_user_by_id(user_id: int) -> YoubotUser:
    with SESSION_MAKER() as session:
        user = session.query(YoubotUser).filter_by(id=user_id).first()
    if user:
        return user
    else:
        raise KeyError(f"User with id {user_id} not found")


def get_archival_messages(limit=None) -> List[ArchivalMemoryModel]:
    with SESSION_MAKER() as session:
        raw_messages = session.query(ArchivalMemoryModel).limit(limit).all()
    return raw_messages


def readable_message(msg) -> Optional[str]:
    if msg.role == "user":
        msg_text_d = json.loads(msg.text)
        if msg_text_d.get("type") in ["login", "heartbeat"]:
            return None
        else:
            return msg_text_d["message"]

    elif msg.role == "tool":
        return None
    elif msg.role == "assistant":
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.function["name"] == "send_message":
                    try:
                        return json.loads(tool_call.function["arguments"], strict=False)["message"]
                    except json.JSONDecodeError:
                        logging.warning("Could not decode JSON, returning raw response.")
                        return tool_call.function["arguments"]
        elif "system alert" in msg.text:
            pass
        else:
            logging.warning(f"Unexpected assistant message: {msg}")
            pass


def get_memgpt_recall(limit=None) -> List[Dict]:
    with SESSION_MAKER() as session:
        # raw messages ordered by created_at
        raw_messages = session.query(RecallMemoryModel).order_by(RecallMemoryModel.created_at).limit(limit).all()

    return [
        {"role": m.role, "time": m.created_at, "content": m.readable_message()} for m in raw_messages if not m.is_system_status_message()
    ]


def get_entity_name_text(youbot_user: YoubotUser, entity_name: str) -> Optional[str]:
    with SESSION_MAKER() as session:
        memory_entity = session.query(MemroyEntity).filter_by(youbot_user_id=youbot_user.id, entity_name=entity_name).first()
    if memory_entity:
        return memory_entity.text
    else:
        return None


def upsert_memory_entity(youbot_user_id: int, entity_name: str, entity_label: str, text: str) -> None:
    # embedding = OpenAIEmbedding(
    # api_base=MemGPTConfig.embedding_endpoint,  # type: ignore
    # api_key=os.environ["OPENAI_API_KEY"],
    # )

    # embedding = get_embedding(text)
    # embedding_dim = len(embedding)
    # embedding_model = MemGPTConfig.embedding_model_name

    # if exists, update
    with SESSION_MAKER() as session:
        memory_entity = (
            session.query(MemroyEntity).filter_by(youbot_user_id=youbot_user_id, entity_name=entity_name, entity_label=entity_label).first()
        )
        if memory_entity:
            session.query(MemroyEntity).filter_by(youbot_user_id=youbot_user_id, entity_name=entity_name, entity_label=entity_label).update(
                {"text": text}
            )
            session.commit()
            return
        else:
            memory_entity = MemroyEntity(youbot_user_id=youbot_user_id, entity_name=entity_name, entity_label=entity_label, text=text)  # type: ignore
            session.add(memory_entity)
            session.commit()


# def query_memory_entities(youbot_user_id: int, query_text: str) -> List[MemroyEntity]:
#     query_vec = get_embedding(query_text)
#     with SESSION_MAKER() as session:
#         memory_entities = session.query(MemroyEntity).filter_by(youbot_user_id=youbot_user_id, entity_label=entity_label).all()
#     return memory_entities
