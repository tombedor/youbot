from datetime import UTC, datetime
import json
import os
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy import NullPool, create_engine
from memgpt.agent_store.storage import RecallMemoryModel, ArchivalMemoryModel

from sqlalchemy.orm import sessionmaker, declarative_base

from youbot.data_models import AgentReminder, MemroyEntity, Signup, SmsWebhookLog, YoubotUser


Base = declarative_base()

MAX_EMBEDDING_DIM = 4096  # maximum supported embeding size - do NOT change or else DBs will need to be reset


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


def get_archival_messages(youbot_user: YoubotUser, limit=None) -> List[ArchivalMemoryModel]:
    with SESSION_MAKER() as session:
        raw_messages = session.query(ArchivalMemoryModel).filter_by(user_id=youbot_user.memgpt_user_id).limit(limit).all()
    return raw_messages


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


def upsert_memory_entity(youbot_user: YoubotUser, entity_name: str, entity_label: str, text: str) -> None:
    # if exists, update
    with SESSION_MAKER() as session:
        memory_entity = (
            session.query(MemroyEntity).filter_by(youbot_user_id=youbot_user.id, entity_name=entity_name, entity_label=entity_label).first()
        )
        if memory_entity:
            session.query(MemroyEntity).filter_by(youbot_user_id=youbot_user.id, entity_name=entity_name, entity_label=entity_label).update(
                {"text": text}
            )
            session.commit()
            return
        else:
            memory_entity = MemroyEntity(youbot_user_id=youbot_user_id, entity_name=entity_name, entity_label=entity_label, text=text)  # type: ignore
            session.add(memory_entity)
            session.commit()
