import logging
from time import sleep
import time
from typing import List, Optional

from tqdm import tqdm
from youbot.clients.google_client import fetch_calendar_events, get_contact_info
from youbot.clients.llm_client import query_llm
from youbot.data_models import YoubotUser, Fact
from youbot.oath_util import get_google_credentials
from youbot.prompts import CALENDAR_SUMMARIZER_SYSTEM_PROMPT, DATETIME_FORMATTER
from youbot.store import fetch_persisted_calendar_events, get_youbot_user_by_id, upsert_event_to_db
from youbot import cache

GOOGLE_API_SLEEP_INTERVAL_SECONDS = 0.4

GOOGLE_CALENDAR_FETCH_INTERVAL_SECONDS = 60 * 30  # 30 minutes


@cache.cache(ttl=GOOGLE_CALENDAR_FETCH_INTERVAL_SECONDS)
def cached_fetch_calendar_events(youbot_user_id: int) -> int:
    youbot_user = get_youbot_user_by_id(youbot_user_id)
    logging.info("Fetching calendar events for user: %s", youbot_user.id)
    fetch_and_persist_calendar_events(youbot_user)
    return int(time.time())


def get_calendar_facts(youbot_user: YoubotUser) -> List[Fact]:
    cached_fetch_calendar_events(youbot_user.id)
    facts = []
    for event in tqdm(fetch_persisted_calendar_events(youbot_user)):
        attenddee_names_and_emails = []
        for attendee in event.attendee_emails:
            name = get_google_contact_name(attendee, youbot_user.id)
            if name:
                attenddee_names_and_emails.append("Name: " + name + ", Email: " + attendee)
            else:
                attenddee_names_and_emails.append("Email: " + attendee)

        event_str_list = ["Event Summary: " + event.summary]
        if event.description:
            event_str_list.append("Event Description: " + event.description)
        event_str_list.append("Start: " + event.start.strftime(DATETIME_FORMATTER))
        event_str_list.append("End: " + event.end.strftime(DATETIME_FORMATTER))
        if event.location:
            event_str_list.append("Location: " + event.location)
        if len(attenddee_names_and_emails) > 0:
            event_str_list.append("Attendees: " + ", ".join(attenddee_names_and_emails))
        if event.recurrence:
            event_str_list.append("Recurrence: " + ", ".join(event.recurrence))

        raw_event_summary = "\n".join(event_str_list)
        summary = query_llm(prompt=raw_event_summary, system=CALENDAR_SUMMARIZER_SYSTEM_PROMPT)

        fact = Fact(text=summary, timestamp=event.start)
        facts.append(fact)
    return facts


@cache.cache()
def get_google_contact_name(email: str, youbot_user_id: int) -> Optional[str]:
    sleep(GOOGLE_API_SLEEP_INTERVAL_SECONDS)

    youbot_user = get_youbot_user_by_id(youbot_user_id)
    creds = get_google_credentials(youbot_user)
    response = get_contact_info(email, creds)
    assert type(response) == dict
    return response.get("name")


def fetch_and_persist_calendar_events(youbot_user: YoubotUser) -> None:
    events = fetch_calendar_events(get_google_credentials(youbot_user))
    for event in events:
        logging.info("persisting event: %s", event)
        upsert_event_to_db(youbot_user, event)


if __name__ == "__main__":
    youbot_user = get_youbot_user_by_id(1)
    facts = get_calendar_facts(youbot_user)
