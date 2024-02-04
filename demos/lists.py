from youbot.agent_manager import AgentManager
from youbot.memgpt_extensions.functions.user_lists import create_list


if __name__ == '__main__':
    agent = AgentManager.get_or_create_agent('testbot')
    create_list(agent, 'test_list')