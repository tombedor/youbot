# from gcsa.google_calendar import GoogleCalendar
# from gcsa.event import Event, Attendee
# from datetime import datetime, date

# from youbot import GOOGLE_CREDS_PATH, GOOGLE_EMAIL
# from youbot.service.google_service import fetch_google_email


# def create_calendar_event(
#     self,
#     event_title: str,
#     start_year: int,
#     start_month: int,
#     start_day: int,
#     start_hour: int,
#     start_min: int,
#     end_year: int,
#     end_month: int,
#     end_day: int,
#     end_hour: int,
#     end_min: int,
# ) -> str:
#     """Creates a calendar event in the user's linked google calendar

#     Args:
#         event_title (str): The title of the event.
#         start_year (int): The year of the start of the event.
#         start_month (int): The month of the start of the event.
#         start_day (int): The day of the start of the event.
#         start_hour (int): The hour of the start of the event.
#         start_min (int): The minute of the start of the event.
#         end_year (int): The year of the end of the event.
#         end_month (int): The month of the end of the event.
#         end_day (int): The day of the end of the event.
#         end_hour (int): The hour of the end of the event.
#         end_min (int): The minute of the end of the event.

#     Raises:
#         ValueError: If no google email is linked to the user. Get email from user and call link_google_email

#     Returns:
#         str: The result of the event creation attempt.
#     """
#     assert GOOGLE_CREDS_PATH is not None, "No google creds path set"
#     assert GOOGLE_EMAIL is not None, "No google email set"

#     calendar = GoogleCalendar(credentials_path=GOOGLE_CREDS_PATH, default_calendar=GOOGLE_EMAIL)  # type: ignore

#     # either all hour/min values are null, or none are
#     hour_min_none = [val is None for val in [start_hour, start_min, end_hour, end_min]]
#     if not all(hour_min_none) and any(hour_min_none):
#         raise ValueError("Either all or none of the start_hour, start_min, end_hour, end_min values must be null")

#     if all(hour_min_none):
#         start_val = date(start_year, start_month, start_day)
#         end_val = date(end_year, end_month, end_day)
#     else:
#         start_val = datetime(start_year, start_month, start_day, start_hour, start_min)
#         end_val = datetime(end_year, end_month, end_day, end_hour, end_min)

#     email = fetch_google_email(self.agent_state.user_id)
#     event = Event(event_title, start=start_val, end=end_val, attendees=[Attendee(email=email)])
#     calendar.add_event(event)
#     return f"Created event {event_title}"
