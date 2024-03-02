from youbot.memgpt_client import MemGPTClient
from youbot.memgpt_extensions.functions.graph import add_node


agent = MemGPTClient.get_or_create_agent("testbot")

agent.add_function(add_node.__name__)

response = MemGPTClient.user_message("testbot", "I have added a function to add nodes to a graph. Please create a node for Tom Bedor.")
print(response)
