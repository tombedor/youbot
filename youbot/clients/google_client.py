from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Generator, List, Optional
from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user
from googleapiclient.discovery import build

import pytz
import requests


def get_primary_user_info(credentials: Credentials | external_account_authorized_user.Credentials):
    userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {credentials.token}"}
    response = requests.get(userinfo_endpoint, headers=headers)
    if response.ok:
        return response.json()
    else:
        return None


def get_contact_info(email, credentials: Credentials):
    service = _get_people_service(credentials)
    contact_info = {}
    try:
        results = service.people().searchContacts(query=email, readMask="names,emailAddresses").execute()
        connections = results.get("results", [])
        if connections:
            person = connections[0]["person"]
            contact_info["name"] = person.get("names", [{}])[0].get("displayName", "N/A")
            contact_info["email"] = person.get("emailAddresses", [{}])[0].get("value", "N/A")
    except Exception as e:
        print(f"An error occurred: {e}")
    return contact_info


@dataclass
class CalendarEvent:
    event_id: str
    summary: str
    description: Optional[str]
    start: datetime
    end: datetime
    location: Optional[str]
    attendee_emails: List[str]
    recurrence: List[str]
    reminders: bool
    visibility: str

    def __post_init__(self):
        self.start = convert_to_utc(self.start)
        self.end = convert_to_utc(self.end)


def convert_to_utc(dt: datetime) -> datetime:
    """Convert a datetime object to UTC if it contains time; leave date-only as naive."""
    if dt.tzinfo is None:
        return pytz.utc.localize(dt)
    else:
        return dt.astimezone(pytz.UTC)


def str_to_tz_aware(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt


def fetch_calendar_events(credentials: Credentials, calendar_id="primary", days=30) -> Generator[CalendarEvent, Any, None]:
    """
    Fetch events with a 30-day look back and look forward period, handling pagination, and yield CalendarEvent objects.

    Args:
    service: The Google Calendar API service instance.
    calendar_id: The ID of the calendar to query.
    days: The number of days to look back and forward.

    Yields:
    CalendarEvent: The dataclass instance for each event.
    """
    service = _get_calendar_service(credentials)

    now = datetime.utcnow()
    time_min = (now - timedelta(days=days)).isoformat() + "Z"
    time_max = (now + timedelta(days=days)).isoformat() + "Z"

    page_token = None

    while True:
        events_result = (
            service.events()
            .list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy="startTime", pageToken=page_token)
            .execute()
        )

        events = events_result.get("items", [])
        for event in events:
            summary = event.get("summary", "")
            description = event.get("description", "")
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
            end = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", ""))
            location = event.get("location", "")
            attendees = event.get("attendees", [])
            attendee_emails = [attendee["email"] for attendee in attendees]
            recurrence = event.get("recurrence", [])
            reminders = event.get("reminders", {}).get("useDefault", False)
            visibility = event.get("visibility", "")

            yield CalendarEvent(
                event_id=event["id"],
                summary=summary,
                description=description,
                start=str_to_tz_aware(start),
                end=str_to_tz_aware(end),
                location=location,
                attendee_emails=attendee_emails,
                recurrence=recurrence,
                reminders=reminders,
                visibility=visibility,
            )

        page_token = events_result.get("nextPageToken")
        if not page_token:
            break


def _get_calendar_service(credentials: Credentials):
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def _get_people_service(credentials: Credentials):
    return build("people", "v1", credentials=credentials, cache_discovery=False)
