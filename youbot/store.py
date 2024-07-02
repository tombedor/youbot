from datetime import UTC, datetime, timedelta
import logging
import os
from typing import Any, Callable, List, Optional, Tuple

from sqlalchemy import NullPool, create_engine
from memgpt.agent_store.storage import ArchivalMemoryModel
from toolz import curry


from sqlalchemy.orm import sessionmaker, declarative_base

from youbot.data_models import AgentReminder, CalendarEvent, CalendarEventDB, MemoryEntity, Signup, SmsWebhookLog, YoubotUser, Entity
from youbot.util import Maybe


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
        MemoryEntity.__table__,
        CalendarEventDB.__table__,
    ],
)
SESSION_MAKER = sessionmaker(bind=ENGINE)


def query_youbot_user_by_field_fn(field_name: str) -> Callable[..., YoubotUser]:
    def wrapper(value: Any) -> YoubotUser:
        with SESSION_MAKER() as session:
            user = session.query(YoubotUser).filter(getattr(YoubotUser, field_name) == value).first()
            if not user:
                raise KeyError(f"User with {field_name} {value} not found")
            else:
                return user

    return wrapper


get_youbot_user_by_email = query_youbot_user_by_field_fn("email")

get_youbot_user_by_agent_id = query_youbot_user_by_field_fn("memgpt_agent_id")

get_youbot_user_by_phone = query_youbot_user_by_field_fn("phone")

get_youbot_user_by_id = query_youbot_user_by_field_fn("id")

get_youbot_user_by_name = query_youbot_user_by_field_fn("name")


def maybe_user_by_field_fn(field_name: str) -> Callable[..., Maybe[YoubotUser]]:
    def wrapper(value: Any) -> Maybe[YoubotUser]:
        with SESSION_MAKER() as session:
            return Maybe(session.query(YoubotUser).filter(getattr(YoubotUser, field_name) == value).first())

    return wrapper


maybe_youbot_user_by_id = maybe_user_by_field_fn("id")


def create_signup(name: str, phone: str, email: Optional[str]) -> None:
    with SESSION_MAKER() as session:
        session.add(Signup(name=name, phone=phone, email=email))  # type: ignore
        session.commit()


def create_youbot_user(user: YoubotUser) -> int:
    with SESSION_MAKER() as session:
        session.add(user)
        session.commit()
        return user.id


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


def get_archival_messages(youbot_user_id: int, limit=None) -> List[ArchivalMemoryModel]:
    youbot_user = get_youbot_user_by_id(youbot_user_id)
    with SESSION_MAKER() as session:
        raw_messages = session.query(ArchivalMemoryModel).filter_by(user_id=youbot_user.memgpt_user_id).limit(limit).all()
    return raw_messages


@curry
def get_entity_name_summary(youbot_user_id: int, entity_name: str, entity_label: str) -> Optional[str]:
    with SESSION_MAKER() as session:
        memory_entity = (
            session.query(MemoryEntity).filter_by(youbot_user_id=youbot_user_id, entity_name=entity_name, entity_label=entity_label).first()
        )
    if memory_entity:
        return memory_entity.text
    else:
        return None


def get_entity_name_label_texts(youbot_user_id: int) -> List[Tuple[str, str, str]]:
    with SESSION_MAKER() as session:
        rows = session.query(MemoryEntity).filter_by(youbot_user_id=youbot_user_id).all()
    return [(row.entity_name, row.entity_label, row.text) for row in rows]


@curry
def upsert_memory_entity(youbot_user_id: int, entity: Entity) -> None:
    logging.info(f"Upserting entity: {entity.entity_name} {entity.entity_label.name}")
    # if exists, update
    with SESSION_MAKER() as session:
        memory_entity = (
            session.query(MemoryEntity)
            .filter_by(youbot_user_id=youbot_user_id, entity_name=entity.entity_name, entity_label=entity.entity_label.name)
            .first()
        )
        if memory_entity:
            session.query(MemoryEntity).filter_by(
                youbot_user_id=youbot_user_id, entity_name=entity.entity_name, entity_label=entity.entity_label.name
            ).update({"text": entity.summary})
            session.commit()
            return
        else:
            memory_entity = MemoryEntity(youbot_user_id=youbot_user_id, entity_name=entity.entity_name, entity_label=entity.entity_label.name, text=entity.summary)  # type: ignore
            session.add(memory_entity)
            session.commit()


def fetch_persisted_calendar_events(youbot_user_id: int) -> List[CalendarEvent]:
    with SESSION_MAKER() as session:
        events = session.query(CalendarEventDB).filter_by(youbot_user_id=youbot_user_id).all()
    return [
        CalendarEvent(
            event_id=event.event_id,
            summary=event.summary,
            description=event.description,
            start=event.start,
            end=event.end,
            location=event.location,
            attendee_emails=event.attendee_emails.split(",") if event.attendee_emails else [],
            recurrence=event.recurrence.split(",") if event.recurrence else [],
            reminders=event.reminders,
            visibility=event.visibility,
        )
        for event in events
    ]


def get_recent_and_soon_events(youbot_user_id: int) -> List[CalendarEvent]:
    """Gets events for preceding 12 hours to following 12 hours."""
    with SESSION_MAKER() as session:
        db_events = session.query(CalendarEventDB).filter_by(youbot_user_id=youbot_user_id).filter(CalendarEventDB.start >= datetime.now() - timedelta(hours=12)).filter(CalendarEventDB.end <= datetime.now() + timedelta(hours=12)).all()  # type: ignore
    return [
        CalendarEvent(
            event_id=event.event_id,
            summary=event.summary,
            description=event.description,
            start=event.start,
            end=event.end,
            location=event.location,
            attendee_emails=event.attendee_emails.split(",") if event.attendee_emails else [],
            recurrence=event.recurrence.split(",") if event.recurrence else [],
            reminders=event.reminders,
            visibility=event.visibility,
        )
        for event in db_events
    ]


def upsert_event_to_db(youbot_user_id: int, event: CalendarEvent):
    with SESSION_MAKER() as session:
        persisted_event = session.query(CalendarEventDB).filter_by(event_id=event.event_id, youbot_user_id=youbot_user_id).first()
        if persisted_event:
            session.query(CalendarEventDB).filter_by(event_id=event.event_id, youbot_user_id=youbot_user_id).update(
                {
                    "summary": event.summary,
                    "description": event.description,
                    "start": event.start,
                    "end": event.end,
                    "location": event.location,
                    "attendee_emails": ",".join(event.attendee_emails) if event.attendee_emails else "",
                    "recurrence": ",".join(event.recurrence) if event.recurrence else "",
                    "reminders": event.reminders,
                    "visibility": event.visibility,
                }
            )
            session.commit()
            return
        else:
            persisted_event = CalendarEventDB(
                youbot_user_id=youbot_user_id,
                event_id=event.event_id,
                summary=event.summary,
                description=event.description,
                start=event.start,
                end=event.end,
                location=event.location,
                attendee_emails=event.attendee_emails,
                recurrence=event.recurrence,
                reminders=event.reminders,
                visibility=event.visibility,
            )  # type: ignore
            session.add(persisted_event)
            session.commit()
