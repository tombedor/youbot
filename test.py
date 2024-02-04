import os
from gcsa.google_calendar import GoogleCalendar
from sqlalchemy import UUID, Column, MetaData, String, Table, create_engine
from memgpt import MemGPT
from memgpt.agent import Agent
from gcsa.event import Event
from datetime import datetime, date
from demos.demo_manager import DemoManager
import google.auth


from youbot.agent_manager import AgentManager

    
postgres_url = os.getenv('POSTGRES_URL')
engine = create_engine(postgres_url)
metadata = MetaData()

google_emails = Table('google_emails', metadata,
                        Column('email', String, primary_key=True),
                        Column('memgpt_user_id', UUID)
                        )

metadata.create_all(engine)



def create_calendar_event(self, event_title: str, start_year: int, start_month: int, start_day: int, start_hour: int, start_min: int, end_year: int, end_month: int, end_day: int, end_hour: int, end_min: int) -> str:
    with engine.connect() as connection:
        user_id = self.agent_state.user_id
        row = connection.execute(google_emails.select().where(google_emails.c.memgpt_user_id == user_id)).fetchone()
        if row is None:
            raise ValueError('No google email linked to the user. Get email from user and call link_google_email')
        else:
            email = row[0]
    calendar = GoogleCalendar(email)
    
    # either all hour/min values are null, or none are
    hour_min_none = [val is None for val in [start_hour, start_min, end_hour, end_min]]
    if not all(hour_min_none) and any(hour_min_none):
        raise 'Either all or none of the start_hour, start_min, end_hour, end_min values must be null'
    
    if all(hour_min_none):
        start_val = date(start_year, start_month, start_day)
        end_val = date(end_year, end_month, end_day)
    else:
        start_val = datetime(start_year, start_month, start_day, start_hour, start_min)
        end_val = datetime(end_year, end_month, end_day, end_hour, end_min)
    event = Event(event_title, start=start_val, end=end_val)    
    calendar.add_event(event)
    return f'Created event {event_title}'
    
def link_google_email(self, email: str) -> str:
    user_id = self.agent_state.user_id
    
    with engine.connect() as connection:
        connection.execute(google_emails.insert().values(email=email, memgpt_user_id=user_id))
        connection.commit()
        
    return f'Linked {email} to the user. Notify the user that they will still need to go through the OAuth constent screen.'
        
if __name__ == '__main__':
    DemoManager.run()
    google.auth.default()
    
    client = MemGPT()
    
    agent = AgentManager.get_or_create_agent('testbot')
    link_google_email(agent, 'tombedor@gmail.com')
    create_calendar_event(agent, 'test event', 2022, 12, 1, 12, 0, 2022, 12, 1, 13, 0)
    
    