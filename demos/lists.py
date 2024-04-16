from youbot.clients.memgpt_client import MemGPTClient
from youbot.memgpt_extensions.functions.user_lists import create_list


if __name__ == "__main__":
    agent = MemGPTClient.get_or_create_agent("testbot")
    create_list(agent, "test_list")
