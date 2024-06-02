from datetime import UTC, datetime
import re
from typing import Optional
from uuid import UUID
from pydantic import field_validator
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field


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


class GoogleToken(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    youbot_user_id: int = Field(..., description="Youbot user whose assistant is being reminded")
    access_token: str = Field(..., description="The access token")
    refresh_token: str = Field(..., description="The refresh token")
    expires_at: datetime = Field(..., description="The time the token expires")
    UniqueConstraint("youbot_user_id")
