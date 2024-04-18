from datetime import UTC, datetime
import re
from typing import Optional
from uuid import UUID
from pydantic import field_validator
from sqlalchemy import NullPool, create_engine
from sqlmodel import SQLModel, Field

from youbot import DATABASE_URL
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


# raw signup table from web
class Signup(SQLModel, table=True):
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    name: str = Field(..., description="The name of the user")
    discord_member_id: Optional[str] = Field(None, description="The discord member id for the user")
    phone_number: Optional[str] = Field(None, description="The phone number for the user")


class YoubotUser(SQLModel, table=True):
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    name: str = Field(..., description="The name of the user")
    memgpt_user_id: UUID = Field(..., description="The unique identifier for the user in the memgpt system")
    memgpt_agent_id: UUID = Field(..., description="The unique identifier for the user's agent in the memgpt system")
    discord_member_id: Optional[str] = Field(None, description="The discord member id for the user")
    phone_number: str = Field(str, description="The phone number for the user")
    human_description: str = Field(..., description="Text description of th user to be provided to the MemGPT agent")

    @field_validator("phone_number")
    def phone_is_e164(cls, phone_number: str) -> str:
        if not bool(re.match(r"^\+\d{1,15}$", phone_number)):
            raise ValueError("Invalid phone number format")
        return phone_number


class SmsWebhookLog(SQLModel, table=True):
    id: int = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    created_at: datetime = Field(default=datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    source: str = Field(..., description="Where the webhook came from")
    info: str = Field(..., description="The information from the webhook")


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

    def create_signup(self, name: str, phone_number: str, discord_member_id: Optional[str]) -> None:
        with self.session_maker() as session:
            session.add(Signup(name=name, phone_number=phone_number, discord_member_id=discord_member_id))  # type: ignore
            session.commit()

    def create_user(self, user: YoubotUser) -> None:
        with self.session_maker() as session:
            session.add(user)
            session.commit()

    def get_user_by_email(self, email: str) -> YoubotUser:
        with self.session_maker() as session:
            user = session.query(YoubotUser).filter(YoubotUser.email == email).first()
            assert user
            return user

    def create_sms_webhook_log(self, source: str, msg: str) -> None:
        with self.session_maker() as session:
            webhook_log = SmsWebhookLog(source=source, info=msg)  # type: ignore
            session.add(webhook_log)
            session.commit()

    def get_youbot_user(self, discord_member_id: str) -> YoubotUser:
        session = self.session_maker()
        user = session.query(YoubotUser).filter(YoubotUser.discord_member_id == discord_member_id).first()
        session.close()
        assert user
        return user


if __name__ == "__main__":
    store = Store()
