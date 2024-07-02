from time import sleep
from typing import List

from youbot.clients.google_client import _get_people_service, fetch_calendar_events, get_contact_info
from youbot.data_models import CalendarEvent, Fact
from youbot.clients.oauth_client import get_google_credentials
from youbot.prompts import date_to_string, summarize_calendar_text
from youbot.store import fetch_persisted_calendar_events, get_youbot_user_by_id, upsert_event_to_db
from youbot import CLI_USER_ID, cache
from toolz import curry, pipe
from toolz.curried import map

from youbot.util import Maybe, assert_type

GOOGLE_API_SLEEP_INTERVAL_SECONDS = 0.4

GOOGLE_CALENDAR_FETCH_INTERVAL_SECONDS = 60 * 30  # 30 minutes


def get_calendar_facts(youbot_user_id: int) -> List[Fact]:
    fetch_and_persist_calendar_events(youbot_user_id)
    return pipe(
        fetch_persisted_calendar_events(youbot_user_id),
        map(
            lambda event: pipe(
                event,
                get_raw_text_summary(youbot_user_id),
                assert_type(str),
                summarize_calendar_text,
                lambda summary: Fact(youbot_user_id=youbot_user_id, text=summary, timestamp=event.start),
            )
        ),
        list,
    )  # type: ignore


@curry
def get_raw_text_summary(youbot_user_id: int, event: CalendarEvent) -> str:
    assert type(event) == CalendarEvent
    attenddee_names_and_emails = []
    for attendee in event.attendee_emails:
        name = get_google_contact_name(attendee, youbot_user_id)
        if name:
            attenddee_names_and_emails.append("Name: " + name + ", Email: " + attendee)
        else:
            attenddee_names_and_emails.append("Email: " + attendee)

    return pipe(
        [
            "Event Summary: " + event.summary,
            "Event Description: " + event.description if event.description else None,
            "Start: " + date_to_string(event.start),
            "End: " + date_to_string(event.end),
            "Location: " + event.location if event.location else None,
            "Attendees: " + ", ".join(attenddee_names_and_emails) if len(attenddee_names_and_emails) > 0 else None,
            "Recurrence: " + ", ".join(event.recurrence) if event.recurrence else None,
        ],
        lambda x: filter(None, x),
        "\n\n".join,
    )  # type: ignore


@cache.cache()
def get_google_contact_name(email: str, youbot_user_id: int) -> Maybe[str]:
    sleep(GOOGLE_API_SLEEP_INTERVAL_SECONDS)

    google_creds = pipe(
        youbot_user_id,
        get_youbot_user_by_id,
        get_google_credentials,
    )

    assert type(google_creds) == Maybe

    return google_creds.map(_get_people_service).map(get_contact_info(email)).map(lambda info: info.get("name"))  # type: ignore


@cache.cache(ttl=GOOGLE_CALENDAR_FETCH_INTERVAL_SECONDS)
def fetch_and_persist_calendar_events(youbot_user_id: int) -> int:
    maybe_creds = pipe(
        youbot_user_id,
        get_youbot_user_by_id,
        get_google_credentials,
    )

    assert isinstance(maybe_creds, Maybe)

    return (
        maybe_creds.map(fetch_calendar_events(30))
        .map(lambda events: map(lambda event: upsert_event_to_db(youbot_user_id, event), events))
        .map(len)  # type: ignore
        .value
    )


if __name__ == "__main__":
    facts = get_calendar_facts(CLI_USER_ID)
