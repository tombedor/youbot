from datetime import UTC, datetime
import json
import os
import re
from typing import List, Optional
from uuid import UUID
from attr import dataclass
from pydantic import field_validator
from sqlalchemy import NullPool, create_engine
from sqlmodel import SQLModel, Field
from memgpt.agent_store.storage import RecallMemoryModel, ArchivalMemoryModel


from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()



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


class AgentReminder(SQLModel, table=True):
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    youbot_user_id: int = Field(..., description="Youbot user whose assistant is being reminded")
    state: str = Field("pending", description="The state of the reminder")
    reminder_time_utc: datetime = Field(..., description="Time to remind the user")
    reminder_message: str = Field(..., description="Message to remind the agent with")


@dataclass
class RecallMessage:
    user_id: UUID
    content: str
    role: str
    time: datetime


class Store:
    def __init__(self) -> None:
        self.engine = create_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
        Base.metadata.create_all(
            self.engine,
            tables=[
                Signup.__table__,
                YoubotUser.__table__,
                SmsWebhookLog.__table__,
                AgentReminder.__table__,
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

    def get_youbot_user_by_agent_id(self, agent_id: UUID) -> YoubotUser:
        with self.session_maker() as session:
            user = session.query(YoubotUser).filter_by(memgpt_agent_id=agent_id).first()
            if user:
                return user
            else:
                raise KeyError(f"User with agent id {agent_id} not found")

    def create_agent_reminder(self, youbot_user_id: int, reminder_time_utc: datetime, reminder_message: str) -> None:
        with self.session_maker() as session:
            reminder = AgentReminder(youbot_user_id=youbot_user_id, reminder_time_utc=reminder_time_utc, reminder_message=reminder_message)  # type: ignore
            session.add(reminder)
            session.commit()

    def create_sms_webhook_log(self, source: str, msg: str) -> None:
        with self.session_maker() as session:
            webhook_log = SmsWebhookLog(source=source, info=msg)  # type: ignore
            session.add(webhook_log)
            session.commit()

    # all pending state reminders where the reminder time is in the past
    def get_pending_reminders(self) -> List[AgentReminder]:
        with self.session_maker() as session:
            reminders = (
                session.query(AgentReminder)
                .filter(AgentReminder.state == "pending", AgentReminder.reminder_time_utc < datetime.now(UTC)) # type: ignore
                .all()
            )
        return reminders

    def update_reminder_state(self, reminder_id: int, new_state: str) -> None:
        with self.session_maker() as session:
            reminder = session.query(AgentReminder).filter_by(id=reminder_id).first()
            assert reminder
            reminder.state = new_state
            session.commit()

    def get_youbot_user_by_discord(self, discord_member_id: str) -> YoubotUser:
        with self.session_maker() as session:
            user = session.query(YoubotUser).filter_by(discord_member_id=discord_member_id).first()
        if user:
            return user
        else:
            raise KeyError(f"User with discord member id {discord_member_id} not found")

    def get_youbot_user_by_id(self, user_id: int) -> YoubotUser:
        with self.session_maker() as session:
            user = session.query(YoubotUser).filter_by(id=user_id).first()
        if user:
            return user
        else:
            raise KeyError(f"User with id {user_id} not found")

    def get_archival_messages(self, limit=None) -> List[str]:
        with self.session_maker() as session:
            raw_messages = session.query(ArchivalMemoryModel).limit(limit).all()
        return [msg.text for msg in raw_messages]

    def get_memgpt_recall(self, limit=None) -> List[RecallMessage]:
        with self.session_maker() as session:
            # raw messages ordered by created_at
            raw_messages = session.query(RecallMemoryModel).order_by(RecallMemoryModel.c.created_at).limit(limit).all()

        skipped = 0
        cleaned_messages = []
        for msg in raw_messages:
            text = msg.text

            if not msg.text:
                continue

            bad_strings = [
                '"type": "heartbeat"',
                '"status": "OK"',
                "Bootup sequence complete",
                '"type": "login"',
                "You are MemGPT, the latest version of Limnal Corporation",
                "This is an automated system message hidden from the user",
                "This is placeholder text",
                "have been hidden from view due to conversation memory constraints",
            ]
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
                text = json.loads(text)["message"]
            except json.JSONDecodeError:
                text = msg.text

            cleaned_messages.append(RecallMessage(role=role, content=text, user_id=msg.user_id, time=msg.created_at))
        return cleaned_messages
