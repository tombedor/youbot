from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel, Field


class YoubotUser(SQLModel, table=True):
    id: UUID = Field(..., description="The unique identifier for the user", primary_key=True, index=True)
    memgpt_user_id: UUID = Field(..., description="The unique identifier for the user in the memgpt system")
    email: str = Field(..., description="The email address for the user")
    memgpt_agent_id: UUID = Field(..., description="The unique identifier for the user's agent in the memgpt system")
    discord_member_id: Optional[str] = Field(None, description="The discord member id for the user")
    phone_number: Optional[str] = Field(None, description="The phone number for the user")
    human_description: str = Field(..., description="Text description of th user to be provided to the MemGPT agent")
