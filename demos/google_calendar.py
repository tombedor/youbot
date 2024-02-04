
from youbot.agent_manager import AgentManager
from youbot.memgpt_extensions.functions.google_calendar import get_creds

# TODO: Need to figure out oauth for multiple users better

if __name__ == '__main__':
    agent = AgentManager.get_or_create_agent('testbot')
    get_creds(agent)
    


