
import os

from dotenv import load_dotenv
from youbot.agent_manager import AgentManager
from youbot.memgpt_extensions.functions.google_calendar import create_calendar_event, link_google_email
from memgpt import MemGPT

# TODO: Need to figure out oauth for multiple users better

load_dotenv()
DEMO_EMAIL = os.getenv('DEMO_USER_EMAIL')

if __name__ == '__main__':
    agent = AgentManager.get_or_create_agent('testbot')
    agent.add_function(link_google_email.__name__)
    agent.add_function(create_calendar_event.__name__)
    
    client = MemGPT()
    response = client.user_message(message=f'please link the google email {DEMO_EMAIL} to my account', agent_id=agent.agent_state.id)
    
    client.user_message(message='please create a calendar event called "test event" for tomorrow', agent_id=agent.agent_state.id, user_id=client.user_id)
    
    
    
    
    


