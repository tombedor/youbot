from youbot.agent_manager import AgentManager
from youbot.memgpt_extensions.functions.graph import add_node


agent = AgentManager.get_or_create_agent("testbot")

agent.add_function(add_node.__name__)

response = AgentManager.user_message("testbot", "I have added a function to add nodes to a graph. Please create a node for Tom Bedor.")
print(response)
