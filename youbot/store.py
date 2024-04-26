from datetime import UTC, datetime
import json
import re
from typing import List, Optional
from uuid import UUID
from attr import dataclass
from pydantic import field_validator
from sqlalchemy import NullPool, create_engine
from sqlmodel import SQLModel, Field
from memgpt.agent_store.db import get_db_model
from memgpt.agent_store.storage import TableType, RECALL_TABLE_NAME, ARCHIVAL_TABLE_NAME


from youbot import DATABASE_URL
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

MEMGPT_RECALL_TABLE = get_db_model(RECALL_TABLE_NAME, TableType.RECALL_MEMORY).__table__  # type: ignore
MEMGPT_ARCHIVAL_TABLE = get_db_model(ARCHIVAL_TABLE_NAME, TableType.ARCHIVAL_MEMORY).__table__  # type: ignore


# raw signup table from web
class Signup(SQLModel, table=True):
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    name: str = Field(..., description="The name of the user")
    discord_member_id: Optional[str] = Field(None, description="The discord member id for the user")
    phone: Optional[str] = Field(None, description="The phone number for the user")


class YoubotUser(SQLModel, table=True):
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
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    source: str = Field(..., description="Where the webhook came from")
    info: str = Field(..., description="The information from the webhook")


@dataclass
class RecallMessage:
    user_id: UUID
    content: str
    role: str
    time: datetime


class Store:
    def __init__(self) -> None:
        self.engine = create_engine(DATABASE_URL, poolclass=NullPool)
        Base.metadata.create_all(
            self.engine,
            tables=[
                Signup.__table__,
                YoubotUser.__table__,
                SmsWebhookLog.__table__,
            ],
        )
        self.session_maker = sessionmaker(bind=self.engine)

    def create_signup(self, name: str, phone: str, discord_member_id: Optional[str]) -> None:
        with self.session_maker() as session:
            session.add(Signup(name=name, phone=phone, discord_member_id=discord_member_id))  # type: ignore
            session.commit()

    def create_youbot_user(self, user: YoubotUser) -> None:
        with self.session_maker() as session:
            session.add(user)
            session.commit()

    def get_youbot_user_by_phone(self, phone: str) -> YoubotUser:
        with self.session_maker() as session:
            user = session.query(YoubotUser).filter_by(phone=phone).first()
            if user:
                return user
            else:
                raise KeyError(f"User with phone {phone} not found")

    def create_sms_webhook_log(self, source: str, msg: str) -> None:
        with self.session_maker() as session:
            webhook_log = SmsWebhookLog(source=source, info=msg)  # type: ignore
            session.add(webhook_log)
            session.commit()

    def get_youbot_user_by_discord(self, discord_member_id: str) -> YoubotUser:
        with self.session_maker() as session:
            user = session.query(YoubotUser).filter_by(discord_member_id=discord_member_id).first()
        if user:
            return user
        else:
            raise KeyError(f"User with discord member id {discord_member_id} not found")
        
    def get_archival_messages(self, limit=None) -> List[str]:
        with self.session_maker() as session:
            raw_messages = session.query(MEMGPT_ARCHIVAL_TABLE).limit(limit).all()
        return [msg.text for msg in raw_messages]

    def get_memgpt_recall(self, limit=None) -> List[RecallMessage]:
        with self.session_maker() as session:
            # raw messages ordered by created_at
            raw_messages = session.query(MEMGPT_RECALL_TABLE).order_by(MEMGPT_RECALL_TABLE.c.created_at).limit(limit).all()

        skipped = 0
        cleaned_messages = []
        for msg in raw_messages:
            text = msg.text

            if not msg.text:
                continue

            bad_strings = ['"type": "heartbeat"', '"status": "OK"', "Bootup sequence complete", '"type": "login"', "You are MemGPT, the latest version of Limnal Corporation", "This is an automated system message hidden from the user", 'This is placeholder text', 'have been hidden from view due to conversation memory constraints']
            if any(bad_string in text for bad_string in bad_strings):
                skipped += 1
                continue

            if msg.role in ["system", "tool"] or '{"type": "login",' in msg.text:
                role = "system"
            elif msg.role == "user":
                role = "user"
            elif msg.role == "assistant":
                role = "assistant"
            else:
                raise ValueError(f"Unknown role: {msg.role}")
            text = msg.text

            # check if text is actually a json object
            try:
                text = json.loads(text)['message']
            except json.JSONDecodeError:
                text = msg.text

            cleaned_messages.append(RecallMessage(role=role, content=text, user_id=msg.user_id, time=msg.created_at))
        return cleaned_messages
