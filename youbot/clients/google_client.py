from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional
from google.oauth2.credentials import Credentials
from google.auth import external_account_authorized_user
from googleapiclient.discovery import build
import gspread
from gspread import Client
from gspread.spreadsheet import Spreadsheet
from gspread.worksheet import Worksheet

import pytz
import requests

from youbot.data_models import CalendarEvent
from youbot.clients.oauth_client import get_google_credentials

from toolz import curry


def get_primary_user_info(credentials: Credentials | external_account_authorized_user.Credentials):
    userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {credentials.token}"}
    response = requests.get(userinfo_endpoint, headers=headers)
    if response.ok:
        return response.json()
    else:
        return None


@curry
def get_contact_info(email, service):
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
class YoubotSpreadsheet:
    spreadsheet_name: str
    client: Client
    spreadsheet: Spreadsheet
    worksheets: Dict[str, Worksheet]

    @classmethod
    def get_or_create(cls, youbot_user_id: int, spreadsheet_name: str, sheet_names: List[str]) -> Optional["YoubotSpreadsheet"]:
        creds = get_google_credentials(youbot_user_id)
        if creds.is_nothing():
            return
        client = gspread.authorize(creds.value)  # type: ignore
        try:
            spreadsheet = client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(spreadsheet_name)

        existing_sheets = [sheet.title for sheet in spreadsheet.worksheets()]
        worksheet_dict = {}
        for name in sheet_names:
            if name not in existing_sheets:
                worksheet_dict[name] = spreadsheet.add_worksheet(title=name, rows=100, cols=20)
            else:
                worksheet_dict[name] = spreadsheet.worksheet(name)
        return cls(spreadsheet_name=spreadsheet_name, client=client, spreadsheet=spreadsheet, worksheets=worksheet_dict)


@curry
def write_data_to_spreadsheet(youbot_spreadsheet: YoubotSpreadsheet, worksheet_name: str, data: List[List]):
    youbot_spreadsheet.worksheets[worksheet_name].update(range_name="A1", values=data)  # type: ignore


def str_to_tz_aware(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt


@curry
def fetch_calendar_events(days, credentials: Credentials) -> Generator[CalendarEvent, Any, None]:
    """
    Fetch events with a 30-day look back and look forward period, handling pagination, and yield CalendarEvent objects.

    Args:
    service: The Google Calendar API service instance.
    calendar_id: The ID of the calendar to query.
    days: The number of days to look back and forward.

    Yields:
    CalendarEvent: The dataclass instance for each event.
    """
    calendar_id = "primary"

    service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

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


def _get_people_service(credentials: Credentials):
    return build("people", "v1", credentials=credentials, cache_discovery=False)
