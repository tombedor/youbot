from copy import deepcopy
import uuid
from memgpt.agent import save_agent
from youbot.store import YoubotUser


def purge_send_message_calls(youbot_user: YoubotUser):

    agent_messages = []
    new_messages = []
    for m in youbot_user.agent._messages:
        if not m.tool_calls:
            agent_messages.append(m)
        else:
            call = m.tool_calls[0]
            if call.function["name"] == "send_message":
                refactored_message = deepcopy(m)
                refactored_message.text = json.loads(call.function["arguments"])["message"]  # type: ignore
                refactored_message.id = uuid.uuid4()
                refactored_message.tool_calls = None
                new_messages.append(refactored_message)
                agent_messages.append(refactored_message)

    youbot_user.agent.persistence_manager.persist_messages(new_messages)
    youbot_user.agent._messages = agent_messages
    save_agent(youbot_user.agent)
